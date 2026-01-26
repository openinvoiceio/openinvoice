from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openinvoice.accounts.permissions import IsAccountMember

from .base import get_integration
from .serializers import IntegrationSerializer


class IntegrationsListAPIView(APIView):
    serializer_class = IntegrationSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    @extend_schema(operation_id="list_integrations", responses={200: IntegrationSerializer(many=True)})
    def get(self, _):
        integrations = []
        for slug in settings.INTEGRATIONS:
            integration = get_integration(slug=slug)
            integrations.append(
                {
                    "name": integration.name,
                    "slug": integration.slug,
                    "description": integration.description,
                    "is_enabled": integration.is_enabled(self.request.account.id),
                }
            )

        serializer = IntegrationSerializer(integrations, many=True)
        return Response(serializer.data)
