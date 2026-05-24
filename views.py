
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import serializers
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient


class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='articles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField()
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.creator.username} on {self.article.title}"
    
class ArticleSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'creator', 'creator_name', 'created_at', 'updated_at']
        read_only_fields = ['creator', 'created_at', 'updated_at']


class CommentSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = Comment
        fields = ['id', 'article', 'content', 'creator', 'creator_name', 'created_at']
        read_only_fields = ['creator', 'created_at']


class IsCreatorOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True


        return obj.creator == request.user


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsCreatorOrReadOnly]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def my_articles(self, request):
        articles = Article.objects.filter(creator=request.user)
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsCreatorOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class ArticlePermissionsTest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )

        self.article = Article.objects.create(
            title='Test Article',
            content='Test content',
            creator=self.user1
        )
        self.articles_url = '/api/articles/'
        self.article_detail_url = f'/api/articles/{self.article.id}/'

    def test_anonymous_can_only_read(self):
        response = self.client.get(self.articles_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.article_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(self.articles_url, {
            'title': 'New Article',
            'content': 'New content'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


        response = self.client.put(self.article_detail_url, {
            'title': 'Updated Title',
            'content': 'Updated content'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.delete(self.article_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_can_create(self):

        self.client.force_authenticate(user=self.user1)

        response = self.client.post(self.articles_url, {
            'title': 'New Article',
            'content': 'New content'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Article.objects.last().creator, self.user1)

    def test_only_creator_can_edit_and_delete(self):

        self.client.force_authenticate(user=self.user1)
        response = self.client.put(self.article_detail_url, {
            'title': 'Updated Title',
            'content': 'Updated content'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(self.article_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        article2 = Article.objects.create(
            title='Test Article 2',
            content='Test content 2',
            creator=self.user1
        )

        self.client.force_authenticate(user=self.user2)

        article2_url = f'/api/articles/{article2.id}/'

        response = self.client.put(article2_url, {
            'title': 'Hacked Title',
            'content': 'Hacked content'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.delete(article2_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_view_all_articles(self):

        self.client.force_authenticate(user=self.user2)

        response = self.client.get(self.articles_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.article_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
