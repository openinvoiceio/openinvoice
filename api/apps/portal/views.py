import structlog
from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember
from apps.invoices.choices import InvoiceStatus
from apps.invoices.models import Invoice

from .authentication import PortalAuthentication
from .crypto import sign_portal_token
from .serializers import (
    PortalCustomerSerializer,
    PortalCustomerUpdateSerializer,
    PortalInvoiceSerializer,
    PortalSessionCreateSerializer,
    PortalSessionSerializer,
)

logger = structlog.get_logger(__name__)


class PortalSessionCreateAPIView(generics.GenericAPIView):
    serializer_class = PortalSessionCreateSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    @extend_schema(
        operation_id="create_portal_session",
        request=PortalSessionCreateSerializer,
        responses={200: PortalSessionSerializer},
    )
    def post(self, request, *_args, **_kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = sign_portal_token(customer=serializer.validated_data["customer"])
        portal_url = f"{settings.BASE_URL}/customer-portal/{token}"

        serializer = PortalSessionSerializer({"portal_url": portal_url})
        return Response(serializer.data)


@extend_schema_view(list=extend_schema(operation_id="list_portal_invoices"))
class PortalInvoiceListAPIView(generics.ListAPIView):
    queryset = Invoice.objects.none()
    serializer_class = PortalInvoiceSerializer
    permission_classes = [AllowAny]
    authentication_classes = [PortalAuthentication]

    def get_queryset(self):
        return Invoice.objects.filter(
            customer_id=self.request.customer.id,
            status__in=[InvoiceStatus.OPEN, InvoiceStatus.PAID],
        )


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_portal_customer"))
class PortalCustomerAPIView(generics.RetrieveAPIView):
    serializer_class = PortalCustomerSerializer
    permission_classes = [AllowAny]
    authentication_classes = [PortalAuthentication]

    def get_object(self):
        return self.request.customer

    @extend_schema(
        operation_id="update_portal_customer",
        request=PortalCustomerUpdateSerializer,
        responses=PortalCustomerSerializer,
    )
    def put(self, request, *_, **__):
        customer = self.get_object()
        serializer = PortalCustomerUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        customer.update_portal_profile(
            name=data.get("name", customer.name),
            email=data.get("email", customer.email),
            phone=data.get("phone", customer.phone),
            legal_name=data.get("legal_name", customer.legal_name),
            legal_number=data.get("legal_number", customer.legal_number),
        )
        customer.address.update(**data.get("address") or {})

        if "shipping" in data:
            if data["shipping"] is None:
                if customer.shipping:
                    customer.shipping.delete()
            elif customer.shipping:
                customer.shipping.update(
                    name=data["shipping"].get("name", customer.shipping.name),
                    phone=data["shipping"].get("phone", customer.shipping.phone),
                    address_data=data["shipping"].get("address", {}),
                )
            else:
                customer.add_shipping(
                    name=data["shipping"].get("name"),
                    phone=data["shipping"].get("phone"),
                    address_data=data["shipping"].get("address"),
                )

        logger.info(
            "Portal customer profile updated",
            customer_id=str(customer.id),
            account_id=str(customer.account_id),
        )

        serializer = PortalCustomerSerializer(customer)
        return Response(serializer.data)
