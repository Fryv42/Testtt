const QuizTimer = require('../timer');

describe('QuizTimer', () => {
    let timer;
    let mockDisplayElement;

    beforeEach(() => {
        mockDisplayElement = {
            textContent: '',
            classList: {
                add: jest.fn(),
                remove: jest.fn()
            }
        };
        
        timer = new QuizTimer(60, {
            displayElement: mockDisplayElement,
            warningThreshold: 10
        });
    });

    afterEach(() => {
        if (timer) {
            timer.stop();
        }
        jest.clearAllMocks();
    });

    describe('Initialization', () => {
        test('should create timer with correct initial values', () => {
            expect(timer.duration).toBe(60);
            expect(timer.remaining).toBe(60);
            expect(timer.isRunning).toBe(false);
            expect(timer.isPaused).toBe(false);
        });

        test('should format time correctly', () => {
            expect(timer.formatTime(0)).toBe('00:00');
            expect(timer.formatTime(5)).toBe('00:05');
            expect(timer.formatTime(60)).toBe('01:00');
            expect(timer.formatTime(125)).toBe('02:05');
        });

        test('should handle negative time', () => {
            expect(timer.formatTime(-5)).toBe('00:00');
        });
    });

    describe('Timer Controls', () => {
        test('should start timer', () => {
            jest.useFakeTimers();
            timer.start();
            
            expect(timer.isRunning).toBe(true);
            expect(timer.isPaused).toBe(false);
            
            jest.advanceTimersByTime(1000);
            expect(timer.remaining).toBeLessThanOrEqual(59);
            
            timer.stop();
            jest.useRealTimers();
        });

        test('should pause timer', () => {
            jest.useFakeTimers();
            timer.start();
            jest.advanceTimersByTime(2000);
            
            const remainingBeforePause = timer.remaining;
            timer.pause();
            
            expect(timer.isPaused).toBe(true);
            jest.advanceTimersByTime(5000);
            
            expect(timer.remaining).toBe(remainingBeforePause);
            
            timer.stop();
            jest.useRealTimers();
        });

        test('should resume paused timer', () => {
            jest.useFakeTimers();
            timer.start();
            jest.advanceTimersByTime(2000);
            timer.pause();
            
            timer.resume();
            
            expect(timer.isPaused).toBe(false);
            expect(timer.isRunning).toBe(true);
            
            jest.advanceTimersByTime(1000);
            expect(timer.remaining).toBeLessThan(58);
            
            timer.stop();
            jest.useRealTimers();
        });

        test('should reset timer', () => {
            jest.useFakeTimers();
            timer.start();
            jest.advanceTimersByTime(5000);
            
            timer.reset();
            
            expect(timer.remaining).toBe(60);
            expect(timer.isRunning).toBe(false);
            
            jest.useRealTimers();
        });
    });

    describe('Display Updates', () => {
        test('should update display with correct time format', () => {
            timer.updateDisplay();
            expect(mockDisplayElement.textContent).toBe('01:00');
        });

        test('should add warning class when time is low', () => {
            timer.remaining = 10;
            timer.updateDisplay();
            expect(mockDisplayElement.classList.add).toHaveBeenCalledWith('timer-warning');
        });

        test('should remove warning class when time is sufficient', () => {
            timer.remaining = 15;
            timer.updateDisplay();
            expect(mockDisplayElement.classList.remove).toHaveBeenCalledWith('timer-warning');
        });

        test('should add expired class when time is up', () => {
            timer.remaining = 0;
            timer.updateDisplay();
            expect(mockDisplayElement.classList.add).toHaveBeenCalledWith('timer-expired');
        });
    });

    describe('Expiration', () => {
        test('should call onExpire callback when time expires', (done) => {
            const onExpireMock = jest.fn();
            
            timer = new QuizTimer(1, {
                onExpire: onExpireMock,
                displayElement: mockDisplayElement
            });
            
            timer.start();
            
            setTimeout(() => {
                expect(onExpireMock).toHaveBeenCalled();
                expect(timer.remaining).toBe(0);
                timer.stop();
                done();
            }, 1500);
        });

        test('should stop timer when expired', () => {
            timer.remaining = 0;
            timer.expire();
            
            expect(timer.isRunning).toBe(false);
            expect(timer.remaining).toBe(0);
        });
    });

    describe('Server Time Sync', () => {
        test('should calculate server time offset', async () => {
            global.fetch = jest.fn(() =>
                Promise.resolve({
                    json: () => Promise.resolve({ timestamp: Date.now() })
                })
            );
            
            await timer.syncWithServer();
            
            expect(fetch).toHaveBeenCalledWith('/api/server-time/', {
                method: 'GET',
                cache: 'no-cache'
            });
        });

        test('should handle server sync failure gracefully', async () => {
            global.fetch = jest.fn(() =>
                Promise.reject(new Error('Network error'))
            );
            
            await timer.syncWithServer();
            
            expect(timer.serverOffset).toBe(0);
        });

        test('should get synced time', () => {
            timer.serverOffset = 1000;
            const syncedTime = timer.getSyncedTime();
            
            expect(syncedTime).toBeGreaterThan(Date.now() - 100);
            expect(syncedTime).toBeLessThan(Date.now() + 2000);
        });
    });

    describe('Edge Cases', () => {
        test('should handle very large time values', () => {
            timer = new QuizTimer(86400, {
                displayElement: mockDisplayElement
            });
            
            expect(timer.formatTime(86400)).toBe('1440:00');
        });

        test('should handle zero time', () => {
            timer = new QuizTimer(0, {
                displayElement: mockDisplayElement
            });
            
            expect(timer.remaining).toBe(0);
            expect(timer.isTimeExpired()).toBe(true);
        });

        test('should prevent negative remaining time', () => {
            timer.remaining = -5;
            timer.updateDisplay();
            expect(mockDisplayElement.textContent).toBe('00:00');
        });

        test('should handle rapid pause/resume cycles', () => {
            jest.useFakeTimers();
            timer.start();
            
            for (let i = 0; i < 10; i++) {
                timer.pause();
                timer.resume();
            }
            
            expect(timer.isRunning).toBe(true);
            expect(timer.isPaused).toBe(false);
            
            timer.stop();
            jest.useRealTimers();
        });
    });

    describe('onTick callback', () => {
        test('should call onTick callback every second', (done) => {
            const onTickMock = jest.fn();
            
            timer = new QuizTimer(3, {
                onTick: onTickMock,
                displayElement: mockDisplayElement
            });
            
            timer.start();
            
            setTimeout(() => {
                expect(onTickMock).toHaveBeenCalledTimes(3);
                timer.stop();
                done();
            }, 3500);
        });
    });
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { QuizTimer };
}