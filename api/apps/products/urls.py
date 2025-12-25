from django.urls import path

from .views import (
    ProductArchiveAPIView,
    ProductListCreateAPIView,
    ProductRetrieveUpdateDestroyAPIView,
    ProductUnarchiveAPIView,
)

urlpatterns = [
    path("products", ProductListCreateAPIView.as_view()),
    path("products/<uuid:pk>", ProductRetrieveUpdateDestroyAPIView.as_view()),
    path("products/<uuid:pk>/archive", ProductArchiveAPIView.as_view()),
    path("products/<uuid:pk>/unarchive", ProductUnarchiveAPIView.as_view()),
]
