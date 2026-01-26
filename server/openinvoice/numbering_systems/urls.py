from django.urls import path

from .views import (
    NumberingSystemArchiveAPIView,
    NumberingSystemListCreateAPIView,
    NumberingSystemRestoreAPIView,
    NumberingSystemRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path("numbering-systems", NumberingSystemListCreateAPIView.as_view()),
    path("numbering-systems/<uuid:pk>", NumberingSystemRetrieveUpdateDestroyAPIView.as_view()),
    path("numbering-systems/<uuid:pk>/archive", NumberingSystemArchiveAPIView.as_view()),
    path("numbering-systems/<uuid:pk>/restore", NumberingSystemRestoreAPIView.as_view()),
]
