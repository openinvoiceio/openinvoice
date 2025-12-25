from django.urls import path

from .views import NumberingSystemListCreateAPIView, NumberingSystemRetrieveUpdateDestroyAPIView

urlpatterns = [
    path("numbering-systems", NumberingSystemListCreateAPIView.as_view()),
    path("numbering-systems/<uuid:pk>", NumberingSystemRetrieveUpdateDestroyAPIView.as_view()),
]
