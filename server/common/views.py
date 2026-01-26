from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from openinvoice.accounts.permissions import IsAccountMember

from .access import resolve_plan
from .serializers import ConfigSerializer


class ConfigAPIView(generics.GenericAPIView):
    serializer_class = ConfigSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    @extend_schema(
        operation_id="get_config",
        responses=ConfigSerializer,
    )
    def get(self, request):
        serializer = self.get_serializer(
            {
                "is_billing_enabled": hasattr(settings, "STRIPE_API_KEY"),
                "current_plan_code": resolve_plan(request.account),
                "plans": [
                    {
                        "name": plan["name"],
                        "code": plan_code,
                        "features": [
                            {"code": code, "is_enabled": is_enabled} for code, is_enabled in plan["features"].items()
                        ],
                        "limits": [{"code": code, "limit": limit} for code, limit in plan["limits"].items()],
                        "price_id": plan.get("price_id"),
                    }
                    for plan_code, plan in settings.PLANS.items()
                ],
            }
        )
        return Response(serializer.data)
