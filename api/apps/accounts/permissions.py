from rest_framework.generics import get_object_or_404
from rest_framework.permissions import BasePermission

from .enums import MemberRole
from .models import Member

MAX_ACCOUNTS = 5


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


class CanCreateAccount(BasePermission):
    def has_permission(self, request, _):
        if request.method != "POST":
            return True

        accounts = request.accounts.all()
        if any(len(account.active_subscriptions) > 0 for account in accounts):
            return len(accounts) < MAX_ACCOUNTS

        return len(accounts) == 0
