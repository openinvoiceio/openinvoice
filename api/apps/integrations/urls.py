from django.urls import include, path

from .views import IntegrationsListAPIView

urlpatterns = [
    path("integrations", IntegrationsListAPIView.as_view()),
    path("", include("apps.integrations.stripe.urls")),
]
