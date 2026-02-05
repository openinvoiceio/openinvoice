from openinvoice.core.choices import FeatureCode
from openinvoice.core.permissions import HasFeature


class CustomNumberingSystemFeature(HasFeature):
    key = FeatureCode.CUSTOM_NUMBERING_SYSTEMS
    methods = ["POST", "PUT", "DELETE"]
