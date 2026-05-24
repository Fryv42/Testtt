import { createQuiz, getQuizzes, getQuizDetail, updateQuiz, deleteQuiz } from './api.js';

window.addEventListener('api:loading-start', () => {
    const loader = document.getElementById('global-loader');
    if (loader) loader.style.display = 'block';
});

window.addEventListener('api:loading-end', () => {
    const loader = document.getElementById('global-loader');
    if (loader) loader.style.display = 'none';
});

async function loadQuizzes() {
    try {
        const quizzes = await getQuizzes();
        const container = document.getElementById('quizzes-list');
        if (container) {
            container.innerHTML = quizzes.map(q => `<li>${q.title}</li>`).join('');
        }
    } catch (error) {
        console.error('Не удалось загрузить квизы:', error.message);
        alert(`Ошибка: ${error.message}`);
    }
}

async function addNewQuiz(title) {
    try {
        const newQuiz = await createQuiz({ title, questions: [] });
        console.log('Квиз создан:', newQuiz);
        await loadQuizzes(); // обновить список
    } catch (error) {
        console.error('Ошибка создания:', error);
    }
}

window.loadQuizzes = loadQuizzes;
window.addNewQuiz = addNewQuiz;
window.getQuizDetail = (id) => getQuizDetail(id).then(console.log);
window.updateQuiz = (id, data) => updateQuiz(id, data).then(console.log);
window.deleteQuiz = (id) => deleteQuiz(id).then(() => loadQuizzes());