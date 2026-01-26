from django.urls import path

from .views import (
    CustomerListCreateAPIView,
    CustomerRetrieveUpdateDestroyAPIView,
    CustomerTaxIdCreateAPIView,
    CustomerTaxIdDestroyAPIView,
    CustomerTaxRateAssignAPIView,
    CustomerTaxRateDestroyAPIView,
)

urlpatterns = [
    path("customers", CustomerListCreateAPIView.as_view()),
    path("customers/<uuid:pk>", CustomerRetrieveUpdateDestroyAPIView.as_view()),
    path("customers/<uuid:pk>/tax-rates", CustomerTaxRateAssignAPIView.as_view()),
    path("customers/<uuid:pk>/tax-rates/<uuid:tax_rate_id>", CustomerTaxRateDestroyAPIView.as_view()),
    path("customers/<uuid:pk>/tax-ids", CustomerTaxIdCreateAPIView.as_view()),
    path("customers/<uuid:customer_id>/tax-ids/<uuid:pk>", CustomerTaxIdDestroyAPIView.as_view()),
]
