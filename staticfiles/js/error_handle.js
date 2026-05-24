
export class ResilientFetcher {
  constructor(options = {}) {
    this.options = {
      maxRetries: 3,
      baseDelay: 500,
      maxDelay: 30000,
      persistQueue: true,
      storageKey: 'pendingRequests',
      debug: false,
      ...options
    };
    this.isOnline = typeof navigator !== 'undefined' ? navigator.onLine : true;
    this.pendingRequests = new Map();
    this.activeRequests = new Map();
    this.stats = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      retriedRequests: 0,
      queuedRequests: 0,
      recoveredRequests: 0
    };
    this.fetch = this.fetch.bind(this);
    this.handleOnline = this.handleOnline.bind(this);
    this.handleOffline = this.handleOffline.bind(this);
    this.processQueue = this.processQueue.bind(this);
    this.initNetworkListeners();
    this.loadPendingRequests();
    
    this._log('info', 'ResilientFetcher initialized', {
      maxRetries: this.options.maxRetries,
      isOnline: this.isOnline,
      pendingCount: this.pendingRequests.size
    });
  }
  _log(level, ...args) {
    const timestamp = new Date().toISOString();
    const prefix = '[ResilientFetcher]';
    
    if (level === 'debug' && !this.options.debug) {
      return;
    }
    
    const logMethod = level === 'error' ? console.error : 
                      level === 'warn' ? console.warn : 
                      console.log;
    
    logMethod(`${prefix} [${timestamp}]`, ...args);
  }
  initNetworkListeners() {
    if (typeof window === 'undefined') return;

    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);
    this.startConnectionMonitoring();
  }
  startConnectionMonitoring() {
    this.monitorInterval = setInterval(() => {
      const currentStatus = navigator.onLine;
      if (currentStatus !== this.isOnline) {
        this._log('debug', `Connection status changed: ${this.isOnline} -> ${currentStatus}`);
        this.isOnline = currentStatus;
        
        if (currentStatus) {
          this.handleOnline();
        } else {
          this.handleOffline();
        }
      }
    }, 30000);
  }
  async handleOnline() {
    this._log('info', 'Network connection restored');
    this.isOnline = true;
    
    if (this.options.onStatusChange) {
      try {
        this.options.onStatusChange('online', {
          pendingRequests: this.pendingRequests.size,
          stats: { ...this.stats }
        });
      } catch (error) {
        this._log('error', 'Error in onStatusChange callback', error);
      }
    }

    if (this.pendingRequests.size > 0) {
      this._log('info', `Processing ${this.pendingRequests.size} pending requests`);
      await this.processQueue();
    }
  }
  handleOffline() {
    this._log('warn', 'Network connection lost');
    this.isOnline = false;
    
    if (this.options.onStatusChange) {
      try {
        this.options.onStatusChange('offline', {
          pendingRequests: this.pendingRequests.size,
          stats: { ...this.stats }
        });
      } catch (error) {
        this._log('error', 'Error in onStatusChange callback', error);
      }
    }
  }
  _generateRequestId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}-${this.stats.totalRequests}`;
  }


  _saveToQueue(requestId, url, options, metadata = {}) {
    const requestData = {
      id: requestId,
      url,
      options: {
        ...options,
        body: options.body,
        method: options.method,
        headers: options.headers
      },
      metadata: {
        ...metadata,
        timestamp: new Date().toISOString(),
        attempts: metadata.attempts || 0
      }
    };

    this.pendingRequests.set(requestId, requestData);
    this.stats.queuedRequests++;

    if (this.options.persistQueue) {
      this._persistQueue();
    }

    if (this.options.onQueueUpdate) {
      try {
        this.options.onQueueUpdate('added', {
          requestId,
          queueSize: this.pendingRequests.size,
          request: requestData
        });
      } catch (error) {
        this._log('error', 'Error in onQueueUpdate callback', error);
      }
    }

    this._log('debug', `Request ${requestId} saved to queue`, {
      url,
      method: options.method,
      queueSize: this.pendingRequests.size
    });
  }
  _removeFromQueue(requestId) {
    const removed = this.pendingRequests.delete(requestId);
    
    if (removed) {
      if (this.options.persistQueue) {
        this._persistQueue();
      }

      if (this.options.onQueueUpdate) {
        try {
          this.options.onQueueUpdate('removed', {
            requestId,
            queueSize: this.pendingRequests.size
          });
        } catch (error) {
          this._log('error', 'Error in onQueueUpdate callback', error);
        }
      }

      this._log('debug', `Request ${requestId} removed from queue`);
    }
  }
  _persistQueue() {
    if (typeof localStorage === 'undefined') return;

    try {
      const queueArray = Array.from(this.pendingRequests.values());
      localStorage.setItem(this.options.storageKey, JSON.stringify(queueArray));
      this._log('debug', `Queue persisted to localStorage (${queueArray.length} items)`);
    } catch (error) {
      this._log('error', 'Failed to persist queue to localStorage', error);

      if (error.name === 'QuotaExceededError') {
        this._cleanupOldRequests();
      }
    }
  }

  loadPendingRequests() {
    if (typeof localStorage === 'undefined' || !this.options.persistQueue) return;

    try {
      const stored = localStorage.getItem(this.options.storageKey);
      if (!stored) return;

      const requests = JSON.parse(stored);
      const now = Date.now();
      const maxAge = 24 * 60 * 60 * 1000;
      
      let loadedCount = 0;
      let expiredCount = 0;

      requests.forEach(request => {
        const requestTime = new Date(request.metadata.timestamp).getTime();
        if (now - requestTime > maxAge) {
          expiredCount++;
          return;
        }

        this.pendingRequests.set(request.id, request);
        loadedCount++;
      });

      this.stats.queuedRequests = this.pendingRequests.size;
      
      this._log('info', `Loaded ${loadedCount} requests from localStorage (${expiredCount} expired)`);

      if (this.options.onQueueUpdate) {
        try {
          this.options.onQueueUpdate('loaded', {
            queueSize: this.pendingRequests.size,
            loadedCount,
            expiredCount
          });
        } catch (error) {
          this._log('error', 'Error in onQueueUpdate callback', error);
        }
      }
      if (this.isOnline && this.pendingRequests.size > 0) {
        setTimeout(() => this.processQueue(), 1000);
      }
    } catch (error) {
      this._log('error', 'Failed to load pending requests from localStorage', error);
    }
  }
  _cleanupOldRequests() {
    const requests = Array.from(this.pendingRequests.entries());

    requests.sort((a, b) => {
      const timeA = new Date(a[1].metadata.timestamp).getTime();
      const timeB = new Date(b[1].metadata.timestamp).getTime();
      return timeA - timeB;
    });

    const toRemove = Math.ceil(requests.length / 2);
    for (let i = 0; i < toRemove; i++) {
      this._removeFromQueue(requests[i][0]);
    }

    this._log('warn', `Cleaned up ${toRemove} old requests due to storage quota`);
  }

  async processQueue() {
    if (!this.isOnline) {
      this._log('debug', 'Cannot process queue: offline');
      return;
    }

    if (this.pendingRequests.size === 0) {
      this._log('debug', 'Queue is empty');
      return;
    }

    if (this.isProcessingQueue) {
      this._log('debug', 'Queue processing already in progress');
      return;
    }

    this.isProcessingQueue = true;
    this._log('info', `Starting queue processing (${this.pendingRequests.size} items)`);

    const requests = Array.from(this.pendingRequests.values());
    let successCount = 0;
    let failCount = 0;

    for (const request of requests) {
      if (!this.isOnline) {
        this._log('info', 'Queue processing interrupted: went offline');
        break;
      }

      try {
        this._log('debug', `Processing queued request ${request.id}`, {
          url: request.url,
          method: request.options.method
        });
        const response = await fetch(request.url, {
          ...request.options,
          headers: {
            ...request.options.headers,
            'X-Retry-Count': request.metadata.attempts.toString()
          }
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        this._removeFromQueue(request.id);
        successCount++;
        this.stats.recoveredRequests++;

        this._log('debug', `Queued request ${request.id} succeeded`);

      } catch (error) {
        failCount++;
        this._log('error', `Failed to process queued request ${request.id}`, error);

        request.metadata.attempts++;
        
        if (request.metadata.attempts >= this.options.maxRetries) {
          this._log('warn', `Request ${request.id} exceeded max retries, removing from queue`);
          this._removeFromQueue(request.id);

          if (this.options.onError) {
            try {
              this.options.onError({
                type: 'queue_processing_failed',
                requestId: request.id,
                url: request.url,
                error: error.message,
                attempts: request.metadata.attempts
              });
            } catch (callbackError) {
              this._log('error', 'Error in onError callback', callbackError);
            }
          }
        } else {
          this.pendingRequests.set(request.id, request);
          if (this.options.persistQueue) {
            this._persistQueue();
          }
        }
      }
      await this._delay(100);
    }

    this.isProcessingQueue = false;
    
    this._log('info', `Queue processing completed`, {
      successCount,
      failCount,
      remaining: this.pendingRequests.size
    });

    if (this.options.onQueueUpdate) {
      try {
        this.options.onQueueUpdate('processed', {
          successCount,
          failCount,
          queueSize: this.pendingRequests.size
        });
      } catch (error) {
        this._log('error', 'Error in onQueueUpdate callback', error);
      }
    }
  }

  async fetch(url, options = {}, retryOptions = {}) {
    const requestId = this._generateRequestId();
    const maxRetries = retryOptions.maxRetries || this.options.maxRetries;
    const baseDelay = retryOptions.baseDelay || this.options.baseDelay;
    
    let attempt = 0;
    let lastError = null;

    this.stats.totalRequests++;
    this.activeRequests.set(requestId, { url, options, startTime: Date.now() });

    this._log('debug', `Starting request ${requestId}`, {
      url,
      method: options.method || 'GET',
      maxRetries
    });

    while (attempt <= maxRetries) {
      if (!this.isOnline) {
        this._log('warn', `Offline, queuing request ${requestId}`);
        this._saveToQueue(requestId, url, options, {
          attempts: attempt,
          lastError: lastError?.message
        });
        
        this.activeRequests.delete(requestId);
        
        throw new NetworkError('Network is offline. Request queued for later.', {
          requestId,
          queued: true
        });
      }

      try {
        this._log('debug', `Attempt ${attempt + 1}/${maxRetries + 1} for ${requestId}`);
        
        const response = await fetch(url, {
          ...options,
          headers: {
            ...options.headers,
            'X-Request-ID': requestId,
            'X-Retry-Count': attempt.toString()
          }
        });

        if (!response.ok) {
          const errorBody = await response.text();
          throw new HTTPError(
            `HTTP ${response.status}: ${response.statusText}`,
            response.status,
            errorBody
          );
        }

        this.stats.successfulRequests++;
        this.activeRequests.delete(requestId);
        
        this._log('debug', `Request ${requestId} succeeded after ${attempt + 1} attempts`);
        
        return response;

      } catch (error) {
        lastError = error;
        attempt++;

        this._log('warn', `Request ${requestId} attempt ${attempt} failed`, {
          error: error.message,
          isNetworkError: error instanceof NetworkError || error.name === 'TypeError'
        });

        if (this.options.onError) {
          try {
            this.options.onError({
              type: 'request_failed',
              requestId,
              url,
              attempt,
              maxRetries,
              error: error.message
            });
          } catch (callbackError) {
            this._log('error', 'Error in onError callback', callbackError);
          }
        }

        if (attempt > maxRetries) {
          this.stats.failedRequests++;
          
          this._log('error', `Request ${requestId} failed after ${maxRetries + 1} attempts`);
          if (this._shouldQueueOnFailure(error)) {
            this._saveToQueue(requestId, url, options, {
              attempts: attempt,
              lastError: error.message
            });
          }
          
          this.activeRequests.delete(requestId);
          if (this.options.onError) {
            try {
              this.options.onError({
                type: 'request_failed_final',
                requestId,
                url,
                attempts: attempt,
                error: error.message
              });
            } catch (callbackError) {
              this._log('error', 'Error in onError callback', callbackError);
            }
          }
          
          throw new MaxRetriesExceededError(
            `Failed after ${attempt} attempts: ${error.message}`,
            {
              requestId,
              attempts: attempt,
              lastError: error
            }
          );
        }
        if (!this._shouldRetry(error)) {
          this._log('info', `Not retrying request ${requestId} due to error type`, {
            error: error.message
          });
          
          this.activeRequests.delete(requestId);
          throw error;
        }

        this.stats.retriedRequests++;
        if (this.options.onRetry) {
          try {
            this.options.onRetry({
              requestId,
              url,
              attempt,
              maxRetries,
              delay: this._calculateDelay(attempt, baseDelay),
              error: error.message
            });
          } catch (callbackError) {
            this._log('error', 'Error in onRetry callback', callbackError);
          }
        }

        const delay = this._calculateDelay(attempt, baseDelay);
        this._log('debug', `Waiting ${delay}ms before retry ${attempt}`);
        await this._delay(delay);
      }
    }
  }

  _calculateDelay(attempt, baseDelay) {
    const exponentialDelay = baseDelay * Math.pow(2, attempt - 1);
    const jitter = Math.random() * 300;
    return Math.min(exponentialDelay + jitter, this.options.maxDelay);
  }

  _shouldRetry(error) {
    if (error instanceof NetworkError) return true;
    if (error.name === 'TypeError' && error.message.includes('network')) return true;
    if (error.name === 'AbortError') return true;

    if (error instanceof HTTPError) {
      const retryableStatuses = [408, 429, 500, 502, 503, 504];
      return retryableStatuses.includes(error.status);
    }
    
    return false;
  }
  _shouldQueueOnFailure(error) {
    if (!this.isOnline) return true;
    if (error instanceof NetworkError) return true;
    if (error.name === 'TypeError' && error.message.includes('network')) return true;
    
    if (error instanceof HTTPError) {
      const queueableStatuses = [408, 429, 500, 502, 503, 504];
      return queueableStatuses.includes(error.status);
    }
    
    return false;
  }
  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  getStats() {
    return {
      ...this.stats,
      isOnline: this.isOnline,
      pendingRequests: this.pendingRequests.size,
      activeRequests: this.activeRequests.size,
      queueSize: this.pendingRequests.size,
      timestamp: new Date().toISOString()
    };
  }
  getPendingRequests() {
    return Array.from(this.pendingRequests.values()).map(req => ({
      id: req.id,
      url: req.url,
      method: req.options.method,
      timestamp: req.metadata.timestamp,
      attempts: req.metadata.attempts
    }));
  }
  clearQueue(clearStorage = true) {
    const count = this.pendingRequests.size;
    this.pendingRequests.clear();
    
    if (clearStorage && typeof localStorage !== 'undefined') {
      localStorage.removeItem(this.options.storageKey);
    }
    
    this._log('info', `Cleared ${count} pending requests from queue`);
    
    if (this.options.onQueueUpdate) {
      try {
        this.options.onQueueUpdate('cleared', { count });
      } catch (error) {
        this._log('error', 'Error in onQueueUpdate callback', error);
      }
    }
  }
  cancelRequest(requestId) {
    const request = this.activeRequests.get(requestId);
    if (request?.controller) {
      request.controller.abort();
    }
    this.activeRequests.delete(requestId);
    this._log('debug', `Cancelled request ${requestId}`);
  }
  async forceProcessQueue() {
    if (this.pendingRequests.size === 0) {
      this._log('debug', 'No pending requests to process');
      return;
    }

    this._log('info', 'Force processing queue');
    await this.processQueue();
  }
  destroy() {
    if (typeof window !== 'undefined') {
      window.removeEventListener('online', this.handleOnline);
      window.removeEventListener('offline', this.handleOffline);
    }
    
    if (this.monitorInterval) {
      clearInterval(this.monitorInterval);
    }

    this.activeRequests.forEach((request, id) => {
      this.cancelRequest(id);
    });
    
    this._log('info', 'ResilientFetcher destroyed');
  }
}

export class NetworkError extends Error {
  constructor(message, metadata = {}) {
    super(message);
    this.name = 'NetworkError';
    this.metadata = metadata;
  }
}

export class HTTPError extends Error {
  constructor(message, status, body = null) {
    super(message);
    this.name = 'HTTPError';
    this.status = status;
    this.body = body;
  }
}

export class MaxRetriesExceededError extends Error {
  constructor(message, metadata = {}) {
    super(message);
    this.name = 'MaxRetriesExceededError';
    this.metadata = metadata;
  }
}
export const resilientFetcher = new ResilientFetcher();
export default ResilientFetcher;