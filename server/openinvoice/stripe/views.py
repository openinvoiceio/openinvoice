import stripe
import structlog
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from openinvoice.accounts.permissions import IsAccountMember

from .models import StripeCustomer
from .serializers import (
    StripeBillingPortalSerializer,
    StripeCheckoutSerializer,
    StripeCheckoutSessionSerializer,
)
from .tasks import (
    handle_subscription_created_event,
    handle_subscription_deleted_event,
    handle_subscription_updated_event,
)

logger = structlog.get_logger(__name__)


class StripeWebhookAPIView(GenericAPIView):
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={200: {}}, exclude=True)
    def post(self, request):
        if not hasattr(settings, "STRIPE_API_KEY"):
            raise NotFound

        try:
            event = stripe.Webhook.construct_event(
                payload=request.body,
                sig_header=request.META["HTTP_STRIPE_SIGNATURE"],
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.SignatureVerificationError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            match event["type"]:
                case "customer.subscription.created":
                    handle_subscription_created_event(event)
                case "customer.subscription.updated":
                    handle_subscription_updated_event(event)
                case "customer.subscription.deleted":
                    handle_subscription_deleted_event(event)
                case _:
                    logger.info("Stripe event ignored", event_type=event.get("type"))
        except Exception as e:
            logger.error("Failed to handle Stripe webhook event", data=event, error=str(e))
            raise APIException("Failed to handle Stripe webhook event") from e

        return Response(status=status.HTTP_200_OK)


class StripeCheckoutAPIView(GenericAPIView):
    serializer_class = StripeCheckoutSessionSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    @extend_schema(
        operation_id="create_stripe_checkout",
        request=StripeCheckoutSerializer,
        responses=StripeCheckoutSessionSerializer,
    )
    def post(self, request):
        if not hasattr(settings, "STRIPE_API_KEY"):
            raise NotFound

        serializer = StripeCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            stripe_customer = StripeCustomer.objects.ensure_for_account(self.request.account)
            checkout_session = stripe_customer.create_checkout_session(serializer.validated_data["price_id"])
            logger.info(
                "Stripe checkout session created",
                account_id=str(self.request.account.id),
                stripe_customer_id=stripe_customer.customer_id,
                session_id=checkout_session.id,
                price_id=serializer.validated_data["price_id"],
            )
        except stripe.StripeError as e:
            logger.error("Failed to create checkout session", error=str(e))
            raise ValidationError("Failed to create checkout session") from e

        serializer = StripeCheckoutSessionSerializer(data={"session_url": checkout_session.url})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StripeBillingPortalAPIView(generics.GenericAPIView):
    serializer_class = StripeBillingPortalSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    @extend_schema(
        operation_id="create_stripe_billing_portal",
        request=None,
        responses={"200": StripeBillingPortalSerializer},
    )
    def post(self, request):
        if not hasattr(settings, "STRIPE_API_KEY"):
            raise NotFound

        try:
            stripe_customer = StripeCustomer.objects.ensure_for_account(request.account)
            session = stripe_customer.create_billing_portal_session()
            logger.info(
                "Stripe billing portal session created",
                account_id=str(request.account.id),
                stripe_customer_id=stripe_customer.customer_id,
                session_id=session.id,
            )
        except stripe.StripeError as e:
            raise APIException("Failed to create billing portal session") from e

        serializer = StripeBillingPortalSerializer(data={"url": session.url})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
