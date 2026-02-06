from django.urls import path

from .views import (
    BillingProfileListCreateAPIView,
    BillingProfileRetrieveUpdateDestroyAPIView,
    CustomerListCreateAPIView,
    CustomerRetrieveUpdateDestroyAPIView,
    CustomerTaxIdCreateAPIView,
    CustomerTaxIdDestroyAPIView,
    ShippingProfileListCreateAPIView,
    ShippingProfileRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path("customers", CustomerListCreateAPIView.as_view()),
    path("customers/<uuid:pk>", CustomerRetrieveUpdateDestroyAPIView.as_view()),
    path("customers/<uuid:customer_id>/tax-ids", CustomerTaxIdCreateAPIView.as_view()),
    path(
        "customers/<uuid:customer_id>/tax-ids/<uuid:pk>",
        CustomerTaxIdDestroyAPIView.as_view(),
    ),
    path("billing-profiles", BillingProfileListCreateAPIView.as_view()),
    path("billing-profiles/<uuid:pk>", BillingProfileRetrieveUpdateDestroyAPIView.as_view()),
    path("shipping-profiles", ShippingProfileListCreateAPIView.as_view()),
    path("shipping-profiles/<uuid:pk>", ShippingProfileRetrieveUpdateDestroyAPIView.as_view()),
]
