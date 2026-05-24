class AnswerSender {
  constructor(sessionId) {
    this.sessionId = sessionId;
    this.isSending = false;
    this.lastPayload = null;
    this.retryCount = 0;
    this.maxRetries = 3;
  }

  validate(answerId) {
    return answerId !== null && answerId !== undefined && answerId !== '';
  }

  setStatus(status, message = '') {
    // можно заменить на UI-рендеринг
    console.log(`[ANSWER STATUS] ${status}`, message);
  }

  log(payload, status) {
    console.log('[ANSWER LOG]', {
      payload,
      status,
      timestamp: new Date().toISOString()
    });
  }

  async send(answerId) {
    if (this.isSending) return { ok: false, error: 'ALREADY_SENDING' };

    if (!this.validate(answerId)) {
      this.setStatus('error', 'Invalid answer');
      return { ok: false, error: 'INVALID_ANSWER' };
    }

    this.isSending = true;
    this.setStatus('loading');

    const payload = { answer_id: answerId };
    this.lastPayload = payload;

    try {
      const result = await this._sendWithRetry(payload);

      if (result.ok) {
        this.setStatus('success');
        this.log(payload, 'success');
      } else {
        this.setStatus('error', result.error);
        this.log(payload, 'error');
      }

      return result;
    } finally {
      this.isSending = false;
    }
  }

  async _sendWithRetry(payload) {
    this.retryCount = 0;

    while (this.retryCount <= this.maxRetries) {
      try {
        const res = await fetch(`/api/v1/sessions/${this.sessionId}/answer/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const text = await res.text();
          throw new Error(`HTTP ${res.status}: ${text}`);
        }

        const data = await res.json();

        // подтверждение получения от сервера
        if (!data || data.status !== 'ack') {
          throw new Error('No ACK from server');
        }

        return { ok: true, data };

      } catch (err) {
        this.retryCount++;

        console.warn(`Send attempt ${this.retryCount} failed`, err);

        if (this.retryCount > this.maxRetries) {
          return { ok: false, error: err.message };
        }

        await this._delay(500 * this.retryCount); // exponential backoff
      }
    }
  }

  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

export default AnswerSender;