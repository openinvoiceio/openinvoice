from rest_framework.generics import get_object_or_404
from rest_framework.permissions import BasePermission

from openinvoice.core.access import is_limit_exceeded
from openinvoice.core.choices import LimitCode
from openinvoice.core.permissions import WithinLimit

from .choices import MemberRole
from .models import Member


class IsAccountMember(BasePermission):
    def has_permission(self, request, _):
        return request.account is not None


class IsAccountOwner(BasePermission):
    def has_permission(self, request, _):
        if request.account is None:
            return False

        member = get_object_or_404(
            Member, user=request.user, account_id=request.account.id, account__in=request.accounts
        )

        return member and member.role == MemberRole.OWNER


class MaxAccountsLimit(WithinLimit):
    key = LimitCode.MAX_ACCOUNTS
    methods = ["POST"]

    def get_usage(self, request) -> int:
        return request.accounts.count()

    def has_permission(self, request, _):
        if request.method not in self.methods:
            return True

        usage = self.get_usage(request)
        return not is_limit_exceeded(request.account, self.key, usage)
