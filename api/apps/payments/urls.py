from django.urls import path

from .views import PaymentListCreateAPIView, PaymentRetrieveAPIView

urlpatterns = [
    path("payments", PaymentListCreateAPIView.as_view()),
    path("payments/<uuid:pk>", PaymentRetrieveAPIView.as_view()),
]
