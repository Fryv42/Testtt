
(function() {
    const errorMessages = {
        title: 'Заголовок должен содержать минимум 5 символов.',
        description: 'Описание не должно превышать 1000 символов.',
        questionText: 'Текст вопроса должен содержать минимум 10 символов.',
        answers: 'Необходимо добавить минимум 2 варианта ответа.',
        email: 'Введите корректный email (например, name@domain.com).',
        password: 'Пароль должен быть не менее 8 символов и содержать хотя бы одну цифру и одну букву.'
    };

    const validators = {
        title: (value) => value && value.trim().length >= 5,
        description: (value) => !value || value.length <= 1000,
        questionText: (value) => value && value.trim().length >= 10,
        answers: (answersElements) => {
            let nonEmptyCount = 0;
            answersElements.forEach(input => {
                if (input.value.trim() !== '') nonEmptyCount++;
            });
            return nonEmptyCount >= 2;
        },
        email: (value) => /^[^\s@]+@([^\s@.,]+\.)+[^\s@.,]{2,}$/.test(value),
        password: (value) => {
            if (!value || value.length < 8) return false;
            const hasLetter = /[a-zA-Z]/.test(value);
            const hasDigit = /\d/.test(value);
            return hasLetter && hasDigit;
        }
    };

    function showError(field, message) {
        clearError(field);
        field.classList.add('is-invalid');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        field.parentNode.insertBefore(errorDiv, field.nextSibling);
    }

    function clearError(field) {
        field.classList.remove('is-invalid');
        const next = field.nextSibling;
        if (next && next.classList && next.classList.contains('invalid-feedback')) {
            next.remove();
        }
    }

    function validateField(field) {
        const name = field.getAttribute('data-validate') || field.name;
        if (!validators[name]) {
            clearError(field);
            return true;
        }

        let isValid = false;
        let value = field.value;

        if (name === 'answers') {
            const answersContainer = field.closest('.answers-group');
            if (answersContainer) {
                const answerInputs = answersContainer.querySelectorAll('.answer-input');
                isValid = validators.answers(answerInputs);
            } else {
                isValid = true;
            }
        } else {
            isValid = validators[name](value);
        }

        if (!isValid) {
            showError(field, errorMessages[name] || 'Некорректное значение');
        } else {
            clearError(field);
        }
        return isValid;
    }

    function validateForm(form) {
        let isFormValid = true;
        const fieldsToValidate = form.querySelectorAll('[data-validate], input[name], textarea[name]');
        
        fieldsToValidate.forEach(field => {
            const validateAttr = field.getAttribute('data-validate');
            const fieldName = validateAttr || field.name;
            if (validators[fieldName]) {
                const isValid = validateField(field);
                if (!isValid) isFormValid = false;
            }
        });

        const answersGroup = form.querySelector('.answers-group');
        if (answersGroup && !form.querySelector('[data-validate="answers"]')) {
            const answerInputs = answersGroup.querySelectorAll('.answer-input');
            if (answerInputs.length) {
                const isValid = validators.answers(answerInputs);
                if (!isValid) {
                    showError(answerInputs[0], errorMessages.answers);
                    isFormValid = false;
                }
            }
        }

        return isFormValid;
    }

    function initValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!validateForm(form)) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            });

            const inputs = form.querySelectorAll('[data-validate], input[name], textarea[name]');
            inputs.forEach(input => {
                input.addEventListener('input', () => {
                    if (input.classList.contains('is-invalid')) {
                        validateField(input);
                    }
                });
                input.addEventListener('blur', () => validateField(input));
            });

            const addAnswerBtn = form.querySelector('.add-answer');
            if (addAnswerBtn) {
                addAnswerBtn.addEventListener('click', () => {
                    setTimeout(() => {
                        const answersGroup = form.querySelector('.answers-group');
                        if (answersGroup) {
                            const answerInputs = answersGroup.querySelectorAll('.answer-input');
                            answerInputs.forEach(inp => {
                                inp.removeEventListener('input', () => {});
                                inp.addEventListener('input', () => {
                                    const answersValid = validators.answers(answerInputs);
                                    if (!answersValid) {
                                        showError(answerInputs[0], errorMessages.answers);
                                    } else {
                                        answerInputs.forEach(ai => clearError(ai));
                                    }
                                });
                            });
                        }
                    }, 50);
                });
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initValidation);
    } else {
        initValidation();
    }
})();