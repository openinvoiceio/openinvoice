from django.db.models import CharField, Model, Value
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember

from .enums import IntegrationType
from .models import StripeConnection
from .serializers import IntegrationConnectionSerializer


class IntegrationConnectionsListAPIView(generics.GenericAPIView):
    queryset = StripeConnection.objects.none()
    serializer_class = IntegrationConnectionSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, IsAccountMember]
    connections = [
        (StripeConnection, IntegrationType.STRIPE),
    ]

    def get_model_qs(self, model: Model, integration_type: IntegrationType):
        return (
            model.objects.filter(account_id=self.request.account.id)
            .annotate(type=Value(integration_type, output_field=CharField()))
            .values("id", "type", "created_at")
        )

    @extend_schema(
        operation_id="list_integration_connections", responses={200: IntegrationConnectionSerializer(many=True)}
    )
    def get(self, _):
        queryset = None
        for model, integration_type in self.connections:
            qs = self.get_model_qs(model, integration_type)
            queryset = qs if queryset is None else queryset.union(qs)

        serializer = self.get_serializer(queryset or [], many=True)
        return Response(serializer.data)
