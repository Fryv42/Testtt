/**
 * @jest-environment jsdom
 */
import { createQuiz, getQuizzes, getQuizDetail, updateQuiz, deleteQuiz } from '../api.js';

global.fetch = jest.fn();

beforeEach(() => {
    fetch.mockClear();
    Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrftoken=testcsrf123;',
    });
});

describe('Quiz API', () => {
    const mockQuiz = { id: 1, title: 'Test Quiz', questions: [] };
    const baseUrl = '/api';

    test('createQuiz отправляет POST-запрос с CSRF', async () => {
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockQuiz,
        });

        const result = await createQuiz({ title: 'New Quiz' });
        expect(fetch).toHaveBeenCalledWith(`${baseUrl}/quizzes/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': 'testcsrf123',
            },
            body: JSON.stringify({ title: 'New Quiz' }),
        });
        expect(result).toEqual(mockQuiz);
    });

    test('getQuizzes возвращает список квизов', async () => {
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => [mockQuiz],
        });
        const result = await getQuizzes();
        expect(result).toEqual([mockQuiz]);
    });

    test('getQuizDetail требует ID', async () => {
        await expect(getQuizDetail()).rejects.toThrow('Quiz ID is required');
        expect(fetch).not.toHaveBeenCalled();
    });

    test('getQuizDetail успешный запрос', async () => {
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockQuiz,
        });
        const result = await getQuizDetail(1);
        expect(fetch).toHaveBeenCalledWith(`${baseUrl}/quizzes/1/`, expect.any(Object));
        expect(result).toEqual(mockQuiz);
    });

    test('updateQuiz отправляет PUT', async () => {
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ ...mockQuiz, title: 'Updated' }),
        });
        const result = await updateQuiz(1, { title: 'Updated' });
        expect(fetch).toHaveBeenCalledWith(`${baseUrl}/quizzes/1/`, {
            method: 'PUT',
            headers: expect.objectContaining({ 'X-CSRFToken': 'testcsrf123' }),
            body: JSON.stringify({ title: 'Updated' }),
        });
        expect(result.title).toBe('Updated');
    });

    test('deleteQuiz отправляет DELETE и возвращает null при 204', async () => {
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 204,
            json: async () => null,
        });
        const result = await deleteQuiz(1);
        expect(fetch).toHaveBeenCalledWith(`${baseUrl}/quizzes/1/`, {
            method: 'DELETE',
            headers: expect.any(Object),
        });
        expect(result).toBeNull();
    });

    test('обработка ошибки 404', async () => {
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 404,
            statusText: 'Not Found',
            json: async () => ({ detail: 'Quiz not found' }),
        });
        await expect(getQuizDetail(999)).rejects.toThrow('Quiz not found');
        await expect(getQuizDetail(999)).rejects.toMatchObject({ status: 404 });
    });

    test('обработка ошибки 500', async () => {
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 500,
            statusText: 'Internal Server Error',
        });
        await expect(getQuizzes()).rejects.toThrow('Ошибка 500: Internal Server Error');
    });

    test('генерируются события loading-start и loading-end', async () => {
        const startHandler = jest.fn();
        const endHandler = jest.fn();
        window.addEventListener('api:loading-start', startHandler);
        window.addEventListener('api:loading-end', endHandler);

        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({}),
        });
        await getQuizzes();

        expect(startHandler).toHaveBeenCalled();
        expect(endHandler).toHaveBeenCalled();

        window.removeEventListener('api:loading-start', startHandler);
        window.removeEventListener('api:loading-end', endHandler);
    });
});