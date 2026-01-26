from django.urls import path

from .views import (
    ProductArchiveAPIView,
    ProductListCreateAPIView,
    ProductRestoreAPIView,
    ProductRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path("products", ProductListCreateAPIView.as_view()),
    path("products/<uuid:pk>", ProductRetrieveUpdateDestroyAPIView.as_view()),
    path("products/<uuid:pk>/archive", ProductArchiveAPIView.as_view()),
    path("products/<uuid:pk>/restore", ProductRestoreAPIView.as_view()),
]
