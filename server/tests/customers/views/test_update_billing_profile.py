import pytest

from tests.factories import BillingProfileFactory, CustomerFactory, TaxRateFactory

pytestmark = pytest.mark.django_db


def test_update_billing_profile_tax_rates(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)
    billing_profile = BillingProfileFactory()
    customer.billing_profiles.add(billing_profile)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/billing-profiles/{billing_profile.id}",
        {"tax_rates": [str(tax_rate.id)]},
    )

    assert response.status_code == 200
    assert [tax_rate_data["id"] for tax_rate_data in response.data["tax_rates"]] == [str(tax_rate.id)]


def test_update_billing_profile_clears_tax_rates(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)
    billing_profile = BillingProfileFactory()
    billing_profile.tax_rates.add(tax_rate)
    customer.billing_profiles.add(billing_profile)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/billing-profiles/{billing_profile.id}",
        {"tax_rates": []},
    )

    assert response.status_code == 200
    assert response.data["tax_rates"] == []
