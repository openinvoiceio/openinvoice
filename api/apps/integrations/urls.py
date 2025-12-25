from django.urls import include, path

from .views import IntegrationConnectionsListAPIView

urlpatterns = [
    path("integrations", IntegrationConnectionsListAPIView.as_view()),
    path("", include("apps.integrations.stripe.urls")),
]
