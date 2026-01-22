from django.urls import path

from .views import (
    TaxRateArchiveAPIView,
    TaxRateListCreateAPIView,
    TaxRateRestoreAPIView,
    TaxRateRetrieveUpdateAPIView,
)

urlpatterns = [
    path("tax-rates", TaxRateListCreateAPIView.as_view()),
    path("tax-rates/<uuid:pk>", TaxRateRetrieveUpdateAPIView.as_view()),
    path("tax-rates/<uuid:pk>/archive", TaxRateArchiveAPIView.as_view()),
    path("tax-rates/<uuid:pk>/restore", TaxRateRestoreAPIView.as_view()),
]
