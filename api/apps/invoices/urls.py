from django.urls import path

from .views import (
    InvoiceCloneAPIView,
    InvoiceFinalizeAPIView,
    InvoiceLineCreateAPIView,
    InvoiceLineUpdateDestroyAPIView,
    InvoiceListCreateAPIView,
    InvoicePreviewAPIView,
    InvoiceRetrieveUpdateDestroyAPIView,
    InvoiceRevisionsListCreateAPIView,
    InvoiceVoidAPIView,
)

urlpatterns = [
    # Invoices
    path("invoices", InvoiceListCreateAPIView.as_view()),
    path("invoices/<uuid:pk>", InvoiceRetrieveUpdateDestroyAPIView.as_view()),
    path("invoices/<uuid:pk>/revisions", InvoiceRevisionsListCreateAPIView.as_view()),
    path("invoices/<uuid:pk>/finalize", InvoiceFinalizeAPIView.as_view()),
    path("invoices/<uuid:pk>/void", InvoiceVoidAPIView.as_view()),
    path("invoices/<uuid:pk>/preview", InvoicePreviewAPIView.as_view()),
    path("invoices/<uuid:pk>/clone", InvoiceCloneAPIView.as_view()),
    # Lines
    path("invoice-lines", InvoiceLineCreateAPIView.as_view()),
    path("invoice-lines/<uuid:pk>", InvoiceLineUpdateDestroyAPIView.as_view()),
]
