import structlog
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated

from apps.customers.models import Customer

from .crypto import get_customer_id_from_token

logger = structlog.get_logger(__name__)


class PortalAuthentication(BaseAuthentication):
    """Authenticate portal requests using a token without creating sessions."""

    keyword = "Bearer"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth:
            raise NotAuthenticated

        if len(auth) != 2 or auth[0].lower() != self.keyword.lower().encode():
            raise AuthenticationFailed("Invalid token header")

        try:
            token = auth[1].decode()
        except UnicodeError as e:
            raise AuthenticationFailed("Invalid token header") from e

        customer_id = get_customer_id_from_token(token)
        logger.info("Token", customer_id=customer_id, token=token)
        if not customer_id:
            raise AuthenticationFailed("Invalid token")

        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist as e:
            raise AuthenticationFailed("Invalid token") from e

        request.customer = customer
        return AnonymousUser(), customer
