# Компонент QuizTimer

## Описание
Обратный отсчет времени для вопросов квиза с серверной синхронизацией, визуальными предупреждениями и автоматической отправкой пустого ответа.

---

## Возможности
- Формат отображения: `MM:SS`
- Синхронизация с серверным временем (компенсация задержки сети)
- Красная индикация + пульсация за последние 10 секунд
- Авто-отправка ответа при `00:00` через WebSocket
- Управление потоком: `start()`, `pause()`, `resume()`, `stop()`
- Callback'и: `onTick(seconds)`, `onExpire()`

---

## HTML
```html
<div id="quiz-timer" class="quiz-timer">--:--</div>
```

---

## CSS
```css
.quiz-timer {
  font-size: 1.5rem;
  font-weight: 700;
  padding: 0.5rem 1rem;
  background: #f8f9fa;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
}

.quiz-timer.timer-warning {
  color: #dc3545;
  background: #ffe6e6;
  animation: pulse 1s infinite;
}

.quiz-timer.timer-expired {
  color: #fff;
  background: #dc3545;
}

@keyframes pulse {
  50% { transform: scale(1.05); }
}
```

---

## JavaScript API
```javascript
class QuizTimer {
  constructor(durationSec, { displayElement, warningThreshold = 10, onTick, onExpire })
  
  start(serverStartTimeMs) // Запуск с серверной меткой
  pause()                  // Приостановка
  resume()                 // Возобновление
  stop()                   // Полная остановка
  reset()                  // Сброс к исходному значению
}
```

---

## Пример использования
```javascript
import QuizTimer from './timer.js';

const timer = new QuizTimer(30, {
  displayElement: document.getElementById('quiz-timer'),
  onExpire: () => submitAnswer(null, true)
});

// Запуск после получения вопроса от сервера
timer.start(questionData.started_at);
```

---

## Интеграция
- Импорт: `import QuizTimer from './timer.js'`
- Требует endpoint `/api/server-time/` для начальной синхронизации
- При истечении времени вызывает `onExpire`, который отправляет `submit_answer` через WebSocket
- Тесты: `static/js/__tests__/timer.test.js`
- Стили: добавляются в `static/css/style.css`