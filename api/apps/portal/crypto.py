from django.conf import settings
from django.core import signing

from apps.customers.models import Customer


def generate_portal_token(customer: Customer) -> str:
    signer = signing.TimestampSigner()
    return signer.sign(str(customer.id))


def get_customer_id_from_token(token: str) -> str | None:
    signer = signing.TimestampSigner()
    try:
        return signer.unsign(token, max_age=settings.PORTAL_TOKEN_MAX_AGE)
    except (signing.BadSignature, signing.SignatureExpired):
        return None
