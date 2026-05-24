"""Права доступа для REST API."""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsQuizOwnerOrReadOnly(BasePermission):
    """Изменение викторины доступно только создателю; чтение — всем."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return obj.created_by_id == request.user.id
