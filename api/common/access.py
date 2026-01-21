from django.conf import settings

from apps.accounts.models import Account
from common.choices import FeatureCode, LimitCode


def resolve_plan(account: Account) -> str:
    if not hasattr(settings, "STRIPE_API_KEY"):
        return settings.DEFAULT_PLAN

    subscription = account.active_subscription
    if subscription is None:
        return settings.DEFAULT_PLAN

    for code, plan in settings.PLANS.items():
        if subscription.price_id == plan.get("price_id"):
            return code

    return settings.DEFAULT_PLAN


def has_feature(account: Account, code: FeatureCode) -> bool:
    plan = resolve_plan(account)
    feature = settings.PLANS.get(plan, {}).get("features", {}).get(code)
    if isinstance(feature, bool):
        return feature
    return False


def is_limit_exceeded(account: Account, code: LimitCode, usage: int) -> bool:
    plan = resolve_plan(account)
    limit = settings.PLANS.get(plan, {}).get("limits", {}).get(code)
    if isinstance(limit, int):
        return usage >= limit
    return False
