from openinvoice.core.choices import FeatureCode
from openinvoice.core.permissions import HasFeature


class StripeIntegrationFeature(HasFeature):
    key = FeatureCode.STRIPE_INTEGRATION
    methods = ["POST", "PUT", "DELETE"]
