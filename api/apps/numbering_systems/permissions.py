from common.enums import EntitlementCode
from common.permissions import EntitlementFeature


class CustomNumberingSystemFeature(EntitlementFeature):
    key = EntitlementCode.CUSTOM_NUMBERING_SYSTEMS
    methods = ["POST", "PUT", "DELETE"]
