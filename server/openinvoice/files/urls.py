from django.urls import path

from .views import FileListCreateAPIView, FileRetrieveAPIView

urlpatterns = [
    path("files", FileListCreateAPIView.as_view()),
    path("files/<uuid:pk>", FileRetrieveAPIView.as_view()),
]
