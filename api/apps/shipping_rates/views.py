from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember

from .choices import ShippingRateStatus
from .filtersets import ShippingRateFilterSet
from .models import ShippingRate
from .permissions import MaxShippingRatesLimit
from .serializers import ShippingRateCreateSerializer, ShippingRateSerializer, ShippingRateUpdateSerializer


@extend_schema_view(list=extend_schema(operation_id="list_shipping_rates"))
class ShippingRateListCreateAPIView(generics.ListAPIView):
    queryset = ShippingRate.objects.none()
    serializer_class = ShippingRateSerializer
    filterset_class = ShippingRateFilterSet
    search_fields = ["name", "code"]
    ordering_fields = ["created_at"]
    permission_classes = [IsAuthenticated, IsAccountMember, MaxShippingRatesLimit]

    def get_queryset(self):
        return ShippingRate.objects.for_account(self.request.account)

    @extend_schema(
        operation_id="create_shipping_rate",
        request=ShippingRateCreateSerializer,
        responses={201: ShippingRateSerializer},
    )
    def post(self, request):
        serializer = ShippingRateCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        shipping_rate = ShippingRate.objects.create_shipping_rate(
            account=request.account,
            name=data["name"],
            code=data.get("code"),
            currency=data.get("currency"),
            amount=data.get("amount"),
            metadata=data.get("metadata"),
        )

        serializer = ShippingRateSerializer(shipping_rate)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_shipping_rate"))
class ShippingRateRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = ShippingRate.objects.none()
    serializer_class = ShippingRateSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return ShippingRate.objects.for_account(self.request.account)

    @extend_schema(
        operation_id="update_shipping_rate",
        request=ShippingRateUpdateSerializer,
        responses={200: ShippingRateSerializer},
    )
    def put(self, request, **_):
        shipping_rate = self.get_object()
        serializer = ShippingRateUpdateSerializer(
            shipping_rate, data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if shipping_rate.status == ShippingRateStatus.ARCHIVED:
            raise ValidationError("Cannot update once archived.")

        shipping_rate.update(
            name=data.get("name", shipping_rate.name),
            code=data.get("code", shipping_rate.code),
            currency=data.get("currency", shipping_rate.currency),
            amount=data.get("amount", shipping_rate.amount),
            metadata=data.get("metadata", shipping_rate.metadata),
        )

        serializer = ShippingRateSerializer(shipping_rate)
        return Response(serializer.data)

    @extend_schema(
        operation_id="delete_shipping_rate",
        request=None,
        responses={204: None},
    )
    def delete(self, _, **__):
        shipping_rate = self.get_object()

        shipping_rate.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ShippingRateArchiveAPIView(generics.GenericAPIView):
    queryset = ShippingRate.objects.none()
    serializer_class = ShippingRateSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return ShippingRate.objects.for_account(self.request.account)

    @extend_schema(
        operation_id="archive_shipping_rate",
        request=None,
        responses={200: ShippingRateSerializer},
    )
    def post(self, _, **__):
        shipping_rate = self.get_object()

        shipping_rate.archive()

        serializer = ShippingRateSerializer(shipping_rate)
        return Response(serializer.data)


class ShippingRateRestoreAPIView(generics.GenericAPIView):
    queryset = ShippingRate.objects.none()
    serializer_class = ShippingRateSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return ShippingRate.objects.for_account(self.request.account)

    @extend_schema(
        operation_id="restore_shipping_rate",
        request=None,
        responses={200: ShippingRateSerializer},
    )
    def post(self, _, **__):
        shipping_rate = self.get_object()

        shipping_rate.restore()

        serializer = ShippingRateSerializer(shipping_rate)
        return Response(serializer.data)
