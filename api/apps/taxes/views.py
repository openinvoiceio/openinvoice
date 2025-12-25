import structlog
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember

from .filters import TaxRateFilter
from .models import TaxRate
from .permissions import MaxTaxRatesLimit
from .serializers import TaxRateCreateSerializer, TaxRateSerializer, TaxRateUpdateSerializer

logger = structlog.get_logger(__name__)


@extend_schema_view(list=extend_schema(operation_id="list_tax_rates"))
class TaxRateListCreateAPIView(generics.ListAPIView):
    queryset = TaxRate.objects.none()
    serializer_class = TaxRateSerializer
    filterset_class = TaxRateFilter
    search_fields = ["name", "description"]
    ordering_fields = ["created_at"]
    permission_classes = [IsAuthenticated, IsAccountMember, MaxTaxRatesLimit]

    def get_queryset(self):
        return TaxRate.objects.for_account(self.request.account.id)

    @extend_schema(operation_id="create_tax_rate", request=TaxRateCreateSerializer, responses={201: TaxRateSerializer})
    def post(self, request):
        serializer = TaxRateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        tax_rate = TaxRate.objects.create_tax_rate(
            account=request.account,
            name=data["name"],
            description=data.get("description"),
            percentage=data["percentage"],
            country=data.get("country"),
        )

        logger.info(
            "Tax rate created",
            account_id=request.account.id,
            tax_rate_id=tax_rate.id,
        )

        serializer = TaxRateSerializer(tax_rate)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_tax_rate"))
class TaxRateRetrieveUpdateAPIView(generics.RetrieveAPIView):
    queryset = TaxRate.objects.none()
    serializer_class = TaxRateSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return TaxRate.objects.for_account(self.request.account.id)

    @extend_schema(operation_id="update_tax_rate", request=TaxRateUpdateSerializer, responses={200: TaxRateSerializer})
    def put(self, request, **_):
        tax_rate = self.get_object()
        serializer = TaxRateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        tax_rate.update(
            name=data.get("name", tax_rate.name),
            description=data.get("description", tax_rate.description),
            country=data.get("country", tax_rate.country),
        )

        logger.info(
            "Tax rate updated",
            account_id=request.account.id,
            tax_rate_id=tax_rate.id,
        )

        serializer = TaxRateSerializer(tax_rate)
        return Response(serializer.data)


class TaxRateArchiveAPIView(generics.GenericAPIView):
    queryset = TaxRate.objects.none()
    serializer_class = TaxRateSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return TaxRate.objects.for_account(self.request.account.id)

    @extend_schema(operation_id="archive_tax_rate", request=None, responses={200: TaxRateSerializer})
    def post(self, request, *_, **__):
        tax_rate = self.get_object()

        tax_rate.archive()

        logger.info(
            "Tax rate archived",
            account_id=request.account.id,
            tax_rate_id=tax_rate.id,
        )

        serializer = TaxRateSerializer(tax_rate)
        return Response(serializer.data)


class TaxRateUnarchiveAPIView(generics.GenericAPIView):
    queryset = TaxRate.objects.none()
    serializer_class = TaxRateSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return TaxRate.objects.for_account(self.request.account.id)

    @extend_schema(operation_id="unarchive_tax_rate", request=None, responses={200: TaxRateSerializer})
    def post(self, request, *_, **__):
        tax_rate = self.get_object()

        tax_rate.unarchive()

        logger.info(
            "Tax rate unarchived",
            account_id=request.account.id,
            tax_rate_id=tax_rate.id,
        )

        serializer = TaxRateSerializer(tax_rate)
        return Response(serializer.data)
