class QuizTimer {
    constructor(durationSeconds, options = {}) {
        this.duration = durationSeconds;
        this.remaining = durationSeconds;
        this.isRunning = false;
        this.isPaused = false;
        this.intervalId = null;
        this.serverOffset = 0;
        this.questionStartTime = null;
        this.onTick = options.onTick || null;
        this.onExpire = options.onExpire || null;
        this.warningThreshold = options.warningThreshold || 10;
        this.displayElement = options.displayElement || null;
        this.init();
    }

    init() {
        this.calculateServerOffset();
        this.render();
    }

    async calculateServerOffset() {
        try {
            const clientTime = Date.now();
            const response = await fetch('/api/server-time/', {
                method: 'GET',
                cache: 'no-cache'
            });
            const data = await response.json();
            const serverTime = data.timestamp || Date.now();
            const roundTripTime = Date.now() - clientTime;
            this.serverOffset = serverTime + roundTripTime / 2 - clientTime;
        } catch (error) {
            this.serverOffset = 0;
        }
    }

    getSyncedTime() {
        return Date.now() + this.serverOffset;
    }

    start(serverStartTime = null) {
        if (this.isRunning && !this.isPaused) return;
        
        this.isRunning = true;
        this.isPaused = false;
        this.questionStartTime = serverStartTime || this.getSyncedTime();
        
        this.intervalId = setInterval(() => {
            const currentTime = this.getSyncedTime();
            const elapsed = Math.floor((currentTime - this.questionStartTime) / 1000);
            this.remaining = Math.max(0, this.duration - elapsed);
            
            this.updateDisplay();
            
            if (this.onTick) {
                this.onTick(this.remaining);
            }
            
            if (this.remaining <= 0) {
                this.expire();
            }
        }, 1000);
        
        this.updateDisplay();
    }

    pause() {
        if (!this.isRunning || this.isPaused) return;
        
        this.isPaused = true;
        clearInterval(this.intervalId);
        this.intervalId = null;
    }

    resume() {
        if (!this.isPaused) return;
        
        this.isPaused = false;
        const elapsedBeforePause = this.duration - this.remaining;
        this.questionStartTime = this.getSyncedTime() - (elapsedBeforePause * 1000);
        this.start();
    }

    stop() {
        this.isRunning = false;
        this.isPaused = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    reset() {
        this.stop();
        this.remaining = this.duration;
        this.questionStartTime = null;
        this.updateDisplay();
    }

    expire() {
        this.stop();
        this.remaining = 0;
        this.updateDisplay();
        
        if (this.onExpire) {
            this.onExpire();
        }
        
        this.autoSubmitEmptyAnswer();
    }

    async autoSubmitEmptyAnswer() {
        if (!window.ws || window.ws.readyState !== WebSocket.OPEN) return;
        
        window.ws.send(JSON.stringify({
            action: 'submit_answer',
            question_id: window.currentQuestion?.question_id,
            answer_id: null,
            time_expired: true,
            timestamp: this.getSyncedTime()
        }));
    }

    formatTime(seconds) {
        if (seconds < 0) seconds = 0;
        
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    updateDisplay() {
        if (!this.displayElement) return;
        
        const timeString = this.formatTime(this.remaining);
        this.displayElement.textContent = timeString;
        
        if (this.remaining <= this.warningThreshold) {
            this.displayElement.classList.add('timer-warning');
        } else {
            this.displayElement.classList.remove('timer-warning');
        }
        
        if (this.remaining <= 0) {
            this.displayElement.classList.add('timer-expired');
        } else {
            this.displayElement.classList.remove('timer-expired');
        }
    }

    render() {
        if (this.displayElement) {
            this.updateDisplay();
        }
    }

    getRemainingSeconds() {
        return this.remaining;
    }

    isTimeExpired() {
        return this.remaining <= 0;
    }

    syncWithServer() {
        return this.calculateServerOffset();
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = QuizTimer;
}

if (typeof window !== 'undefined') {
    window.QuizTimer = QuizTimer;
}