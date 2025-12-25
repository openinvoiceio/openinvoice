from django.urls import path

from .views import (
    PriceArchiveAPIView,
    PriceListCreateAPIView,
    PriceRetrieveUpdateDestroyAPIView,
    PriceUnarchiveAPIView,
)

urlpatterns = [
    path("prices", PriceListCreateAPIView.as_view()),
    path("prices/<uuid:pk>", PriceRetrieveUpdateDestroyAPIView.as_view()),
    path("prices/<uuid:pk>/archive", PriceArchiveAPIView.as_view()),
    path("prices/<uuid:pk>/unarchive", PriceUnarchiveAPIView.as_view()),
]
