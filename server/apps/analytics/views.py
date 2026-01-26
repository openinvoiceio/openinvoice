from __future__ import annotations

from dateutil.relativedelta import relativedelta
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember
from apps.invoices.models import Invoice

from .queries import fetch_gross_revenue, fetch_overdue_balance
from .serializers import (
    GrossRevenueParamsSerializer,
    GrossRevenueSerializer,
    OverdueBalanceParamsSerializer,
    OverdueBalanceSerializer,
)


class GrossRevenueAPIView(generics.GenericAPIView):
    queryset = Invoice.objects.none()
    serializer_class = GrossRevenueSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, IsAccountMember]

    @extend_schema(
        operation_id="get_gross_revenue",
        parameters=[GrossRevenueParamsSerializer],
        responses={200: GrossRevenueSerializer(many=True)},
    )
    def get(self, request):
        serializer = GrossRevenueParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        today = timezone.now().date()
        date_before = data.get("date_before", today).replace(day=1)
        date_after = data.get("date_after", date_before - relativedelta(months=12)).replace(day=1)
        currency = data.get("currency", request.account.default_currency)

        data = fetch_gross_revenue(
            account_id=request.account.id,
            currency=currency,
            date_after=min(date_after, date_before),
            date_before=date_before,
            customer_id=data.get("customer_id"),
        )

        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)


class OverdueBalanceAPIView(generics.GenericAPIView):
    queryset = Invoice.objects.none()
    serializer_class = OverdueBalanceSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, IsAccountMember]

    @extend_schema(
        operation_id="get_overdue_balance",
        parameters=[OverdueBalanceParamsSerializer],
        responses={200: OverdueBalanceSerializer(many=True)},
    )
    def get(self, request):
        serializer = OverdueBalanceParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        today = timezone.now().date()
        capped_before = min(data.get("date_before", today), today)
        date_before = capped_before.replace(day=1)
        date_after = data.get("date_after", date_before - relativedelta(months=12)).replace(day=1)
        currency = data.get("currency", request.account.default_currency)

        data = fetch_overdue_balance(
            account_id=request.account.id,
            currency=currency,
            today=today,
            date_after=min(date_after, date_before),
            date_before=date_before,
            customer_id=data.get("customer_id"),
        )

        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)
