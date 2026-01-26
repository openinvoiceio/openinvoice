import structlog
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember

from .filtersets import PaymentFilterSet
from .models import Payment
from .serializers import PaymentRecordSerializer, PaymentSerializer

logger = structlog.get_logger(__name__)


@extend_schema_view(list=extend_schema(operation_id="list_payments"))
class PaymentListCreateAPIView(generics.ListAPIView):
    queryset = Payment.objects.none()
    serializer_class = PaymentSerializer
    ordering_fields = ["created_at"]
    permission_classes = [IsAuthenticated, IsAccountMember]
    filterset_class = PaymentFilterSet

    def get_queryset(self):
        return Payment.objects.for_account(self.request.account)

    @extend_schema(operation_id="record_payment", request=PaymentRecordSerializer, responses={201: PaymentSerializer})
    def post(self, request):
        serializer = PaymentRecordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        payment = Payment.objects.record_payment(
            invoice=data["invoice"],
            amount=data["amount"],
            currency=data["currency"],
            description=data.get("description"),
            transaction_id=data.get("transaction_id"),
            received_at=data.get("received_at"),
        )

        logger.info(
            "Manual payment recorded",
            account_id=str(request.account.id),
            invoice_id=str(data["invoice"].id),
            payment_id=str(payment.id),
        )

        serializer = PaymentSerializer(payment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_payment"))
class PaymentRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Payment.objects.none()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Payment.objects.for_account(self.request.account)
