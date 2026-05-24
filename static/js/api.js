
const API_BASE_URL = '/api';

const emitLoadingStart = () => window.dispatchEvent(new CustomEvent('api:loading-start'));
const emitLoadingEnd = () => window.dispatchEvent(new CustomEvent('api:loading-end'));

function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    return cookieValue ? cookieValue.split('=')[1] : null;
}

async function request(url, options = {}) {
    emitLoadingStart();
    try {
        const csrfToken = getCSRFToken();
        const headers = {
            'Content-Type': 'application/json',
            ...(csrfToken && { 'X-CSRFToken': csrfToken }),
            ...options.headers,
        };

        const response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            headers,
        });

        if (!response.ok) {
            let errorMessage = `Ошибка ${response.status}: ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || errorMessage;
            } catch (e) { /* ответ не JSON, оставляем стандартное сообщение */ }
            const error = new Error(errorMessage);
            error.status = response.status;
            throw error;
        }

        if (response.status === 204) return null;
        return await response.json();
    } finally {
        emitLoadingEnd();
    }
}

export async function createQuiz(data) {
    return request('/quizzes/', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

export async function getQuizzes() {
    return request('/quizzes/');
}

export async function getQuizDetail(id) {
    if (!id) throw new Error('Quiz ID is required');
    return request(`/quizzes/${id}/`);
}

export async function updateQuiz(id, data) {
    if (!id) throw new Error('Quiz ID is required');
    return request(`/quizzes/${id}/`, {
        method: 'PUT',
        body: JSON.stringify(data),
    });
}

export async function deleteQuiz(id) {
    if (!id) throw new Error('Quiz ID is required');
    return request(`/quizzes/${id}/`, {
        method: 'DELETE',
    });
}