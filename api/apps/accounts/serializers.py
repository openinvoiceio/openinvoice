from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from apps.addresses.serializers import AddressSerializer
from apps.files.fields import FileRelatedField
from apps.numbering_systems.choices import NumberingSystemAppliesTo
from apps.numbering_systems.fields import NumberingSystemRelatedField
from apps.stripe.serializers import StripeSubscriptionSerializer
from apps.taxes.serializers import TaxIdSerializer
from apps.users.serializers import UserSerializer
from common.fields import CurrencyField, MetadataField

from .choices import InvitationStatus, MemberRole
from .models import Invitation


class AccountSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    legal_name = serializers.CharField(allow_null=True)
    legal_number = serializers.CharField(allow_null=True)
    email = serializers.EmailField()
    phone = serializers.CharField(allow_null=True)
    address = AddressSerializer()
    country = CountryField()
    default_currency = CurrencyField()
    invoice_footer = serializers.CharField(allow_null=True)
    invoice_numbering_system_id = serializers.UUIDField(allow_null=True)
    credit_note_numbering_system_id = serializers.UUIDField(allow_null=True)
    net_payment_term = serializers.IntegerField()
    metadata = MetadataField()
    subscription = StripeSubscriptionSerializer(allow_null=True, source="active_subscription")
    logo_id = serializers.UUIDField(allow_null=True)
    logo_url = serializers.FileField(use_url=True, source="logo.data", allow_null=True)
    tax_ids = TaxIdSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)


class AccountCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    legal_name = serializers.CharField(max_length=255, allow_null=True, required=False)
    legal_number = serializers.CharField(max_length=255, allow_null=True, required=False)
    email = serializers.EmailField(max_length=255)
    country = CountryField()


class AccountUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    legal_name = serializers.CharField(max_length=255, allow_null=True, required=False)
    legal_number = serializers.CharField(max_length=255, allow_null=True, required=False)
    email = serializers.EmailField(max_length=255, required=False)
    phone = serializers.CharField(max_length=255, allow_null=True, required=False)
    address = AddressSerializer(required=False)
    country = CountryField(required=False)
    default_currency = CurrencyField(required=False)
    invoice_footer = serializers.CharField(allow_null=True, max_length=255, required=False)
    invoice_numbering_system_id = NumberingSystemRelatedField(
        source="invoice_numbering_system", applies_to=NumberingSystemAppliesTo.INVOICE, allow_null=True, required=False
    )
    credit_note_numbering_system_id = NumberingSystemRelatedField(
        source="credit_note_numbering_system",
        applies_to=NumberingSystemAppliesTo.CREDIT_NOTE,
        allow_null=True,
        required=False,
    )
    net_payment_term = serializers.IntegerField(required=False)
    metadata = MetadataField(required=False)
    logo_id = FileRelatedField(source="logo", allow_null=True, required=False)


class InvitationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    status = serializers.ChoiceField(choices=InvitationStatus.choices)
    created_at = serializers.DateTimeField()
    accepted_at = serializers.DateTimeField(allow_null=True)
    rejected_at = serializers.DateTimeField(allow_null=True)


class InvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    def validate_email(self, email):
        account = self.context["request"].account

        if account.members.filter(email=email).exists():
            raise serializers.ValidationError("A member with this email already exists in the account.")

        if account.invitations.filter(email=email, status=InvitationStatus.PENDING).exists():
            raise serializers.ValidationError("An invitation has already been sent to this email.")

        return email


class InvitationAcceptSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=300)

    def validate(self, data):
        invitation = Invitation.objects.pending_for(code=data["code"], user=self.context["request"].user)

        if not invitation:
            raise serializers.ValidationError("Invalid invitation code.")

        if invitation.is_expired:
            raise serializers.ValidationError("This invitation has expired.")

        data["invitation"] = invitation

        return data


class MemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user = UserSerializer()
    account_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=MemberRole.choices)
    joined_at = serializers.DateTimeField()
