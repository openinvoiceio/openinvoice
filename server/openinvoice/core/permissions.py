from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from .access import has_feature, is_limit_exceeded
from .choices import FeatureCode, LimitCode


class HasFeature(BasePermission):
    key: FeatureCode
    methods: list[str]
    code = "feature_unavailable"
    message = "Feature is not available for your account."

    def has_permission(self, request, _):
        if request.method not in self.methods:
            return True

        if request.account is None:
            return False

        return has_feature(request.account, self.key)


class WithinLimit(BasePermission):
    key: LimitCode
    methods: list[str]
    code = "limit_exceeded"
    message = "Limit has been exceeded for your account."

    def get_usage(self, _: Request) -> int:
        return 0

    def has_permission(self, request, _):
        if request.method not in self.methods:
            return True

        if request.account is None:
            return False

        usage = self.get_usage(request)
        return not is_limit_exceeded(request.account, self.key, usage)
