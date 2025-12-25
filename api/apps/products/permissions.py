from common.enums import EntitlementCode
from common.permissions import EntitlementLimit

from .models import Product


class MaxProductsLimit(EntitlementLimit):
    key = EntitlementCode.MAX_PRODUCTS
    methods = ["POST"]

    def get_usage(self, request) -> int:
        return Product.objects.filter(account_id=request.account.id).count()
