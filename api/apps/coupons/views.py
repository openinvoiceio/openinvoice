import structlog
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember

from .choices import CouponStatus
from .filtersets import CouponFilterSet
from .models import Coupon
from .permissions import MaxCouponsLimit
from .serializers import CouponCreateSerializer, CouponSerializer, CouponUpdateSerializer

logger = structlog.get_logger(__name__)


@extend_schema_view(list=extend_schema(operation_id="list_coupons"))
class CouponListCreateAPIView(generics.ListAPIView):
    queryset = Coupon.objects.none()
    serializer_class = CouponSerializer
    filterset_class = CouponFilterSet
    search_fields = ["name"]
    ordering_fields = ["created_at"]
    permission_classes = [IsAuthenticated, IsAccountMember, MaxCouponsLimit]

    def get_queryset(self):
        return Coupon.objects.for_account(self.request.account).order_by("-created_at")

    @extend_schema(
        operation_id="create_coupon",
        request=CouponCreateSerializer,
        responses={201: CouponSerializer},
    )
    def post(self, request):
        serializer = CouponCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        coupon = Coupon.objects.create_coupon(
            account=request.account,
            name=data["name"],
            currency=data.get("currency"),
            amount=data.get("amount"),
            percentage=data.get("percentage"),
        )
        logger.info(
            "Coupon created",
            account_id=request.account.id,
            coupon_id=coupon.id,
        )

        serializer = CouponSerializer(coupon)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_coupon"))
class CouponRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = Coupon.objects.none()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Coupon.objects.for_account(self.request.account)

    @extend_schema(
        operation_id="update_coupon",
        request=CouponUpdateSerializer,
        responses={200: CouponSerializer},
    )
    def put(self, request, **_):
        coupon = self.get_object()
        serializer = CouponUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if coupon.status == CouponStatus.ARCHIVED:
            raise ValidationError("Cannot update once archived.")

        coupon.update(name=serializer.validated_data.get("name", coupon.name))
        logger.info(
            "Coupon updated",
            account_id=request.account.id,
            coupon_id=coupon.id,
        )

        serializer = CouponSerializer(coupon)
        return Response(serializer.data)

    @extend_schema(
        operation_id="delete_coupon",
        request=None,
        responses={200: CouponSerializer},
    )
    def delete(self, request, **__):
        coupon = self.get_object()

        coupon.archive()
        logger.info(
            "Coupon archived",
            account_id=request.account.id,
            coupon_id=coupon.id,
        )

        serializer = CouponSerializer(coupon)
        return Response(serializer.data)


class CouponArchiveAPIView(generics.GenericAPIView):
    queryset = Coupon.objects.none()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Coupon.objects.for_account(self.request.account)

    @extend_schema(operation_id="archive_coupon", request=None, responses={200: CouponSerializer})
    def post(self, request, **__):
        coupon = self.get_object()

        coupon.archive()
        logger.info(
            "Coupon archived",
            account_id=request.account.id,
            coupon_id=coupon.id,
        )

        serializer = CouponSerializer(coupon)
        return Response(serializer.data)


class CouponRestoreAPIView(generics.GenericAPIView):
    queryset = Coupon.objects.none()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Coupon.objects.for_account(self.request.account)

    @extend_schema(operation_id="restore_coupon", request=None, responses={200: CouponSerializer})
    def post(self, request, **__):
        coupon = self.get_object()

        coupon.restore()
        logger.info(
            "Coupon restored",
            account_id=request.account.id,
            coupon_id=coupon.id,
        )

        serializer = CouponSerializer(coupon)
        return Response(serializer.data)
