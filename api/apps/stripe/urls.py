from django.urls import path

from . import views

urlpatterns = [
    path("stripe/checkout", views.StripeCheckoutAPIView.as_view()),
    path("stripe/billing-portal", views.StripeBillingPortalAPIView.as_view()),
    path("stripe/webhook", views.StripeWebhookAPIView.as_view()),
]
