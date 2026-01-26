import pytest

from apps.addresses.models import Address
from tests.factories import AddressFactory

pytestmark = pytest.mark.django_db


def test_create_address():
    address = Address.objects.create_address(
        line1="123 Main St",
        line2="Suite 100",
        locality="City",
        state="State",
        postal_code="00-001",
        country="PL",
    )

    assert Address.objects.filter(id=address.id).exists()
    assert address.line1 == "123 Main St"
    assert address.line2 == "Suite 100"
    assert address.locality == "City"
    assert address.state == "State"
    assert address.postal_code == "00-001"
    assert address.country == "PL"


def test_update_address():
    address = AddressFactory(
        line1="Old",
        line2="Old2",
        locality="OldCity",
        state="OldState",
        postal_code="11-111",
        country="US",
    )

    address.update(
        line1="New",
        line2=None,
        locality="NewCity",
        state="NewState",
        postal_code="22-222",
        country="CA",
    )

    address.refresh_from_db()
    assert address.line1 == "New"
    assert address.line2 is None
    assert address.locality == "NewCity"
    assert address.state == "NewState"
    assert address.postal_code == "22-222"
    assert address.country == "CA"


def test_clone_address():
    address = AddressFactory(
        line1="Clone St",
        line2="Floor 3",
        locality="CloneCity",
        state="CloneState",
        postal_code="33-333",
        country="DE",
    )

    cloned = Address.objects.from_address(address)

    assert cloned.id != address.id
    assert cloned.line1 == address.line1
    assert cloned.line2 == address.line2
    assert cloned.locality == address.locality
    assert cloned.state == address.state
    assert cloned.postal_code == address.postal_code
    assert cloned.country == address.country
