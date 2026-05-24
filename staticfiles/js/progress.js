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
    this.text.textContent = `${this.current}/${this.total}`;

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