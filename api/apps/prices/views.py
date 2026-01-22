from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember

from .choices import PriceStatus
from .filtersets import PriceFilterSet
from .models import Price
from .serializers import PriceCreateSerializer, PriceSerializer, PriceUpdateSerializer


@extend_schema_view(list=extend_schema(operation_id="list_prices"))
class PriceListCreateAPIView(generics.ListAPIView):
    queryset = Price.objects.none()
    serializer_class = PriceSerializer
    filterset_class = PriceFilterSet
    search_fields = ["product__name", "code"]
    ordering_fields = ["created_at", "product_id"]
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Price.objects.for_account(self.request.account.id)

    @extend_schema(
        operation_id="create_price",
        request=PriceCreateSerializer,
        responses={201: PriceSerializer},
    )
    def post(self, request):
        serializer = PriceCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        price = Price.objects.create_price(
            amount=data.get("amount"),
            product=data["product"],
            currency=data["currency"],
            metadata=data.get("metadata"),
            code=data.get("code"),
            model=data.get("model"),
        )

        for tier in data.get("tiers", []):
            price.add_tier(
                unit_amount=tier["unit_amount"],
                from_value=tier["from_value"],
                to_value=tier.get("to_value"),
            )

        serializer = PriceSerializer(price)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_price"))
class PriceRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = Price.objects.none()
    serializer_class = PriceSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Price.objects.for_account(self.request.account.id)

    @extend_schema(
        operation_id="update_price",
        request=PriceUpdateSerializer,
        responses={200: PriceSerializer},
    )
    def put(self, request, **_):
        price = self.get_object()
        serializer = PriceUpdateSerializer(price, data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if price.status == PriceStatus.ARCHIVED:
            raise ValidationError("Archived prices cannot be updated")

        price.update(
            amount=data.get("amount", price.amount),
            currency=data.get("currency", price.currency),
            metadata=data.get("metadata", price.metadata),
            code=data.get("code", price.code),
        )

        if "tiers" in data:
            price.tiers.all().delete()
            for tier in data["tiers"]:
                price.add_tier(
                    unit_amount=tier["unit_amount"],
                    from_value=tier["from_value"],
                    to_value=tier.get("to_value"),
                )

        price.refresh_from_db()

        serializer = PriceSerializer(price)
        return Response(serializer.data)

    @extend_schema(operation_id="delete_price", request=None, responses={200: PriceSerializer})
    def delete(self, _, **__):
        price = self.get_object()

        if price.is_used:
            raise ValidationError("Used prices cannot be deleted")

        if price.product.default_price_id == price.id:
            raise ValidationError("Default prices cannot be deleted")

        price.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class PriceArchiveAPIView(generics.GenericAPIView):
    queryset = Price.objects.none()
    serializer_class = PriceSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Price.objects.for_account(self.request.account.id)

    @extend_schema(operation_id="archive_price", request=None, responses={200: PriceSerializer})
    def post(self, _, **__):
        price = self.get_object()

        price.archive()

        serializer = PriceSerializer(price)
        return Response(serializer.data)


class PriceRestoreAPIView(generics.GenericAPIView):
    queryset = Price.objects.none()
    serializer_class = PriceSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Price.objects.for_account(self.request.account.id)

    @extend_schema(operation_id="restore_price", request=None, responses={200: PriceSerializer})
    def post(self, _, **__):
        price = self.get_object()

        price.restore()

        serializer = PriceSerializer(price)
        return Response(serializer.data)
