import stripe
import structlog
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAccountMember
from apps.payments.models import Payment

from .models import StripeConnection
from .permissions import StripeIntegrationFeature
from .serializers import (
    StripeConnectionCreateSerializer,
    StripeConnectionSerializer,
    StripeConnectionUpdateSerializer,
)
from .tasks import (
    handle_checkout_async_payment_failed_event,
    handle_checkout_async_payment_succeeded_event,
    handle_checkout_session_completed_event,
    handle_checkout_session_expired_event,
)

logger = structlog.get_logger(__name__)


@extend_schema_view(list=extend_schema(operation_id="list_stripe_connections"))
class StripeConnectionListCreateAPIView(generics.ListAPIView):
    queryset = StripeConnection.objects.none()
    serializer_class = StripeConnectionSerializer
    permission_classes = [IsAuthenticated, IsAccountMember, StripeIntegrationFeature]

    def get_queryset(self):
        return StripeConnection.objects.for_account(self.request.account)

    @extend_schema(
        operation_id="create_stripe_connection",
        request=StripeConnectionCreateSerializer,
        responses={201: StripeConnectionSerializer},
    )
    def post(self, request):
        serializer = StripeConnectionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        connection = StripeConnection.objects.create_connection(
            account=request.account,
            name=serializer.validated_data["name"],
            code=serializer.validated_data["code"],
            api_key=serializer.validated_data["api_key"],
            redirect_url=serializer.validated_data.get("redirect_url"),
        )

        logger.info("Stripe connection created", connection_id=connection.id)

        serializer = StripeConnectionSerializer(connection)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_stripe_connection"))
class StripeConnectionRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = StripeConnection.objects.none()
    serializer_class = StripeConnectionSerializer
    permission_classes = [IsAuthenticated, IsAccountMember, StripeIntegrationFeature]

    def get_queryset(self):
        return StripeConnection.objects.for_account(self.request.account)

    @extend_schema(
        operation_id="update_stripe_connection",
        request=StripeConnectionUpdateSerializer,
        responses={200: StripeConnectionSerializer},
    )
    def put(self, request, **_):
        connection = self.get_object()
        serializer = StripeConnectionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        connection.update(
            name=serializer.validated_data.get("name", connection.name),
            redirect_url=serializer.validated_data.get("redirect_url", connection.redirect_url),
        )

        logger.info("Stripe connection updated", connection_id=connection.id)

        serializer = StripeConnectionSerializer(connection)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(operation_id="delete_stripe_connection", request=None, responses={204: None})
    def delete(self, _, **__):
        connection = self.get_object()

        # TODO: consider archiving instead of deleting
        connection.delete()

        logger.info("Stripe connection deleted", connection_id=connection.id)

        return Response(status=status.HTTP_204_NO_CONTENT)


class StripeWebhookAPIView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    @extend_schema(request=None, responses={200: {}}, exclude=True)
    def post(self, request, pk):
        try:
            connection = StripeConnection.objects.get(id=pk)
        except StripeConnection.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            event = stripe.Webhook.construct_event(
                payload=request.body,
                sig_header=request.META["HTTP_STRIPE_SIGNATURE"],
                secret=connection.webhook_secret,
            )
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.SignatureVerificationError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            match event.get("type"):
                case "checkout.session.completed":
                    handle_checkout_session_completed_event(event)
                case "checkout.session.async_payment_succeeded":
                    handle_checkout_async_payment_succeeded_event(event)
                case "checkout.session.async_payment_failed":
                    handle_checkout_async_payment_failed_event(event)
                case "checkout.session.expired":
                    handle_checkout_session_expired_event(event)
                case _:
                    logger.info("Stripe event ignored", event_type=event.get("type"))
        except Payment.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)
