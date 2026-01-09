from django.urls import path

from .views import (
    InvoiceDiscountCreateAPIView,
    InvoiceDiscountDestroyAPIView,
    InvoiceFinalizeAPIView,
    InvoiceLineCreateAPIView,
    InvoiceLineDiscountCreateAPIView,
    InvoiceLineDiscountDestroyAPIView,
    InvoiceLineTaxCreateAPIView,
    InvoiceLineTaxDestroyAPIView,
    InvoiceLineUpdateDestroyAPIView,
    InvoiceListCreateAPIView,
    InvoicePreviewAPIView,
    InvoiceRetrieveUpdateDestroyAPIView,
    InvoiceRevisionsListCreateAPIView,
    InvoiceTaxCreateAPIView,
    InvoiceTaxDestroyAPIView,
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
    # Lines
    path("invoice-lines", InvoiceLineCreateAPIView.as_view()),
    path("invoice-lines/<uuid:pk>", InvoiceLineUpdateDestroyAPIView.as_view()),
    # Discounts
    path("invoice-lines/<uuid:pk>/discounts", InvoiceLineDiscountCreateAPIView.as_view()),
    path("invoice-lines/<uuid:invoice_line_id>/discounts/<uuid:pk>", InvoiceLineDiscountDestroyAPIView.as_view()),
    path("invoices/<uuid:pk>/discounts", InvoiceDiscountCreateAPIView.as_view()),
    path("invoices/<uuid:invoice_id>/discounts/<uuid:pk>", InvoiceDiscountDestroyAPIView.as_view()),
    # Taxes
    path("invoice-lines/<uuid:pk>/taxes", InvoiceLineTaxCreateAPIView.as_view()),
    path("invoice-lines/<uuid:invoice_line_id>/taxes/<uuid:pk>", InvoiceLineTaxDestroyAPIView.as_view()),
    path("invoices/<uuid:pk>/taxes", InvoiceTaxCreateAPIView.as_view()),
    path("invoices/<uuid:invoice_id>/taxes/<uuid:pk>", InvoiceTaxDestroyAPIView.as_view()),
]
