from django.urls import path

from .views import (
    ProfileRetrieveUpdateAPIView,
)

urlpatterns = [
    path("profile", ProfileRetrieveUpdateAPIView.as_view()),
]
