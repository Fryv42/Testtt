
import { QuizWebSocketClient } from './websocket.js';

class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.listeners = {};
    setTimeout(() => {
      if (this.onopen) {
        this.readyState = WebSocket.OPEN;
        this.onopen({ type: 'open' });
      }
    }, 0);
  }
  
  addEventListener(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }
  
  removeEventListener(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }
  
  send(data) {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket не открыт');
    }
    return true;
  }
  
  close(code = 1000, reason = '') {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ code, reason, wasClean: true });
    }
  }
  simulateMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }
  
  simulateError(error) {
    if (this.onerror) {
      this.onerror(error || { type: 'error' });
    }
  }
  
  simulateClose(code = 1006, reason = 'Соединение потеряно') {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ code, reason, wasClean: false });
    }
  }
}

WebSocket.CONNECTING = 0;
WebSocket.OPEN = 1;
WebSocket.CLOSING = 2;
WebSocket.CLOSED = 3;

describe('QuizWebSocketClient', () => {
  let mockWs;
  let client;
  let originalWebSocket;
  
  beforeEach(() => {
    originalWebSocket = global.WebSocket;
    global.WebSocket = jest.fn((url) => {
      mockWs = new MockWebSocket(url);
      return mockWs;
    });
    jest.useFakeTimers();
  });
  
  afterEach(() => {
    if (client) {
      client.disconnect();
    }
    global.WebSocket = originalWebSocket;
    jest.useRealTimers();
    jest.clearAllMocks();
  });
  
  describe('Constructor and Initialization', () => {
    test('Надо создать экземпляр с действительным кодом сессии.', () => {
      client = new QuizWebSocketClient('TEST123');
      expect(client).toBeInstanceOf(QuizWebSocketClient);
      expect(client.sessionCode).toBe('TEST123');
    });
    
    test('Вызывать ошибку без session code', () => {
      expect(() => new QuizWebSocketClient()).toThrow('Нужен Session Code');
      expect(() => new QuizWebSocketClient('')).toThrow('Нужен Session Code');
    });
    
    test('Инициализация с параметрами по умолчанию', () => {
      client = new QuizWebSocketClient('TEST123');
      expect(client.options.maxReconnectAttempts).toBe(5);
      expect(client.options.reconnectDelay).toBe(1000);
      expect(client.options.debug).toBe(false);
    });
    
    test('должны переопределять параметры по умолчанию', () => {
      const options = {
        maxReconnectAttempts: 3,
        reconnectDelay: 2000,
        debug: true,
        onStatusChange: jest.fn(),
        onMessage: jest.fn(),
        onError: jest.fn()
      };
      
      client = new QuizWebSocketClient('TEST123', options);
      expect(client.options.maxReconnectAttempts).toBe(3);
      expect(client.options.reconnectDelay).toBe(2000);
      expect(client.options.debug).toBe(true);
    });
    
    test('Попытаться создать подключение сразу, () => {
      client = new QuizWebSocketClient('TEST123');
      expect(global.WebSocket).toHaveBeenCalled();
    });
  });
  
  describe('Connection Management', () => {
    test('Корректность url WebSocket-а', () => {
      delete window.location;
      window.location = { protocol: 'http:', host: 'localhost:8000' };
      
      client = new QuizWebSocketClient('ABC123');
      const url = client._getWebSocketUrl();
      expect(url).toBe('ws://localhost:8000/ws/quiz/ABC123/');
    });
    
    test('Использовать протокол wss для HTTPS', () => {
      delete window.location;
      window.location = { protocol: 'https:', host: 'example.com' };
      
      client = new QuizWebSocketClient('ABC123');
      const url = client._getWebSocketUrl();
      expect(url).toBe('wss://example.com/ws/quiz/ABC123/');
    });
    
    test('Обновление статуса до подключения', () => {
      const onStatusChange = jest.fn();
      client = new QuizWebSocketClient('TEST123', { onStatusChange });
      
      expect(onStatusChange).toHaveBeenCalledWith('connecting', expect.any(Object));
    });
    
    test('Обновление статуса до успешного подключения', () => {
      const onStatusChange = jest.fn();
      client = new QuizWebSocketClient('TEST123', { onStatusChange });
      
      jest.runAllTimers();
      
      expect(onStatusChange).toHaveBeenCalledWith('connected', expect.any(Object));
      expect(client.isConnected()).toBe(true);
    });
  });
  
  describe('Message Handling', () => {
    test('Обработка входящих сообщений', () => {
      const onMessage = jest.fn();
      client = new QuizWebSocketClient('TEST123', { onMessage });
      
      jest.runAllTimers();
      
      const testData = { event: { type: 'quiz_start', data: { quiz_id: 1 } } };
      mockWs.simulateMessage(testData);
      
      expect(onMessage).toHaveBeenCalledWith(testData, expect.any(Object));
    });
    
    test('Обработка некорректного JSON', () => {
      const onError = jest.fn();
      client = new QuizWebSocketClient('TEST123', { onError });
      
      jest.runAllTimers();
      if (mockWs.onmessage) {
        mockWs.onmessage({ data: 'invalid json{' });
      }
      
      expect(onError).toHaveBeenCalled();
    });
    
    test('Отслеживание статистики сообщений', () => {
      client = new QuizWebSocketClient('TEST123');
      jest.runAllTimers();
      
      mockWs.simulateMessage({ type: 'test' });
      mockWs.simulateMessage({ type: 'test2' });
      
      const state = client.getState();
      expect(state.stats.messagesReceived).toBe(2);
    });
  });
  
  describe('Reconnection Logic', () => {
    test('Попытка переподключения', () => {
      client = new QuizWebSocketClient('TEST123');
      jest.runAllTimers();
      
      const connectSpy = jest.spyOn(client, 'connect');
      
      mockWs.simulateClose(1006, 'Connection lost');
      expect(client.reconnectTimer).not.toBeNull();
      jest.advanceTimersByTime(1000);
      
      expect(connectSpy).toHaveBeenCalled();
    });
    
    test('Использование экспоненциальной задержки для переподключения.', () => {
      client = new QuizWebSocketClient('TEST123');
      jest.runAllTimers();
      mockWs.simulateClose();
      expect(client.reconnectAttempts).toBe(1);
      jest.advanceTimersByTime(1000);
      mockWs.simulateClose();
      expect(client.reconnectAttempts).toBe(2);
    });
    
    test('Остановка попыток переподключения после некоторого кол-ва попыток', () => {
      const onStatusChange = jest.fn();
      client = new QuizWebSocketClient('TEST123', { 
        maxReconnectAttempts: 3,
        onStatusChange 
      });
      
      jest.runAllTimers();

      for (let i = 0; i < 3; i++) {
        mockWs.simulateClose();
        jest.advanceTimersByTime(client.options.reconnectDelay * Math.pow(2, i));
      }
      mockWs.simulateClose();
      jest.advanceTimersByTime(10000);
      
      expect(onStatusChange).toHaveBeenCalledWith('error', expect.objectContaining({
        reason: 'Max reconnection attempts reached'
      }));
      expect(client.reconnectAttempts).toBe(3);
    });
    
    test('При отключении по нормальным причинам не пытаться переподключиться', () => {
      client = new QuizWebSocketClient('TEST123');
      jest.runAllTimers();
      
      const connectSpy = jest.spyOn(client, 'connect');
      client.disconnect();
      
      expect(client.isManualClose).toBe(true);
      mockWs.simulateClose();
      
      jest.advanceTimersByTime(5000);
      expect(connectSpy).not.toHaveBeenCalled();
    });
  });
  
  describe('Send Functionality', () => {
    test('Сообщение при подключении', () => {
      client = new QuizWebSocketClient('TEST123');
      jest.runAllTimers();
      
      const sendSpy = jest.spyOn(mockWs, 'send');
      
      const testData = { type: 'answer', answer_id: 1 };
      const result = client.send(testData);
      
      expect(result).toBe(true);
      expect(sendSpy).toHaveBeenCalledWith(JSON.stringify(testData));
      expect(client.stats.messagesSent).toBe(1);
    });
    
    test('Отсутствие сообщений, если не подключено', () => {
      client = new QuizWebSocketClient('TEST123');
      const result = client.send({ test: 'data' });
      
      expect(result).toBe(false);
    });
    
    test('Обработка ошибок с сообщениями', () => {
      const onError = jest.fn();
      client = new QuizWebSocketClient('TEST123', { onError });
      jest.runAllTimers();
      mockWs.send = jest.fn(() => {
        throw new Error('Send failed');
      });
      
      const result = client.send({ test: 'data' });
      
      expect(result).toBe(false);
      expect(onError).toHaveBeenCalled();
    });
  });
  
  describe('State Management', () => {
    test('Возвращение корректной стадии подключения', () => {
      client = new QuizWebSocketClient('TEST123');
      
      const state = client.getState();
      expect(state.status).toBe('connecting');
      expect(state.sessionCode).toBe('TEST123');
      expect(state.reconnectAttempts).toBe(0);
    });
    
    test('Корректное сообщение стадии подключения', () => {
      client = new QuizWebSocketClient('TEST123');
      expect(client.isConnected()).toBe(false);
      
      jest.runAllTimers();
      expect(client.isConnected()).toBe(true);
    });
    
    test('Сброс попыток переподключения', () => {
      client = new QuizWebSocketClient('TEST123');
      
      client.reconnectAttempts = 5;
      client.resetReconnectAttempts();
      
      expect(client.reconnectAttempts).toBe(0);
    });
  });
  
  describe('Error Handling', () => {
    test('Обработка ошибок WebSocket-а', () => {
      const onError = jest.fn();
      const onStatusChange = jest.fn();
      
      client = new QuizWebSocketClient('TEST123', { onError, onStatusChange });
      
      mockWs.simulateError({ message: 'Network error' });
      
      expect(onError).toHaveBeenCalled();
      expect(onStatusChange).toHaveBeenCalledWith('error', expect.any(Object));
    });
    
    test('Обработка таймаута соединения', () => {
      client = new QuizWebSocketClient('TEST123');
      jest.advanceTimersByTime(30000);
      expect(client.reconnectTimer).not.toBeNull();
    });
  });
  
  describe('Cleanup', () => {
    test('Очистка ресурсов при отключении', () => {
      client = new QuizWebSocketClient('TEST123');
      jest.runAllTimers();
      
      const closeSpy = jest.spyOn(mockWs, 'close');
      
      client.disconnect();
      
      expect(closeSpy).toHaveBeenCalledWith(1000, 'User initiated disconnect');
      expect(client.ws).toBeNull();
      expect(client.reconnectTimer).toBeNull();
    });
    
    test('Обработка загрузки страницы', () => {
      client = new QuizWebSocketClient('TEST123');
      jest.runAllTimers();
      
      const closeSpy = jest.spyOn(mockWs, 'close');
      window.dispatchEvent(new Event('beforeunload'));
      
      expect(client.isManualClose).toBe(true);
      expect(closeSpy).toHaveBeenCalled();
    });
  });
});