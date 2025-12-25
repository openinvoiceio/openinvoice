import pytest
from factory.django import FileField

from apps.files.enums import FilePurpose
from common.pdf import get_generator
from tests.factories import (
    AccountFactory,
    FileFactory,
    MemberFactory,
    StripeCustomerFactory,
    StripeSubscriptionFactory,
    UserFactory,
)

from .api_client import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def account(user):
    account = AccountFactory()
    MemberFactory(user=user, account=account)
    return account


@pytest.fixture
def account_logo(account):
    return FileFactory(
        purpose=FilePurpose.ACCOUNT_LOGO,
        filename="logo.png",
        content_type="image/png",
        data=FileField(data=b"This is a test file content.", filename="logo.png"),
        account=account,
    )


@pytest.fixture
def subscribed_account(account):
    stripe_customer = StripeCustomerFactory(account=account)
    StripeSubscriptionFactory(stripe_customer=stripe_customer)
    return account


@pytest.fixture
def pdf_generator():
    generator = get_generator()
    generator.requests.clear()
    try:
        yield generator
    finally:
        generator.requests.clear()
