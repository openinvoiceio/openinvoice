from django.urls import path

from .views import (
    PortalCustomerAPIView,
    PortalInvoiceListAPIView,
    PortalSessionCreateAPIView,
)

urlpatterns = [
    path("portal/sessions", PortalSessionCreateAPIView.as_view()),
    path("portal/invoices", PortalInvoiceListAPIView.as_view()),
    path("portal/customer", PortalCustomerAPIView.as_view()),
]
