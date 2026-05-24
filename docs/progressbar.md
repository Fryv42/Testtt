# Компонент ProgressBar

## Общее описание

Компонент ProgressBar предназначен для отображения прогресса прохождения теста или опроса. Он визуализирует текущий этап выполнения в виде фиксированного прогресс-бара в верхней части страницы.

---

## Функциональные возможности

- Расчет прогресса по формуле:
  (текущий вопрос / общее количество вопросов) * 100
- Плавная анимация изменения ширины прогресс-бара
- Отображение текстового значения в формате X/Y
- Цветовая индикация этапов:
  - 0–25% — красный
  - 25–50% — оранжевый
  - 50–75% — синий
  - 75–100% — зеленый
- Адаптивность для мобильных устройств
- Простая интеграция в HTML-страницу

---

## HTML структура

<div class="progress-container" id="progress">
  <div class="progress-bar"></div>
  <div class="progress-text">0/0</div>
</div>

---

## CSS

Файл: static/css/progress.css

.progress-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 1000;
  background: #f3f3f3;
}

.progress-bar {
  height: 8px;
  width: 0%;
  background-color: #4caf50;
  transition: width 0.4s ease, background-color 0.3s ease;
}

.progress-text {
  position: absolute;
  top: 10px;
  right: 16px;
  font-size: 14px;
  font-weight: bold;
  color: #333;
}

.progress-bar.progress-25 { background-color: #f44336; }
.progress-bar.progress-50 { background-color: #ff9800; }
.progress-bar.progress-75 { background-color: #2196f3; }
.progress-bar.progress-100 { background-color: #4caf50; }

@media (max-width: 600px) {
  .progress-text {
    font-size: 12px;
    right: 10px;
  }

  .progress-bar {
    height: 6px;
  }
}

---

## JavaScript

Файл: static/js/progress.js

export class ProgressBar {
  constructor({ totalQuestions, container }) {
    this.total = totalQuestions;
    this.current = 0;

    this.container = container;
    this.bar = container.querySelector('.progress-bar');
    this.text = container.querySelector('.progress-text');
  }

  setStep(currentQuestion) {
    this.current = currentQuestion;
    this.update();
  }

  calculatePercent() {
    if (this.total === 0) return 0;
    return Math.round((this.current / this.total) * 100);
  }

  update() {
    const percent = this.calculatePercent();

    this.bar.style.width = percent + '%';
    this.text.textContent = this.current + '/' + this.total;

    this.updateColor(percent);
  }

  updateColor(percent) {
    this.bar.classList.remove(
      'progress-25',
      'progress-50',
      'progress-75',
      'progress-100'
    );

    if (percent >= 100) {
      this.bar.classList.add('progress-100');
    } else if (percent >= 75) {
      this.bar.classList.add('progress-75');
    } else if (percent >= 50) {
      this.bar.classList.add('progress-50');
    } else if (percent >= 25) {
      this.bar.classList.add('progress-25');
    }
  }
}

---

## Пример использования

import { ProgressBar } from './progress.js';

const progress = new ProgressBar({
  totalQuestions: 10,
  container: document.getElementById('progress')
});

progress.setStep(1);

---

## Интеграция

Компонент может использоваться в:

- чистом JavaScript
- Django шаблонах
- Flask приложениях
- любых статических HTML-страницах

---

## Поведение компонента

При вызове setStep:

- обновляется текущий шаг
- пересчитывается процент выполнения
- изменяется ширина прогресс-бара
- обновляется текст X/Y
- обновляется цветовая индикация

---