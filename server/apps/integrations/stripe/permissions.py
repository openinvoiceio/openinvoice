from common.choices import FeatureCode
from common.permissions import HasFeature


class StripeIntegrationFeature(HasFeature):
    key = FeatureCode.STRIPE_INTEGRATION
    methods = ["POST", "PUT", "DELETE"]
