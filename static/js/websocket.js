export class QuizWebSocketClient {
  constructor(sessionCode, options = {}) {
    if (!sessionCode || typeof sessionCode !== 'string') {
      throw new Error('Session code is needed and it must be a string');
    }

    this.sessionCode = sessionCode;
    this.options = {
      maxReconnectAttempts: 5,
      reconnectDelay: 1000,
      debug: false,
      ...options
    };

    this.ws = null;
    this.isManualClose = false;
    this.reconnectAttempts = 0;
    this.reconnectTimer = null;
    this.status = 'disconnected';
    this.lastMessageTime = null;
    this.stats = {
      messagesReceived: 0,
      messagesSent: 0,
      reconnectCount: 0,
      connectedAt: null
    };
    this.connect = this.connect.bind(this);
    this.disconnect = this.disconnect.bind(this);
    this.reconnect = this.reconnect.bind(this);
    this.send = this.send.bind(this);
    this.handleOpen = this.handleOpen.bind(this);
    this.handleMessage = this.handleMessage.bind(this);
    this.handleError = this.handleError.bind(this);
    this.handleClose = this.handleClose.bind(this);
    this.connect();
    this.setupPageUnloadHandler();
  }
  _log(level, ...args) {
    const timestamp = new Date().toISOString();
    const prefix = `[WebSocket ${this.sessionCode}]`;
    
    if (level === 'debug' && !this.options.debug) {
      return;
    }
    
    const logMethod = level === 'error' ? console.error : 
                      level === 'warn' ? console.warn : 
                      console.log;
    
    logMethod(`${prefix} [${timestamp}]`, ...args);
  }
  _setStatus(newStatus, metadata = {}) {
    const oldStatus = this.status;
    this.status = newStatus;
    
    this._log('debug', `Status changed: ${oldStatus} → ${newStatus}`, metadata);
    
    if (this.options.onStatusChange) {
      try {
        this.options.onStatusChange(newStatus, {
          previousStatus: oldStatus,
          ...metadata,
          stats: { ...this.stats }
        });
      } catch (error) {
        this._log('error', 'Error in onStatusChange callback:', error);
      }
    }
  }
  _handleError(error, context = {}) {
    const errorInfo = {
      message: error.message || 'Unknown error',
      context,
      timestamp: new Date().toISOString(),
      sessionCode: this.sessionCode,
      status: this.status
    };
    
    this._log('error', 'Error occurred:', errorInfo);
    
    if (this.options.onError) {
      try {
        this.options.onError(errorInfo);
      } catch (callbackError) {
        this._log('error', 'Error in onError callback:', callbackError);
      }
    }
  }
  _getWebSocketUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const path = `/ws/quiz/${this.sessionCode}/`;

    const customHost = this.options.host || host;
    
    return `${protocol}//${customHost}${path}`;
  }

  connect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      const readyState = this.ws.readyState;
      if (readyState === WebSocket.OPEN) {
        this._log('warn', 'Connection already open');
        return;
      } else if (readyState === WebSocket.CONNECTING) {
        this._log('warn', 'Connection already in progress');
        return;
      }
    }

    this._setStatus('connecting');
    
    try {
      const url = this._getWebSocketUrl();
      this._log('info', `Connecting to ${url}`);
      
      this.ws = new WebSocket(url);

      this.ws.onopen = this.handleOpen;
      this.ws.onmessage = this.handleMessage;
      this.ws.onerror = this.handleError;
      this.ws.onclose = this.handleClose;
      
    } catch (error) {
      this._handleError(error, { action: 'connect' });
      this._setStatus('error', { error: error.message });
      this.reconnect();
    }
  }

  handleOpen(event) {
    this._log('info', 'Connected successfully');
    this.reconnectAttempts = 0;
    this.stats.connectedAt = new Date().toISOString();
    
    this._setStatus('connected', {
      reconnectAttempts: this.reconnectAttempts,
      connectedAt: this.stats.connectedAt
    });
  }

  handleMessage(event) {
    this.lastMessageTime = new Date().toISOString();
    this.stats.messagesReceived++;
    
    this._log('debug', `Message #${this.stats.messagesReceived} received:`, event.data);
    
    try {
      const data = JSON.parse(event.data);
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid message format: expected JSON object');
      }

      const eventType = data.event?.type || data.type || 'unknown';
      this._log('info', `Received event: ${eventType}`);

      if (this.options.onMessage) {
        try {
          this.options.onMessage(data, {
            timestamp: this.lastMessageTime,
            messageNumber: this.stats.messagesReceived
          });
        } catch (callbackError) {
          this._handleError(callbackError, { 
            action: 'onMessage callback',
            messageData: data 
          });
        }
      }
      
    } catch (error) {
      this._handleError(error, { 
        action: 'parse message',
        rawData: event.data 
      });
    }
  }
  handleError(event) {
    const errorInfo = {
      type: 'WebSocket error',
      readyState: this.ws?.readyState,
      url: this.ws?.url
    };
    
    this._handleError(new Error('WebSocket connection error'), errorInfo);
    if (this.status !== 'error') {
      this._setStatus('error', errorInfo);
    }
  }
  handleClose(event) {
    const closeInfo = {
      code: event.code,
      reason: event.reason || 'No reason provided',
      wasClean: event.wasClean,
      manualClose: this.isManualClose
    };
    
    this._log('info', `Connection closed:`, closeInfo);
    this.ws = null;
    
    if (this.isManualClose) {
      this._setStatus('disconnected', { manual: true });
      this._log('info', 'Manual disconnect, none reconnection attempts');
    } else {
      this._setStatus('disconnected', { manual: false });

      if (this.reconnectAttempts < this.options.maxReconnectAttempts) {
        this.reconnect();
      } else {
        this._setStatus('error', { 
          reason: 'Maximum reconnection attempts reached',
          attempts: this.reconnectAttempts 
        });
        this._log('error', 'Max reconnection attempts reached');
      }
    }
  }

  reconnect() {
    if (this.isManualClose) {
      this._log('debug', 'Manual close in progress, skipping reconnect');
      return;
    }
    
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      this._log('error', `Maximum reconnection attempts (${this.options.maxReconnectAttempts}) reached`);
      this._setStatus('error', { 
        reason: 'Maximum reconnection attempts reached',
        attempts: this.reconnectAttempts 
      });
      return;
    }
    
    this.reconnectAttempts++;
    this.stats.reconnectCount++;
    const baseDelay = this.options.reconnectDelay;
    const exponentialDelay = baseDelay * Math.pow(2, this.reconnectAttempts - 1);
    const jitter = Math.random() * 300;
    const delay = Math.min(exponentialDelay + jitter, 30000);
    this._log('info', `Scheduling reconnect attempt ${this.reconnectAttempts}/${this.options.maxReconnectAttempts} in ${Math.round(delay)}ms`);
    this._setStatus('reconnecting', {
      attempt: this.reconnectAttempts,
      maxAttempts: this.options.maxReconnectAttempts,
      delay: Math.round(delay)
    });
    this.reconnectTimer = setTimeout(() => {
      if (!this.isManualClose) {
        this._log('debug', `Executing reconnect attempt ${this.reconnectAttempts}`);
        this.connect();
      }
      this.reconnectTimer = null;
    }, delay);
  }
  send(data) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this._log('warn', 'Can not send message: connection not open', {
        readyState: this.ws?.readyState,
        status: this.status
      });
      return false;
    }
    try {
      const message = JSON.stringify(data);
      this.ws.send(message);
      this.stats.messagesSent++;
      this._log('debug', `Message #${this.stats.messagesSent} sent:`, data);
      return true;
    } catch (error) {
      this._handleError(error, { 
        action: 'send message',
        data: data 
      });
      return false;
    }
  }
  disconnect() {
    this._log('info', 'Manual disconnect initiated');
    this.isManualClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      try {
        if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
          this.ws.close(1000, 'User initiated disconnect');
        }
      } catch (error) {
        this._log('error', 'Error during disconnect:', error);
      }
      this.ws = null;
    }
    this._setStatus('disconnected', { manual: true });
  }
  setupPageUnloadHandler() {
    const handleUnload = () => {
      this._log('debug', 'Page unload detected, cleaning up connection');
      this.isManualClose = true;
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.close(1000, 'Page unload');
      }
    };
    window.addEventListener('beforeunload', handleUnload);
    window.addEventListener('pagehide', handleUnload);
  }
  getState() {
    return {
      status: this.status,
      sessionCode: this.sessionCode,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.options.maxReconnectAttempts,
      isManualClose: this.isManualClose,
      readyState: this.ws?.readyState,
      lastMessageTime: this.lastMessageTime,
      stats: { ...this.stats },
      timestamp: new Date().toISOString()
    };
  }
  isConnected() {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
  resetReconnectAttempts() {
    this.reconnectAttempts = 0;
    this._log('debug', 'Reconnect attempts counter reset');
  }
}
export default QuizWebSocketClient;