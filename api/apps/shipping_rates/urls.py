from django.urls import path

from .views import (
    ShippingRateArchiveAPIView,
    ShippingRateListCreateAPIView,
    ShippingRateRetrieveUpdateDestroyAPIView,
    ShippingRateUnarchiveAPIView,
)

urlpatterns = [
    path("shipping-rates", ShippingRateListCreateAPIView.as_view()),
    path("shipping-rates/<uuid:pk>", ShippingRateRetrieveUpdateDestroyAPIView.as_view()),
    path("shipping-rates/<uuid:pk>/archive", ShippingRateArchiveAPIView.as_view()),
    path("shipping-rates/<uuid:pk>/unarchive", ShippingRateUnarchiveAPIView.as_view()),
]
