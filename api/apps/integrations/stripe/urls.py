from django.urls import path

from .views import (
    StripeConnectionOAuthCallback,
    StripeConnectionRetrieveUpdateDestroyAPIView,
    StripeWebhookAPIView,
)

urlpatterns = [
    path("integrations/stripe", StripeConnectionRetrieveUpdateDestroyAPIView.as_view()),
    path("integrations/stripe/webhook", StripeWebhookAPIView.as_view()),
    path("integrations/stripe/oauth/callback", StripeConnectionOAuthCallback.as_view()),
]
