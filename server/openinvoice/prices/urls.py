from django.urls import path

from .views import (
    PriceArchiveAPIView,
    PriceListCreateAPIView,
    PriceRestoreAPIView,
    PriceRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path("prices", PriceListCreateAPIView.as_view()),
    path("prices/<uuid:pk>", PriceRetrieveUpdateDestroyAPIView.as_view()),
    path("prices/<uuid:pk>/archive", PriceArchiveAPIView.as_view()),
    path("prices/<uuid:pk>/restore", PriceRestoreAPIView.as_view()),
]
