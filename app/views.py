"""
Представления (views) для API квизов и страниц приложения.
"""
import logging
from django.db import IntegrityError
from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Quiz, QuizSession, Participant
from .serializers import QuizSerializer, QuizSessionSerializer, ParticipantSerializer
from .factories import SessionCodeFactory
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .services import generate_session_csv
from .services import get_quiz_statistics
from django.core.cache import cache
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, serializers, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import NotFound

from .models import SessionParticipant
from .serializers import SessionResultSerializer
from .pagination import ResultsPagination

from .factories import SessionCodeFactory
from .models import Participant, Quiz, QuizSession
from .permissions import IsQuizOwnerOrReadOnly
from .serializers import (
    ParticipantSerializer,
    QuizSerializer,
    QuizSessionSerializer,
    QuizWriteSerializer,
)
from .services import generate_session_csv, get_quiz_statistics

logger = logging.getLogger('app.views')

class CustomLoginView(LoginView):
    template_name = 'app/login.html'
    authentication_form = LoginForm

    def get_success_url(self):
        return '/'

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = RegisterForm()
    return render(request, 'app/register.html', {'form': form})

def index(request):
    """Главная страница."""
    return render(request, 'index.html')


def quiz_create(request):
    """Страница создания квиза."""
    return render(request, 'app/quiz_create.html')


def quiz_edit(request, quiz_id):
    """Страница редактирования квиза."""
    return render(request, 'app/quiz_edit.html', {'quiz_id': quiz_id})


def quiz_join(request):
    """Страница присоединения к квизу."""
    return render(request, 'quize/join.html')

def quiz_play(request, session_code):
    """Страница прохождения квиза"""
    return render(request, 'quize/play.html', {'session_code': session_code})

def quiz_play(request, session_code):
    """Страница прохождения квиза."""
    return render(request, 'quize/play.html', {'session_code': session_code})


class HealthCheckSerializer(serializers.Serializer):
    """Ответ health-check."""

    status = serializers.CharField(help_text='Статус сервиса, ожидается "ok".')


class VersionInfoSerializer(serializers.Serializer):
    """Ответ с метаданными версии приложения."""

    app_name = serializers.CharField()
    version = serializers.CharField()
    framework = serializers.CharField()


@extend_schema(
    summary='Проверка работоспособности',
    responses={200: HealthCheckSerializer},
)
@api_view(['GET'])
def health_check(request):
    """
    Проверка работоспособности сервиса.

    Returns:
        Response: JSON ``{"status": "ok"}`` при успешной проверке.
    """
    logger.info('Health check requested')
    return Response({'status': 'ok'})


@extend_schema(
    summary='Версия приложения',
    responses={200: VersionInfoSerializer},
)
@api_view(['GET'])
def get_version(request):
    """
    Получить информацию о версии приложения.

    Returns:
        Response: Название приложения, версия и фреймворк.
    """
    return Response({
        'app_name': 'Quiz Service',
        'version': '0.1.0',
        'framework': 'Django 4.2',
    })


class QuizViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления викторинами.

    list: GET /api/v1/quizzes/ - список всех квизов
    retrieve: GET /api/v1/quizzes/{id}/ - детальная информация
    create: POST /api/v1/quizzes/ - создание квиза
    update: PUT /api/v1/quizzes/{id}/ - обновление квиза
    destroy: DELETE /api/v1/quizzes/{id}/ - удаление квиза
    """

    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsQuizOwnerOrReadOnly]

    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['is_active']

    def get_serializer_class(self):
        """POST/PUT/PATCH используют сериализатор с вложенными вопросами."""
        if self.action in ('create', 'update', 'partial_update'):
            return QuizWriteSerializer
        return QuizSerializer

    def perform_create(self, serializer):
        """Сохраняет викторину с текущим пользователем как создателем."""
        serializer.save(created_by=self.request.user)
        logger.info('Quiz created by user: %s', self.request.user.username)

    @action(detail=True, methods=['post'])
    def start_session(self, request, pk=None):
        """
        POST: запуск новой сессии для выбранной викторины.

        Создаёт ``QuizSession`` с уникальным ``session_code``.
        """
        quiz = self.get_object()

        for _ in range(5):
            try:
                session = QuizSession.objects.create(
                    quiz=quiz,
                    session_code=SessionCodeFactory.create(),
                )
                logger.info('Session started for quiz: %s', quiz.title)
                return Response(QuizSessionSerializer(session).data)
            except IntegrityError:
                logger.warning('Session code collision, retrying...')

        return Response(
            {'error': 'Could not generate unique session code'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class QuizSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления сессиями квизов.

    join: POST /api/v1/sessions/{id}/join/ – присоединиться к сессии
    """
    queryset = QuizSession.objects.all().prefetch_related('participants')
    serializer_class = QuizSessionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_active', 'quiz']
    search_fields = ['session_code']

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """
        POST: присоединение участника к сессии.

        Тело запроса: ``{"name": "<имя>"}``.
        """
        session = self.get_object()

        if not session.is_active:
            return Response(
                {'error': 'Session is closed'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            participant = Participant.objects.create(
                session=session,
                name=request.data['name'],
            )
        except IntegrityError:
            return Response(
                {'error': 'Participant name must be unique in this session'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        logger.info(
            "Participant '%s' joined session: %s",
            participant.name,
            session.session_code,
        )

        return Response(ParticipantSerializer(participant).data)


class ExportSessionResultsView(APIView):
    """Экспорт результатов сессии в CSV."""

    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        """Возвращает CSV-файл с результатами участников."""
        session = get_object_or_404(QuizSession, id=session_id)
        csv_content = generate_session_csv(session)

        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = (
            f'attachment; filename="results_{session.session_code}.csv"'
        )

        logger.info(
            'Export CSV: session %s by user %s',
            session_id,
            request.user.id,
        )
        return response


class QuizStatisticsView(APIView):
    """Статистика ответов по вопросам викторины."""

    def get(self, request, quiz_id):
        """Возвращает агрегированную статистику с пагинацией."""
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        cache_key = f'quiz_stats_{quiz_id}_{page}_{page_size}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        stats = get_quiz_statistics(quiz_id)

        start = (page - 1) * page_size
        end = start + page_size
        paginated_stats = stats[start:end]

        response = {
            'quiz_id': quiz_id,
            'total_questions': len(stats),
            'page': page,
            'page_size': page_size,
            'results': paginated_stats,
        }

        cache.set(cache_key, response, timeout=300)

        return Response(response)

class SessionResultsView(ListAPIView):
    serializer_class = SessionResultSerializer
    pagination_class = ResultsPagination

    def get_queryset(self):
        session_id = self.kwargs["id"]

        queryset = (
            SessionParticipant.objects
            .filter(session_id=session_id)
            .prefetch_related("answers")
            .order_by("-total_score")
        )

        if not queryset.exists():
            raise NotFound("Сессия не найдена или пуста")

        status_filter = self.request.query_params.get("status")

        if status_filter == "finished":
            queryset = queryset.filter(is_finished=True)

        elif status_filter == "unfinished":
            queryset = queryset.filter(is_finished=False)

        return queryset