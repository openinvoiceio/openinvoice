from common.enums import FeatureCode
from common.permissions import HasFeature


class CustomNumberingSystemFeature(HasFeature):
    key = FeatureCode.CUSTOM_NUMBERING_SYSTEMS
    methods = ["POST", "PUT", "DELETE"]
