from common.choices import LimitCode
from common.permissions import WithinLimit

from .models import Product


class MaxProductsLimit(WithinLimit):
    key = LimitCode.MAX_PRODUCTS
    methods = ["POST"]

    def get_usage(self, request) -> int:
        return Product.objects.for_account(request.account).count()
