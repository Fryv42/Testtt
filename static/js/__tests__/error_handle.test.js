/**
 * Тесты для модуля обработки сетевых ошибок
 */

import { ResilientFetcher, NetworkError, HTTPError, MaxRetriesExceededError } from './error-handler.js';
global.fetch = jest.fn();
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => { store[key] = value; }),
    removeItem: jest.fn((key) => { delete store[key]; }),
    clear: jest.fn(() => { store = {}; })
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true
});

describe('ResilientFetcher', () => {
  let fetcher;
  
  beforeEach(() => {
    jest.useFakeTimers();
    fetch.mockClear();
    localStorageMock.clear();
    navigator.onLine = true;
    
    fetcher = new ResilientFetcher({
      maxRetries: 3,
      baseDelay: 500,
      debug: true,
      persistQueue: false
    });
  });
  
  afterEach(() => {
    if (fetcher) {
      fetcher.destroy();
    }
    jest.useRealTimers();
  });
  
  describe('Constructor and Initialization', () => {
    test('should create instance with default options', () => {
      const defaultFetcher = new ResilientFetcher();
      expect(defaultFetcher.options.maxRetries).toBe(3);
      expect(defaultFetcher.options.baseDelay).toBe(500);
      expect(defaultFetcher.options.persistQueue).toBe(true);
    });
    
    test('should override default options', () => {
      const customFetcher = new ResilientFetcher({
        maxRetries: 5,
        baseDelay: 1000,
        debug: true
      });
      
      expect(customFetcher.options.maxRetries).toBe(5);
      expect(customFetcher.options.baseDelay).toBe(1000);
      expect(customFetcher.options.debug).toBe(true);
    });
    test('should initialize with correct network status', () => {
      navigator.onLine = true;
      const onlineFetcher = new ResilientFetcher();
      expect(onlineFetcher.isOnline).toBe(true);
      
      navigator.onLine = false;
      const offlineFetcher = new ResilientFetcher();
      expect(offlineFetcher.isOnline).toBe(false);
    });
  });
  describe('Network Status Handling', () => {
    test('should detect online status', () => {
      const onStatusChange = jest.fn();
      fetcher = new ResilientFetcher({ onStatusChange });
      navigator.onLine = true;
      window.dispatchEvent(new Event('online'));
      expect(fetcher.isOnline).toBe(true);
      expect(onStatusChange).toHaveBeenCalledWith('online', expect.any(Object));
    });
    test('should detect offline status', () => {
      const onStatusChange = jest.fn();
      fetcher = new ResilientFetcher({ onStatusChange });
      navigator.onLine = false;
      window.dispatchEvent(new Event('offline'));
      expect(fetcher.isOnline).toBe(false);
      expect(onStatusChange).toHaveBeenCalledWith('offline', expect.any(Object));
    });
    test('should queue requests when offline', async () => {
      navigator.onLine = false;
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' })
      });
      await expect(fetcher.fetch('/api/test')).rejects.toThrow(NetworkError);
      expect(fetcher.pendingRequests.size).toBe(1);
      expect(fetcher.stats.queuedRequests).toBe(1);
    });
  });
  describe('Retry Logic', () => {
    test('should retry on network failure', async () => {
      fetch
        .mockRejectedValueOnce(new TypeError('Network error'))
        .mockRejectedValueOnce(new TypeError('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });
      const onRetry = jest.fn();
      fetcher = new ResilientFetcher({ onRetry, maxRetries: 3 });
      const response = await fetcher.fetch('/api/test');
      expect(response.ok).toBe(true);
      expect(fetch).toHaveBeenCalledTimes(3);
      expect(onRetry).toHaveBeenCalledTimes(2);
      expect(fetcher.stats.retriedRequests).toBe(2);
      expect(fetcher.stats.successfulRequests).toBe(1);
    });
    
    test('should use exponential backoff', async () => {
      fetch.mockRejectedValue(new TypeError('Network error'));
      
      const promise = fetcher.fetch('/api/test').catch(() => {});
      expect(fetch).toHaveBeenCalledTimes(1);
      await jest.advanceTimersByTimeAsync(500);
      expect(fetch).toHaveBeenCalledTimes(2);
      await jest.advanceTimersByTimeAsync(1000);
      expect(fetch).toHaveBeenCalledTimes(3);
      await jest.advanceTimersByTimeAsync(2000);
      expect(fetch).toHaveBeenCalledTimes(4);
      await promise;
    });
    
    test('should stop retrying after max attempts', async () => {
      fetch.mockRejectedValue(new TypeError('Network error'));
      
      await expect(fetcher.fetch('/api/test')).rejects.toThrow(MaxRetriesExceededError);
      expect(fetch).toHaveBeenCalledTimes(4);
      expect(fetcher.stats.failedRequests).toBe(1);
    });
    
    test('should not retry on certain HTTP errors', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        text: async () => 'Invalid data'
      });
      
      await expect(fetcher.fetch('/api/test')).rejects.toThrow(HTTPError);
      expect(fetch).toHaveBeenCalledTimes(1);
    });
    
    test('should retry on server errors (5xx)', async () => {
      fetch
        .mockResolvedValueOnce({
          ok: false,
          status: 503,
          statusText: 'Service Unavailable',
          text: async () => 'Server error'
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });
      
      const response = await fetcher.fetch('/api/test');
      
      expect(response.ok).toBe(true);
      expect(fetch).toHaveBeenCalledTimes(2);
    });
  });
  
  describe('Queue Management', () => {
    test('should save request to queue when offline', async () => {
      navigator.onLine = false;
      
      fetch.mockResolvedValue({ ok: true });
      
      await expect(fetcher.fetch('/api/test', { method: 'POST' }))
        .rejects.toThrow(NetworkError);
      
      expect(fetcher.pendingRequests.size).toBe(1);
      
      const pending = fetcher.getPendingRequests();
      expect(pending[0].url).toBe('/api/test');
      expect(pending[0].method).toBe('POST');
    });
    
    test('should process queue when coming online', async () => {
      navigator.onLine = false;
      fetch.mockResolvedValue({ ok: true });
      
      await expect(fetcher.fetch('/api/offline')).rejects.toThrow(NetworkError);
      
      expect(fetcher.pendingRequests.size).toBe(1);
      navigator.onLine = true;
      fetch.mockClear();
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'success' })
      });
      
      await fetcher.handleOnline();
      await jest.runAllTimersAsync();
      
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(fetcher.pendingRequests.size).toBe(0);
      expect(fetcher.stats.recoveredRequests).toBe(1);
    });
    
    test('should not process queue when offline', async () => {
      navigator.onLine = false;
      
      await fetcher.processQueue();
      
      expect(fetch).not.toHaveBeenCalled();
    });
    
    test('should clear queue', () => {
      fetcher.pendingRequests.set('test-1', { id: 'test-1', url: '/test1' });
      fetcher.pendingRequests.set('test-2', { id: 'test-2', url: '/test2' });
      
      fetcher.clearQueue();
      
      expect(fetcher.pendingRequests.size).toBe(0);
    });
  });
  
  describe('LocalStorage Persistence', () => {
    test('should persist queue to localStorage', () => {
      fetcher = new ResilientFetcher({ persistQueue: true });
      
      fetcher.pendingRequests.set('test-1', {
        id: 'test-1',
        url: '/api/test',
        options: { method: 'POST' },
        metadata: { timestamp: new Date().toISOString(), attempts: 0 }
      });
      
      fetcher._persistQueue();
      
      expect(localStorageMock.setItem).toHaveBeenCalled();
    });
    
    test('should load queue from localStorage', () => {
      const storedRequests = [{
        id: 'test-1',
        url: '/api/test',
        options: { method: 'POST' },
        metadata: { timestamp: new Date().toISOString(), attempts: 0 }
      }];
      
      localStorageMock.setItem('pendingRequests', JSON.stringify(storedRequests));
      
      fetcher = new ResilientFetcher({ persistQueue: true });
      
      expect(fetcher.pendingRequests.size).toBe(1);
      expect(fetcher.pendingRequests.get('test-1')).toBeTruthy();
    });
  });
  
  describe('Request Headers', () => {
    test('should add request ID and retry count headers', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });
      
      await fetcher.fetch('/api/test');
      
      expect(fetch).toHaveBeenCalledWith('/api/test', expect.objectContaining({
        headers: expect.objectContaining({
          'X-Request-ID': expect.any(String),
          'X-Retry-Count': '0'
        })
      }));
    });
    
    test('should increment retry count on subsequent attempts', async () => {
      fetch
        .mockRejectedValueOnce(new TypeError('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });
      
      await fetcher.fetch('/api/test');
      
      expect(fetch).toHaveBeenNthCalledWith(1, '/api/test', expect.objectContaining({
        headers: expect.objectContaining({ 'X-Retry-Count': '0' })
      }));
      
      expect(fetch).toHaveBeenNthCalledWith(2, '/api/test', expect.objectContaining({
        headers: expect.objectContaining({ 'X-Retry-Count': '1' })
      }));
    });
  });
  
  describe('Callbacks', () => {
    test('should call onError callback', async () => {
      const onError = jest.fn();
      fetcher = new ResilientFetcher({ onError });
      
      fetch.mockRejectedValue(new TypeError('Network error'));
      
      await expect(fetcher.fetch('/api/test')).rejects.toThrow();
      
      expect(onError).toHaveBeenCalled();
    });
    
    test('should call onRetry callback', async () => {
      const onRetry = jest.fn();
      fetcher = new ResilientFetcher({ onRetry });
      
      fetch
        .mockRejectedValueOnce(new TypeError('Network error'))
        .mockResolvedValueOnce({ ok: true });
      
      await fetcher.fetch('/api/test');
      
      expect(onRetry).toHaveBeenCalledTimes(1);
      expect(onRetry).toHaveBeenCalledWith(expect.objectContaining({
        attempt: 1,
        maxRetries: 3
      }));
    });
    
    test('should call onQueueUpdate callback', () => {
      const onQueueUpdate = jest.fn();
      fetcher = new ResilientFetcher({ onQueueUpdate });
      
      fetcher.pendingRequests.set('test', { id: 'test', url: '/test' });
      fetcher._removeFromQueue('test');
      
      expect(onQueueUpdate).toHaveBeenCalledWith('removed', expect.any(Object));
    });
  });
  
  describe('Statistics', () => {
    test('should track request statistics', async () => {
      fetch
        .mockResolvedValueOnce({ ok: true })
        .mockRejectedValueOnce(new TypeError('Network error'))
        .mockRejectedValueOnce(new TypeError('Network error'));
      
      await fetcher.fetch('/api/success');
      
      await expect(fetcher.fetch('/api/fail')).rejects.toThrow();
      
      const stats = fetcher.getStats();
      
      expect(stats.totalRequests).toBe(2);
      expect(stats.successfulRequests).toBe(1);
      expect(stats.failedRequests).toBe(1);
    });
    
    test('should track queue statistics', async () => {
      navigator.onLine = false;
      
      await expect(fetcher.fetch('/api/offline1')).rejects.toThrow();
      await expect(fetcher.fetch('/api/offline2')).rejects.toThrow();
      
      const stats = fetcher.getStats();
      
      expect(stats.queuedRequests).toBe(2);
      expect(stats.pendingRequests).toBe(2);
    });
  });
  
  describe('Error Classes', () => {
    test('NetworkError should have correct properties', () => {
      const error = new NetworkError('Offline', { code: 'NO_NETWORK' });
      
      expect(error.name).toBe('NetworkError');
      expect(error.message).toBe('Offline');
      expect(error.metadata.code).toBe('NO_NETWORK');
    });
    
    test('HTTPError should have status code', () => {
      const error = new HTTPError('Not Found', 404, 'Resource not found');
      
      expect(error.name).toBe('HTTPError');
      expect(error.status).toBe(404);
      expect(error.body).toBe('Resource not found');
    });
    
    test('MaxRetriesExceededError should have metadata', () => {
      const error = new MaxRetriesExceededError('Max retries exceeded', {
        attempts: 4,
        requestId: 'test-123'
      });
      
      expect(error.name).toBe('MaxRetriesExceededError');
      expect(error.metadata.attempts).toBe(4);
      expect(error.metadata.requestId).toBe('test-123');
    });
  });
  
  describe('Cleanup', () => {
    test('should remove event listeners on destroy', () => {
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');
      
      fetcher.destroy();
      
      expect(removeEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
      expect(removeEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));
    });
    
    test('should clear intervals on destroy', () => {
      const clearIntervalSpy = jest.spyOn(window, 'clearInterval');
      
      fetcher.destroy();
      
      expect(clearIntervalSpy).toHaveBeenCalled();
    });
  });
});