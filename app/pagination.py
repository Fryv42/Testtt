from rest_framework.pagination import PageNumberPagination


class ResultsPagination(PageNumberPagination):
    page_size = 20