import json

import stripe
import structlog
from django.conf import settings
from django.http import HttpResponseRedirect
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAccountMember
from apps.integrations.models import StripeConnection
from apps.integrations.permissions import StripeIntegrationFeature
from apps.payments.backends.stripe import StripeBackend

from .serializers import StripeConnectionSerializer, StripeConnectionUpdateSerializer
from .services import delete_stripe_connection, update_stripe_connection

logger = structlog.get_logger(__name__)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_stripe_connection"))
class StripeConnectionRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = StripeConnection.objects.none()
    serializer_class = StripeConnectionSerializer
    permission_classes = [IsAuthenticated, IsAccountMember, StripeIntegrationFeature]

    def get_queryset(self):
        return StripeConnection.objects.filter(account_id=self.request.account.id)

    def get_object(self):
        return generics.get_object_or_404(self.get_queryset())

    @extend_schema(
        operation_id="update_stripe_connection",
        request=StripeConnectionUpdateSerializer,
        responses={200: StripeConnectionSerializer},
    )
    def put(self, request, **_):
        connection = self.get_object()
        serializer = StripeConnectionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        connection = update_stripe_connection(
            connection,
            redirect_url=serializer.validated_data.get("redirect_url", connection.redirect_url),
        )

        serializer = StripeConnectionSerializer(connection)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(operation_id="delete_stripe_connection", request=None, responses={204: None})
    def delete(self, _, **__):
        connection = self.get_object()

        delete_stripe_connection(connection)

        return Response(status=status.HTTP_204_NO_CONTENT)


class StripeConnectionOAuthCallback(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAccountMember]

    @extend_schema(request=None, responses={200: {}}, exclude=True)
    def get(self, request, **_):
        code = request.query_params.get("code")
        error = request.query_params.get("error")
        error_description = request.query_params.get("error_description")

        if code:
            response = stripe.OAuth.token(grant_type="authorization_code", code=code)
            connected_account_id = response["stripe_user_id"]
            StripeConnection.objects.create(
                account=request.account,
                connected_account_id=connected_account_id,
            )

        return HttpResponseRedirect(
            redirect_to=f"{settings.BASE_URL}/settings/integrations/stripe?error={error}&error_description={error_description}"
        )


class StripeWebhookAPIView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    @extend_schema(request=None, responses={200: {}}, exclude=True)
    def post(self, request):
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=request.headers.get("Stripe-Signature", ""),
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )
        except (ValueError, stripe.SignatureVerificationError) as e:
            logger.warning("Stripe webhook verification failed", error=str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST)

        StripeBackend.process_event(event)

        return Response(status=status.HTTP_200_OK)
