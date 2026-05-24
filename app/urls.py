"""Маршруты приложения (страницы и REST API)."""
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import SessionResultsView

from .auth_views import CustomLoginView, register_view
from .views import (
    ExportSessionResultsView,
    QuizSessionViewSet,
    QuizStatisticsView,
    QuizViewSet,
    get_version,
    health_check,
    index,
    quiz_create,
    quiz_edit,
    quiz_join,
    quiz_play,
)

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet, basename='quiz')
router.register(r'sessions', QuizSessionViewSet, basename='quizsession')

urlpatterns = [
    path('', index, name='index'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', register_view, name='register'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('create/', quiz_create, name='quiz_create'),
    path('quiz/<int:quiz_id>/edit/', quiz_edit, name='quiz_edit'),
    path('join/', quiz_join, name='quiz_join'),
    path('quiz/play/<str:session_code>/', quiz_play, name='quiz_play'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', register_view, name='register'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('health/', health_check, name='health_check'),
    path('version/', get_version, name='get_version'),
    path('', include(router.urls)),
    path(
        'quizzes/<int:quiz_id>/statistics/',
        QuizStatisticsView.as_view(),
        name='quiz-statistics',
    ),
    path(
        'sessions/<int:session_id>/export/',
        ExportSessionResultsView.as_view(),
        name='session-export',
    ),
     path("api/v1/sessions/<int:id>/results/", SessionResultsView.as_view(), name="session-results",
    ),
]
