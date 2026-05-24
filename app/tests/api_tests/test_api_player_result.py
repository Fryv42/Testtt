from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from models import Quiz, QuizSession, Participant, Question, AnswerOption, ParticipantAnswer


class SessionResultsAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="admin",
            password="123456"
        )

        self.quiz = Quiz.objects.create(
            title="Python Quiz",
            description="Quiz API Test",
            created_by=self.user
        )

        self.session = QuizSession.objects.create(
            quiz=self.quiz,
            is_active=False
        )
        
        self.question = Question.objects.create(
            quiz=self.quiz,
            text="What is Python?",
            order=1
        )
        
        self.option = AnswerOption.objects.create(
            question=self.question,
            text="Programming Language",
            is_correct=True
        )

        self.participant1 = Participant.objects.create(
            session=self.session,
            name="Alex",
            total_score=200
        )

        self.participant2 = Participant.objects.create(
            session=self.session,
            name="John",
            total_score=100
        )

        # Réponse participant
        ParticipantAnswer.objects.create(
            participant=self.participant1,
            question=self.question,
            answer=self.option,
            is_correct=True,
            response_time_seconds=2.3
        )

    def test_get_results_success(self):

        url = f"/api/v1/sessions/{self.session.id}/results/"

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_results_sorted_by_score_desc(self):

        url = f"/api/v1/sessions/{self.session.id}/results/"

        response = self.client.get(url)

        results = response.data["results"]

        self.assertEqual(results[0]["name"], "Alex")
        self.assertEqual(results[1]["name"], "John")

    def test_answers_are_included(self):

        url = f"/api/v1/sessions/{self.session.id}/results/"

        response = self.client.get(url)

        answers = response.data["results"][0]["answers"]

        self.assertEqual(len(answers), 1)

        self.assertTrue(
            answers[0]["is_correct"]
        )

    def test_response_time_is_included(self):

        url = f"/api/v1/sessions/{self.session.id}/results/"

        response = self.client.get(url)

        answer = response.data["results"][0]["answers"][0]

        self.assertEqual(
            answer["response_time_seconds"],
            2.3
        )

    def test_filter_finished(self):

        url = (
            f"/api/v1/sessions/"
            f"{self.session.id}/results/?status=finished"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            len(response.data["results"]),
            2
        )

        self.assertEqual(
            response.data["results"][0]["status"],
            "finished"
        )

    def test_filter_unfinished(self):

        active_session = QuizSession.objects.create(
            quiz=self.quiz,
            is_active=True
        )

        Participant.objects.create(
            session=active_session,
            name="WaitingPlayer",
            total_score=0
        )

        url = (
            f"/api/v1/sessions/"
            f"{active_session.id}/results/?status=unfinished"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["results"][0]["status"],
            "unfinished"
        )

    def test_pagination_works(self):

        for i in range(25):

            Participant.objects.create(
                session=self.session,
                name=f"User-{i}",
                total_score=i
            )

        url = f"/api/v1/sessions/{self.session.id}/results/"

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            len(response.data["results"]),
            20
        )

        self.assertIsNotNone(
            response.data["next"]
        )

    def test_invalid_session_returns_empty(self):

        url = "/api/v1/sessions/99999/results/"

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            len(response.data["results"]),
            0
        )

    def test_response_structure(self):

        url = f"/api/v1/sessions/{self.session.id}/results/"

        response = self.client.get(url)

        participant = response.data["results"][0]

        self.assertIn("id", participant)
        self.assertIn("name", participant)
        self.assertIn("total_score", participant)
        self.assertIn("status", participant)
        self.assertIn("answers", participant)

    def test_participant_without_answers(self):

        Participant.objects.create(
            session=self.session,
            name="NoAnswers",
            total_score=50
        )

        url = f"/api/v1/sessions/{self.session.id}/results/"

        response = self.client.get(url)

        found = False

        for participant in response.data["results"]:

            if participant["name"] == "NoAnswers":

                found = True

                self.assertEqual(
                    participant["answers"],
                    []
                )

        self.assertTrue(found)