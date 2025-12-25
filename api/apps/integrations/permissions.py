from common.enums import EntitlementCode
from common.permissions import EntitlementFeature


class StripeIntegrationFeature(EntitlementFeature):
    key = EntitlementCode.STRIPE_INTEGRATION
    methods = ["POST", "PUT", "DELETE"]
