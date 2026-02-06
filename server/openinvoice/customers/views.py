import structlog
from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from openinvoice.accounts.permissions import IsAccountMember
from openinvoice.tax_ids.models import TaxId
from openinvoice.tax_ids.serializers import TaxIdCreateSerializer, TaxIdSerializer

from .filtersets import BillingProfileFilterSet, CustomerFilterSet, ShippingProfileFilterSet
from .models import BillingProfile, Customer, ShippingProfile
from .permissions import MaxCustomersLimit
from .serializers import (
    BillingProfileCreateSerializer,
    BillingProfileSerializer,
    BillingProfileUpdateSerializer,
    CustomerCreateSerializer,
    CustomerSerializer,
    CustomerUpdateSerializer,
    ShippingProfileCreateSerializer,
    ShippingProfileSerializer,
    ShippingProfileUpdateSerializer,
)

logger = structlog.get_logger(__name__)


@extend_schema_view(list=extend_schema(operation_id="list_customers"))
class CustomerListCreateAPIView(generics.ListAPIView):
    queryset = Customer.objects.none()
    serializer_class = CustomerSerializer
    filterset_class = CustomerFilterSet
    search_fields = [
        "name",
        "default_billing_profile__email",
        "default_billing_profile__phone",
        "description",
    ]
    ordering_fields = ["created_at"]
    permission_classes = [IsAuthenticated, IsAccountMember, MaxCustomersLimit]

    def get_queryset(self):
        return Customer.objects.for_account(self.request.account).eager_load()

    @extend_schema(
        operation_id="create_customer",
        request=CustomerCreateSerializer,
        responses={201: CustomerSerializer},
    )
    def post(self, request):
        serializer = CustomerCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        billing_data = data.get("billing_profile") or {}

        billing_profile = BillingProfile.objects.create_profile(
            legal_name=billing_data.get("legal_name", data["name"]),
            legal_number=billing_data.get("legal_number"),
            email=billing_data.get("email"),
            phone=billing_data.get("phone"),
            address_data=billing_data.get("address"),
            currency=billing_data.get("currency"),
            language=billing_data.get("language"),
            net_payment_term=billing_data.get("net_payment_term"),
            invoice_numbering_system=billing_data.get("invoice_numbering_system"),
            credit_note_numbering_system=billing_data.get("credit_note_numbering_system"),
        )
        billing_profile.tax_rates.set(billing_data.get("tax_rates", []))

        shipping_profile = None
        if "shipping_profile" in data:
            shipping_data = data.get("shipping_profile") or {}
            shipping_profile = ShippingProfile.objects.create_profile(
                name=shipping_data.get("name"),
                phone=shipping_data.get("phone"),
                address_data=shipping_data.get("address"),
            )

        customer = Customer.objects.create_customer(
            account=request.account,
            name=data["name"],
            description=data.get("description"),
            metadata=data.get("metadata"),
            logo=data.get("logo"),
            default_billing_profile=billing_profile,
            default_shipping_profile=shipping_profile,
        )
        customer.billing_profiles.add(billing_profile)
        if shipping_profile:
            customer.shipping_profiles.add(shipping_profile)

        logger.info(
            "Customer created",
            customer_id=customer.id,
            created_by=request.user.id,
        )

        serializer = self.get_serializer(customer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_customer"))
class CustomerRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = Customer.objects.none()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Customer.objects.for_account(self.request.account).eager_load()

    @extend_schema(
        operation_id="update_customer",
        request=CustomerUpdateSerializer,
        responses={200: CustomerSerializer},
    )
    def put(self, request, **_):
        customer = self.get_object()
        serializer = CustomerUpdateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        customer.update(
            name=data.get("name", customer.name),
            description=data.get("description", customer.description),
            metadata=data.get("metadata", customer.metadata),
            logo=data.get("logo", customer.logo),
            default_billing_profile=data.get("default_billing_profile", customer.default_billing_profile),
            default_shipping_profile=data.get("default_shipping_profile", customer.default_shipping_profile),
        )
        logger.info("Customer updated", account_id=request.account.id, customer_id=customer.id)

        serializer = self.get_serializer(customer)
        return Response(serializer.data)

    @extend_schema(
        operation_id="delete_customer",
        request=None,
        responses={204: None},
    )
    def delete(self, _, pk, **__):
        customer = self.get_object()

        if customer.invoices.exists():
            raise ValidationError("Customer with invoices cannot be deleted")

        customer.delete()

        logger.info("Customer deleted", account_id=self.request.account.id, customer_id=pk)

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(list=extend_schema(operation_id="list_billing_profiles"))
class BillingProfileListCreateAPIView(generics.ListAPIView):
    queryset = BillingProfile.objects.none()
    serializer_class = BillingProfileSerializer
    filterset_class = BillingProfileFilterSet
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return BillingProfile.objects.for_account(self.request.account).order_by("-created_at")

    @extend_schema(
        operation_id="create_billing_profile",
        request=BillingProfileCreateSerializer,
        responses={201: BillingProfileSerializer},
    )
    def post(self, request):
        serializer = BillingProfileCreateSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        customer = data["customer"]
        billing_profile = BillingProfile.objects.create_profile(
            legal_name=data.get("legal_name"),
            legal_number=data.get("legal_number"),
            email=data.get("email"),
            phone=data.get("phone"),
            address_data=data.get("address"),
            currency=data.get("currency"),
            language=data.get("language"),
            net_payment_term=data.get("net_payment_term"),
            invoice_numbering_system=data.get("invoice_numbering_system"),
            credit_note_numbering_system=data.get("credit_note_numbering_system"),
        )
        billing_profile.tax_rates.set(data.get("tax_rates", []))
        customer.billing_profiles.add(billing_profile)
        logger.info("Billing profile created", billing_profile_id=billing_profile.id)

        serializer = self.get_serializer(billing_profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_billing_profile"))
class BillingProfileRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = BillingProfile.objects.none()
    serializer_class = BillingProfileSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return BillingProfile.objects.for_account(self.request.account)

    @extend_schema(
        operation_id="update_billing_profile",
        request=BillingProfileUpdateSerializer,
        responses={200: BillingProfileSerializer},
    )
    def put(self, request, **_):
        profile = self.get_object()
        serializer = BillingProfileUpdateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        profile.update(
            legal_name=data.get("legal_name", profile.legal_name),
            legal_number=data.get("legal_number", profile.legal_number),
            email=data.get("email", profile.email),
            phone=data.get("phone", profile.phone),
            currency=data.get("currency", profile.currency),
            language=data.get("language", profile.language),
            net_payment_term=data.get("net_payment_term", profile.net_payment_term),
            invoice_numbering_system=data.get("invoice_numbering_system", profile.invoice_numbering_system),
            credit_note_numbering_system=data.get("credit_note_numbering_system", profile.credit_note_numbering_system),
            address_data=data.get("address"),
        )
        if "tax_rates" in data:
            profile.tax_rates.set(data["tax_rates"])
        logger.info("Billing profile updated", billing_profile_id=profile.id)

        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @extend_schema(operation_id="delete_billing_profile", request=None, responses={204: None})
    def delete(self, _request, pk):
        profile = self.get_object()

        if Customer.objects.filter(default_billing_profile=profile).exists():
            raise ValidationError("Default billing profiles cannot be deleted")

        profile.delete()
        logger.info("Billing profile deleted", billing_profile_id=pk)

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(list=extend_schema(operation_id="list_shipping_profiles"))
class ShippingProfileListCreateAPIView(generics.ListAPIView):
    queryset = ShippingProfile.objects.none()
    serializer_class = ShippingProfileSerializer
    filterset_class = ShippingProfileFilterSet
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return ShippingProfile.objects.for_account(self.request.account).order_by("-created_at")

    @extend_schema(
        operation_id="create_shipping_profile",
        request=ShippingProfileCreateSerializer,
        responses={201: ShippingProfileSerializer},
    )
    def post(self, request):
        serializer = ShippingProfileCreateSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        customer = data["customer"]
        shipping_profile = ShippingProfile.objects.create_profile(
            name=data.get("name"),
            phone=data.get("phone"),
            address_data=data.get("address"),
        )
        customer.shipping_profiles.add(shipping_profile)
        logger.info("Shipping profile created", shipping_profile_id=shipping_profile.id)

        serializer = self.get_serializer(shipping_profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_shipping_profile"))
class ShippingProfileRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = ShippingProfile.objects.none()
    serializer_class = ShippingProfileSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return ShippingProfile.objects.for_account(self.request.account)

    @extend_schema(
        operation_id="update_shipping_profile",
        request=ShippingProfileUpdateSerializer,
        responses={200: ShippingProfileSerializer},
    )
    def put(self, request, **_):
        profile = self.get_object()
        serializer = ShippingProfileUpdateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        profile.update(
            name=data.get("name", profile.name),
            phone=data.get("phone", profile.phone),
            address_data=data.get("address"),
        )
        logger.info("Shipping profile updated", shipping_profile_id=profile.id)

        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @extend_schema(operation_id="delete_shipping_profile", request=None, responses={204: None})
    def delete(self, _request, pk):
        profile = self.get_object()

        if Customer.objects.filter(default_shipping_profile=profile).exists():
            raise ValidationError("Default shipping profiles cannot be deleted")

        profile.delete()
        logger.info("Shipping profile deleted", shipping_profile_id=pk)

        return Response(status=status.HTTP_204_NO_CONTENT)


class BillingProfileTaxIdCreateAPIView(generics.GenericAPIView):
    queryset = BillingProfile.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return BillingProfile.objects.for_account(self.request.account)

    @extend_schema(
        operation_id="create_billing_profile_tax_id",
        request=TaxIdCreateSerializer,
        responses={201: TaxIdSerializer},
    )
    def post(self, request, *_, **__):
        profile = self.get_object()
        serializer = TaxIdCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if profile.tax_ids.count() >= settings.MAX_TAX_IDS:
            raise ValidationError(f"You can add at most {settings.MAX_TAX_IDS} tax IDs to a billing profile.")

        tax_id = TaxId.objects.create_tax_id(
            type_=data["type"],
            number=data["number"],
            country=data.get("country"),
        )
        profile.tax_ids.add(tax_id)

        logger.info(
            "Billing profile tax ID created",
            account_id=request.account.id,
            billing_profile_id=profile.id,
            tax_id_id=tax_id.id,
        )

        serializer = TaxIdSerializer(tax_id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BillingProfileTaxIdDestroyAPIView(generics.GenericAPIView):
    queryset = TaxId.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return TaxId.objects.filter(
            billing_profiles__customers__account_id=self.request.account.id,
            billing_profiles__id=self.kwargs["billing_profile_id"],
        )

    @extend_schema(operation_id="delete_billing_profile_tax_id", request=None, responses={204: None})
    def delete(self, request, *_, **__):
        tax_id = self.get_object()

        tax_id.delete()

        logger.info(
            "Billing profile tax ID deleted",
            account_id=request.account.id,
            billing_profile_id=self.kwargs["billing_profile_id"],
            tax_id_id=tax_id.id,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
