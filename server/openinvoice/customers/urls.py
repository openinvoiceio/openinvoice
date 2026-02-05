from django.urls import path

from .views import (
    BillingProfileListCreateAPIView,
    BillingProfileRetrieveUpdateDestroyAPIView,
    BillingProfileTaxIdCreateAPIView,
    BillingProfileTaxIdDestroyAPIView,
    CustomerListCreateAPIView,
    CustomerRetrieveUpdateDestroyAPIView,
    ShippingProfileListCreateAPIView,
    ShippingProfileRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path("customers", CustomerListCreateAPIView.as_view()),
    path("customers/<uuid:pk>", CustomerRetrieveUpdateDestroyAPIView.as_view()),
    path("billing-profiles", BillingProfileListCreateAPIView.as_view()),
    path("billing-profiles/<uuid:pk>", BillingProfileRetrieveUpdateDestroyAPIView.as_view()),
    path("billing-profiles/<uuid:pk>/tax-ids", BillingProfileTaxIdCreateAPIView.as_view()),
    path(
        "billing-profiles/<uuid:billing_profile_id>/tax-ids/<uuid:pk>",
        BillingProfileTaxIdDestroyAPIView.as_view(),
    ),
    path("shipping-profiles", ShippingProfileListCreateAPIView.as_view()),
    path("shipping-profiles/<uuid:pk>", ShippingProfileRetrieveUpdateDestroyAPIView.as_view()),
]
