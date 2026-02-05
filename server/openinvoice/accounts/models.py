from __future__ import annotations

import uuid
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django_countries.fields import CountryField
from djmoney import settings as djmoney_settings

from openinvoice.addresses.models import Address
from openinvoice.users.models import User

from .choices import InvitationStatus, MemberRole
from .managers import AccountManager, BusinessProfileManager
from .querysets import AccountQuerySet, BusinessProfileQuerySet, InvitationQuerySet

if TYPE_CHECKING:
    from openinvoice.files.models import File
    from openinvoice.numbering_systems.models import NumberingSystem


class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)
    members = models.ManyToManyField("users.User", through="accounts.Member", related_name="accounts_member_of")
    created_by = models.ForeignKey("users.User", on_delete=models.CASCADE)
    country = CountryField()
    default_currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    language = models.CharField(max_length=10, choices=settings.LANGUAGES)
    invoice_footer = models.CharField(max_length=600, null=True, blank=True)
    invoice_numbering_system = models.OneToOneField(
        "numbering_systems.NumberingSystem",
        on_delete=models.PROTECT,
        related_name="invoice_numbering_account",
        null=True,
    )
    credit_note_numbering_system = models.OneToOneField(
        "numbering_systems.NumberingSystem",
        on_delete=models.PROTECT,
        related_name="credit_note_numbering_account",
        null=True,
    )
    net_payment_term = models.PositiveIntegerField()
    logo = models.OneToOneField("files.File", on_delete=models.SET_NULL, null=True, related_name="account_logo")
    metadata = models.JSONField(default=dict)
    default_business_profile = models.OneToOneField(
        "BusinessProfile",
        on_delete=models.PROTECT,
        related_name="+",
    )
    business_profiles = models.ManyToManyField("BusinessProfile", related_name="accounts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccountManager.from_queryset(AccountQuerySet)()

    class Meta:
        ordering = ["-created_at"]

    def update(
        self,
        country: str,
        default_currency: str,
        language: str,
        invoice_footer: str | None,
        invoice_numbering_system: NumberingSystem | None,
        credit_note_numbering_system: NumberingSystem | None,
        net_payment_term: int,
        metadata: dict,
        logo: File | None,
    ) -> None:
        self.country = country
        self.default_currency = default_currency
        self.language = language
        self.invoice_footer = invoice_footer
        self.invoice_numbering_system = invoice_numbering_system
        self.credit_note_numbering_system = credit_note_numbering_system
        self.net_payment_term = net_payment_term
        self.metadata = metadata
        self.logo = logo

        self.save()

    def deactivate(self) -> None:
        if not self.is_active:
            return

        self.is_active = False
        self.save()

    def invite_member(self, *, email: str, invited_by: User) -> Invitation:
        self.invitations.filter(email=email).delete()

        return self.invitations.create(
            email=email,
            code=get_random_string(64).lower(),
            status=InvitationStatus.PENDING,
            invited_by=invited_by,
        )


class BusinessProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, null=True)
    legal_number = models.CharField(max_length=255, null=True)
    email = models.EmailField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    address = models.OneToOneField(
        "addresses.Address",
        on_delete=models.PROTECT,
        related_name="business_profile_address",
    )
    tax_ids = models.ManyToManyField("tax_ids.TaxId", related_name="business_profiles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    objects = BusinessProfileManager.from_queryset(BusinessProfileQuerySet)()

    def clone(self) -> BusinessProfile:
        new_profile = BusinessProfile.objects.create(
            name=self.name,
            legal_name=self.legal_name,
            legal_number=self.legal_number,
            email=self.email,
            phone=self.phone,
            address=Address.objects.from_address(self.address),
        )
        new_profile.tax_ids.set(self.tax_ids.clone())
        return new_profile

    def update(
        self,
        name: str,
        legal_name: str | None,
        legal_number: str | None,
        email: str | None,
        phone: str | None,
        address_data: dict | None,
    ) -> None:
        self.name = name
        self.legal_name = legal_name
        self.legal_number = legal_number
        self.email = email
        self.phone = phone
        self.save()
        self.address.update(**(address_data or {}))


class Member(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="member")
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=MemberRole.choices)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-joined_at"]
        unique_together = ("user", "account")


class Invitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="invitations")
    code = models.CharField(max_length=1000)
    status = models.CharField(max_length=50, choices=InvitationStatus.choices)
    invited_by = models.ForeignKey("users.User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True)

    objects = models.Manager.from_queryset(InvitationQuerySet)()

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_expired(self) -> bool:
        expiration_date = self.created_at + timedelta(days=settings.INVITATION_EXPIRATION_DAYS)
        return timezone.now() > expiration_date

    def accept(self, user: User) -> Member:
        member = Member.objects.create(user=user, account=self.account, role=MemberRole.MEMBER)

        self.status = InvitationStatus.ACCEPTED
        self.accepted_at = timezone.now()
        self.save(update_fields=["status", "accepted_at"])

        return member
