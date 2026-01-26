from django.urls import path

from .views import (
    ShippingRateArchiveAPIView,
    ShippingRateListCreateAPIView,
    ShippingRateRestoreAPIView,
    ShippingRateRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path("shipping-rates", ShippingRateListCreateAPIView.as_view()),
    path("shipping-rates/<uuid:pk>", ShippingRateRetrieveUpdateDestroyAPIView.as_view()),
    path("shipping-rates/<uuid:pk>/archive", ShippingRateArchiveAPIView.as_view()),
    path("shipping-rates/<uuid:pk>/restore", ShippingRateRestoreAPIView.as_view()),
]
