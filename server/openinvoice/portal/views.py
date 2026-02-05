import structlog
from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from openinvoice.accounts.permissions import IsAccountMember
from openinvoice.customers.models import ShippingProfile
from openinvoice.invoices.choices import InvoiceStatus
from openinvoice.invoices.models import Invoice

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
            name=data.get("name", customer.default_billing_profile.name),
            email=data.get("email", customer.default_billing_profile.email),
            phone=data.get("phone", customer.default_billing_profile.phone),
            legal_name=data.get("legal_name", customer.default_billing_profile.legal_name),
            legal_number=data.get("legal_number", customer.default_billing_profile.legal_number),
            address_data=data.get("address"),
        )

        if "shipping" in data:
            if data["shipping"] is None:
                if customer.default_shipping_profile:
                    shipping_profile = customer.default_shipping_profile
                    customer.default_shipping_profile = None
                    customer.save(update_fields=["default_shipping_profile"])
                    customer.shipping_profiles.remove(shipping_profile)
            elif customer.default_shipping_profile:
                shipping_profile = customer.default_shipping_profile
                shipping_data = data["shipping"] or {}
                customer.default_shipping_profile.update(
                    name=shipping_data.get("name", shipping_profile.name),
                    phone=shipping_data.get("phone", shipping_profile.phone),
                    address_data=shipping_data.get("address"),
                )
            else:
                shipping_data = data.get("shipping") or {}
                shipping_profile = ShippingProfile.objects.create_profile(
                    name=shipping_data.get("name"),
                    phone=shipping_data.get("phone"),
                    address_data=shipping_data.get("address"),
                )
                customer.default_shipping_profile = shipping_profile
                customer.shipping_profiles.add(shipping_profile)
                customer.save(update_fields=["default_shipping_profile"])

        logger.info(
            "Portal customer profile updated",
            customer_id=str(customer.id),
            account_id=str(customer.account_id),
        )

        serializer = PortalCustomerSerializer(customer)
        return Response(serializer.data)
