import structlog
from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from openinvoice.accounts.permissions import IsAccountMember
from openinvoice.addresses.models import Address
from openinvoice.tax_ids.models import TaxId
from openinvoice.tax_ids.serializers import TaxIdCreateSerializer, TaxIdSerializer

from .filtersets import CustomerFilterSet
from .models import Customer
from .permissions import MaxCustomersLimit
from .serializers import (
    CustomerCreateSerializer,
    CustomerSerializer,
    CustomerTaxRateAssignSerializer,
    CustomerUpdateSerializer,
)

logger = structlog.get_logger(__name__)


@extend_schema_view(list=extend_schema(operation_id="list_customers"))
class CustomerListCreateAPIView(generics.ListAPIView):
    queryset = Customer.objects.none()
    serializer_class = CustomerSerializer
    filterset_class = CustomerFilterSet
    search_fields = ["name", "email", "phone", "description"]
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

        address = Address.objects.create_address(**(data.get("address") or {}))
        customer = Customer.objects.create_customer(
            account=request.account,
            name=data["name"],
            legal_name=data.get("legal_name"),
            legal_number=data.get("legal_number"),
            email=data.get("email"),
            phone=data.get("phone"),
            description=data.get("description"),
            currency=data.get("currency"),
            net_payment_term=data.get("net_payment_term"),
            invoice_numbering_system=data.get("invoice_numbering_system"),
            credit_note_numbering_system=data.get("credit_note_numbering_system"),
            metadata=data.get("metadata"),
            address=address,
            logo=data.get("logo"),
        )

        if "shipping" in data:
            customer.add_shipping(
                name=data["shipping"].get("name"),
                phone=data["shipping"].get("phone"),
                address_data=data["shipping"].get("address"),
            )

        logger.info(
            "Customer created",
            account_id=request.account.id,
            customer_id=customer.id,
            created_by=request.user.id,
        )

        serializer = CustomerSerializer(customer)
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
            legal_name=data.get("legal_name", customer.legal_name),
            legal_number=data.get("legal_number", customer.legal_number),
            email=data.get("email", customer.email),
            phone=data.get("phone", customer.phone),
            description=data.get("description", customer.description),
            currency=data.get("currency", customer.currency),
            net_payment_term=data.get("net_payment_term", customer.net_payment_term),
            invoice_numbering_system=data.get("invoice_numbering_system", customer.invoice_numbering_system),
            credit_note_numbering_system=data.get(
                "credit_note_numbering_system", customer.credit_note_numbering_system
            ),
            metadata=data.get("metadata", customer.metadata),
            logo=data.get("logo", customer.logo),
        )

        customer.address.update(**data.get("address", {}))

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
                    address_data=data["shipping"].get("address", {}),
                )

        logger.info("Customer updated", account_id=request.account.id, customer_id=customer.id)

        serializer = CustomerSerializer(customer)
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


class CustomerTaxRateAssignAPIView(generics.GenericAPIView):
    queryset = Customer.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]
    serializer_class = CustomerTaxRateAssignSerializer

    def get_queryset(self):
        return Customer.objects.for_account(self.request.account).eager_load()

    @extend_schema(
        operation_id="assign_customer_tax_rate",
        request=CustomerTaxRateAssignSerializer,
        responses={200: CustomerSerializer},
    )
    def post(self, request, *_, **__):
        customer = self.get_object()
        serializer = CustomerTaxRateAssignSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        tax_rate = serializer.validated_data["tax_rate"]

        if customer.tax_rates.filter(id=tax_rate.id).exists():
            raise ValidationError("Tax rate already assigned")

        if customer.tax_rates.count() >= settings.CUSTOMER_TAX_RATES_LIMIT:
            raise ValidationError(f"At most {settings.CUSTOMER_TAX_RATES_LIMIT} tax rates are allowed")

        customer.tax_rates.add(tax_rate)
        customer.refresh_from_db()

        logger.info(
            "Customer tax rate assigned",
            account_id=customer.account_id,
            customer_id=customer.id,
            tax_rate_id=tax_rate.id,
        )

        serializer = CustomerSerializer(customer)
        return Response(serializer.data)


class CustomerTaxRateDestroyAPIView(generics.GenericAPIView):
    queryset = Customer.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Customer.objects.for_account(self.request.account).eager_load()

    @extend_schema(
        operation_id="remove_customer_tax_rate",
        responses={204: None},
    )
    def delete(self, *_, tax_rate_id, **__):
        customer = self.get_object()

        tax_rate = get_object_or_404(customer.tax_rates, id=tax_rate_id)
        customer.tax_rates.remove(tax_rate)
        customer.refresh_from_db()

        logger.info(
            "Customer tax rate removed",
            account_id=customer.account_id,
            customer_id=customer.id,
            tax_rate_id=tax_rate.id,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerTaxIdCreateAPIView(generics.GenericAPIView):
    queryset = Customer.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Customer.objects.for_account(self.request.account).eager_load()

    def get_customer(self):
        try:
            return self.get_queryset().get(id=self.kwargs["pk"])
        except Customer.DoesNotExist as e:
            raise NotFound from e

    @extend_schema(
        operation_id="create_customer_tax_id",
        request=TaxIdCreateSerializer,
        responses={201: TaxIdSerializer},
    )
    def post(self, request, *_, **__):
        customer = self.get_customer()
        serializer = TaxIdCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if customer.tax_ids.count() >= settings.MAX_TAX_IDS:
            raise ValidationError(f"You can add at most {settings.MAX_TAX_IDS} tax IDs to a customer.")

        tax_id = TaxId.objects.create_tax_id(
            type_=data["type"],
            number=data["number"],
            country=data.get("country"),
        )
        customer.tax_ids.add(tax_id)

        logger.info(
            "Customer tax ID created",
            account_id=customer.account_id,
            customer_id=customer.id,
            tax_id_id=tax_id.id,
        )

        serializer = TaxIdSerializer(tax_id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CustomerTaxIdDestroyAPIView(generics.GenericAPIView):
    queryset = Customer.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return TaxId.objects.filter(
            customers__account_id=self.request.account.id, customers__id=self.kwargs["customer_id"]
        )

    @extend_schema(operation_id="delete_customer_tax_id", request=None, responses={204: None})
    def delete(self, request, *_, **__):
        tax_id = self.get_object()

        tax_id.delete()

        logger.info(
            "Customer tax ID deleted",
            account_id=request.account.id,
            customer_id=self.kwargs["customer_id"],
            tax_id_id=tax_id.id,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
