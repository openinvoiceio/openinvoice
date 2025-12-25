from django.conf import settings

from apps.accounts.models import Account
from common.enums import EntitlementCode


def resolve_entitlement_group(account: Account) -> str:
    if not hasattr(settings, "STRIPE_API_KEY"):
        return settings.DEFAULT_ENTITLEMENT_GROUP

    subscription = account.active_subscription
    if subscription is None:
        return settings.DEFAULT_ENTITLEMENT_GROUP

    if subscription.price_id == settings.STRIPE_STANDARD_PRICE_ID:
        return settings.STANDARD_ENTITLEMENT_GROUP
    if subscription.price_id == settings.STRIPE_ENTERPRISE_PRICE_ID:
        return settings.ENTERPRISE_ENTITLEMENT_GROUP
    return settings.DEFAULT_ENTITLEMENT_GROUP


class EntitlementManager:
    def __init__(self, account: Account):
        self.group = resolve_entitlement_group(account)

    def get_entitlement(self, code: EntitlementCode) -> bool | int | None:
        return settings.ENTITLEMENTS.get(self.group, {}).get(code)

    def has_feature(self, code: EntitlementCode) -> bool:
        value = self.get_entitlement(code)
        if isinstance(value, bool):
            return value
        return False

    def is_limit_exceeded(self, code: EntitlementCode, usage: int) -> bool:
        value = self.get_entitlement(code)
        if isinstance(value, int):
            return usage >= value
        return False


def has_feature(account: Account, code: EntitlementCode) -> bool:
    return EntitlementManager(account).has_feature(code)


def is_limit_exceeded(account: Account, code: EntitlementCode, usage: int) -> bool:
    return EntitlementManager(account).is_limit_exceeded(code, usage)
