"""WebSocket consumer для интерактивного прохождения квиза."""
import json
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from app.models import QuizSession, Question, Participant, AnswerOption, ParticipantAnswer


class QuizConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_code = self.scope['url_route']['kwargs']['session_code']
        self.group_name = f'quiz_{self.session_code}'
        self.participant_id = None
        self.current_question_index = 0
        self.question_start_time = None

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'join':
            await self.handle_join(data)
        elif action == 'start_quiz':
            await self.handle_start_quiz()
        elif action == 'next_question':
            await self.handle_next_question()
        elif action == 'submit_answer':
            await self.handle_submit_answer(data)
        elif action == 'sync_time':
            await self.send_time_sync()

    async def handle_join(self, data):
        participant_name = data.get('name')
        if not participant_name:
            await self.send(text_data=json.dumps({'error': 'Name required'}))
            return

        session = await sync_to_async(QuizSession.objects.select_related('quiz').get)(
            session_code=self.session_code, is_active=True
        )

        participant, _ = await sync_to_async(Participant.objects.get_or_create)(
            session=session,
            name=participant_name,
            defaults={'total_score': 0}
        )
        self.participant_id = participant.id

        await self.send(text_data=json.dumps({
            'type': 'joined',
            'data': {
                'participant_id': participant.id,
                'quiz_title': session.quiz.title,
                'session_code': self.session_code
            }
        }))

    async def handle_start_quiz(self):
        if not self.participant_id:
            return

        await self.send_current_question()

    async def send_current_question(self):
        session = await sync_to_async(QuizSession.objects.prefetch_related(
            'quiz__questions__answers'
        ).get)(session_code=self.session_code, is_active=True)

        questions = list(await sync_to_async(list)(
            session.quiz.questions.order_by('order').all()
        ))

        if self.current_question_index >= len(questions):
            await self.send_quiz_complete()
            return

        question = questions[self.current_question_index]
        self.question_start_time = int(time.time() * 1000)

        await self.send(text_data=json.dumps({
            'type': 'question',
            'data': {
                'question_id': question.id,
                'text': question.text,
                'order': question.order,
                'total': len(questions),
                'timer_seconds': question.timer_seconds or 0,
                'started_at': self.question_start_time,
                'options': [
                    {'id': opt.id, 'text': opt.text}
                    for opt in question.answers.all()
                ]
            }
        }))

    async def handle_next_question(self):
        self.current_question_index += 1
        await self.send_current_question()

    async def handle_submit_answer(self, data):
        if not self.participant_id:
            return

        question_id = data.get('question_id')
        answer_id = data.get('answer_id')
        time_expired = data.get('time_expired', False)

        question = await sync_to_async(Question.objects.prefetch_related('answers').get)(id=question_id)
        correct_answer = await sync_to_async(lambda: question.answers.filter(is_correct=True).first())()

        is_correct = False
        if answer_id and correct_answer and answer_id == correct_answer.id:
            is_correct = True

        if time_expired:
            is_correct = False

        await sync_to_async(self._save_participant_answer)(
            self.participant_id, question_id, answer_id, is_correct
        )

        if is_correct:
            await sync_to_async(self._add_score)(self.participant_id, 10)

        await self.send(text_data=json.dumps({
            'type': 'answer_result',
            'data': {
                'is_correct': is_correct,
                'correct_answer_id': correct_answer.id if correct_answer else None,
                'time_expired': time_expired
            }
        }))

    def _save_participant_answer(self, participant_id, question_id, answer_id, is_correct):
        answer = None
        if answer_id:
            answer = AnswerOption.objects.get(id=answer_id)
        ParticipantAnswer.objects.create(
            participant_id=participant_id,
            question_id=question_id,
            answer=answer,
            is_correct=is_correct
        )

    def _add_score(self, participant_id, points):
        participant = Participant.objects.get(id=participant_id)
        participant.total_score += points
        participant.save(update_fields=['total_score'])

    async def send_quiz_complete(self):
        participant = await sync_to_async(Participant.objects.get)(id=self.participant_id)
        await self.send(text_data=json.dumps({
            'type': 'quiz_complete',
            'data': {
                'total_score': participant.total_score,
                'message': 'Квиз завершён!'
            }
        }))

    async def send_time_sync(self):
        await self.send(text_data=json.dumps({
            'type': 'time_sync',
            'data': {'server_time': int(time.time() * 1000)}
        }))

    async def quiz_message(self, event):
        await self.send(text_data=json.dumps({'message': event['message']}))
