
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.documentation import include_docs_urls
from app.views import ArticleViewSet, CommentViewSet  # заменить your_app
from .views import ExportSessionResultsView

router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('api/docs/', include_docs_urls(title='API Documentation')),
    path('api/v1/sessions/<int:session_id>/export/csv/', ExportSessionResultsView.as_view(), name='export-csv')

]

