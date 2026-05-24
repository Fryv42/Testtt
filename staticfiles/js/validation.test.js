/**
 * @jest-environment jsdom
 */


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

describe('Валидация полей', () => {
    test('title: корректный (>=5 символов)', () => {
        expect(validators.title('Привет')).toBe(true);
        expect(validators.title('Длинный заголовок')).toBe(true);
    });

    test('title: некорректный (<5 символов)', () => {
        expect(validators.title('Нет')).toBe(false);
        expect(validators.title('')).toBe(false);
        expect(validators.title('   ')).toBe(false);
        expect(validators.title(null)).toBe(false);
    });

    test('description: макс 1000 символов', () => {
        const longStr = 'a'.repeat(1000);
        expect(validators.description(longStr)).toBe(true);
        expect(validators.description('Короткое')).toBe(true);
        expect(validators.description('')).toBe(true);
        expect(validators.description(null)).toBe(true);
        const tooLong = 'a'.repeat(1001);
        expect(validators.description(tooLong)).toBe(false);
    });

    test('questionText: мин 10 символов', () => {
        expect(validators.questionText('Десять букв')).toBe(true);
        expect(validators.questionText('1234567890')).toBe(true);
        expect(validators.questionText('Маловато')).toBe(false);
        expect(validators.questionText('')).toBe(false);
    });

    test('answers: минимум 2 непустых варианта', () => {
        const mockInputs = (values) => values.map(v => ({ value: v, valueOf: () => v }));
        let inputs = mockInputs(['a', 'b']);
        expect(validators.answers(inputs)).toBe(true);

        inputs = mockInputs(['a', '']);
        expect(validators.answers(inputs)).toBe(false);

        inputs = mockInputs(['', '']);
        expect(validators.answers(inputs)).toBe(false);

        inputs = mockInputs(['a', 'b', 'c']);
        expect(validators.answers(inputs)).toBe(true);
    });

    test('email: корректные адреса', () => {
        expect(validators.email('user@example.com')).toBe(true);
        expect(validators.email('name.surname@domain.co.uk')).toBe(true);
        expect(validators.email('test+alias@mail.ru')).toBe(true);
    });

    test('email: некорректные адреса', () => {
        expect(validators.email('user@')).toBe(false);
        expect(validators.email('user@domain')).toBe(false);
        expect(validators.email('user@.com')).toBe(false);
        expect(validators.email('user@domain.c')).toBe(false);
        expect(validators.email('user name@domain.com')).toBe(false);
        expect(validators.email('')).toBe(false);
        expect(validators.email(null)).toBe(false);
    });

    test('password: мин 8 символов, буквы и цифры', () => {
        expect(validators.password('Password1')).toBe(true);
        expect(validators.password('12345abcD')).toBe(true);
        expect(validators.password('onlyletters')).toBe(false);
        expect(validators.password('12345678')).toBe(false);
        expect(validators.password('short1')).toBe(false);
        expect(validators.password('')).toBe(false);
    });
});

describe('Интеграция с DOM', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <form id="testForm">
                <input name="title" data-validate="title" value="Valid title">
                <div class="answers-group">
                    <input class="answer-input" value="Answer 1">
                    <input class="answer-input" value="Answer 2">
                </div>
                <button type="submit">Send</button>
            </form>
        `;
    });

    test('форма проходит валидацию с корректными данными', () => {
        const form = document.getElementById('testForm');
        const titleInput = form.querySelector('[name="title"]');
        const answerInputs = form.querySelectorAll('.answer-input');
        
        expect(validators.title(titleInput.value)).toBe(true);
        expect(validators.answers(answerInputs)).toBe(true);
    });
});