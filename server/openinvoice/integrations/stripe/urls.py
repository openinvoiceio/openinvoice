from django.urls import path

from openinvoice.integrations.stripe.views import (
    StripeConnectionListCreateAPIView,
    StripeConnectionRetrieveUpdateDestroyAPIView,
    StripeWebhookAPIView,
)

urlpatterns = [
    path("integrations/stripe/connections", StripeConnectionListCreateAPIView.as_view()),
    path("integrations/stripe/connections/<uuid:pk>", StripeConnectionRetrieveUpdateDestroyAPIView.as_view()),
    path("integrations/stripe/connections/<uuid:pk>/webhook", StripeWebhookAPIView.as_view()),
]
