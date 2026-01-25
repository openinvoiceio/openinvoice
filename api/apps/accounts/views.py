import structlog
from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.tax_ids.models import TaxId
from apps.tax_ids.serializers import TaxIdCreateSerializer, TaxIdSerializer

from .mail import send_invitation_email
from .models import Account, Invitation, Member
from .permissions import IsAccountMember, MaxAccountsLimit
from .serializers import (
    AccountCreateSerializer,
    AccountSerializer,
    AccountUpdateSerializer,
    InvitationAcceptSerializer,
    InvitationCreateSerializer,
    InvitationSerializer,
    MemberSerializer,
)
from .session import remove_active_account_session, set_active_account_session

logger = structlog.get_logger(__name__)


@extend_schema_view(list=extend_schema(operation_id="list_accounts"))
class AccountListCreateAPIView(generics.ListAPIView):
    queryset = Account.objects.none()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated, MaxAccountsLimit]

    def get_queryset(self):
        return self.request.accounts.eager_load()

    @extend_schema(
        operation_id="create_account",
        request=AccountCreateSerializer,
        responses={201: AccountSerializer},
    )
    def post(self, request):
        serializer = AccountCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account = Account.objects.create_account(
            name=serializer.validated_data["name"],
            legal_name=serializer.validated_data.get("legal_name"),
            legal_number=serializer.validated_data.get("legal_number"),
            email=serializer.validated_data["email"],
            country=serializer.validated_data["country"],
            created_by=request.user,
        )
        set_active_account_session(request, account)

        logger.info(
            "Account created",
            account_id=account.id,
            created_by=request.user.id,
            email=account.email,
        )

        serializer = AccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_account"))
class AccountRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = Account.objects.none()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return self.request.accounts.eager_load()

    @extend_schema(
        operation_id="update_account",
        request=AccountUpdateSerializer,
        responses={200: AccountSerializer},
    )
    def put(self, request, **_):
        account = self.get_object()
        serializer = AccountUpdateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        account.update(
            name=data.get("name", account.name),
            legal_name=data.get("legal_name", account.legal_name),
            legal_number=data.get("legal_number", account.legal_number),
            email=data.get("email", account.email),
            phone=data.get("phone", account.phone),
            country=data.get("country", account.country),
            default_currency=data.get("default_currency", account.default_currency),
            invoice_footer=data.get("invoice_footer", account.invoice_footer),
            invoice_numbering_system=data.get("invoice_numbering_system", account.invoice_numbering_system),
            credit_note_numbering_system=data.get("credit_note_numbering_system", account.credit_note_numbering_system),
            net_payment_term=data.get("net_payment_term", account.net_payment_term),
            metadata=data.get("metadata", account.metadata),
            logo=data.get("logo", account.logo),
        )
        account.address.update(**data.get("address", {}))

        logger.info("Account updated", account_id=account.id)

        serializer = AccountSerializer(account)
        return Response(serializer.data)

    @extend_schema(
        operation_id="delete_account",
        request=None,
        responses={200: AccountSerializer},
    )
    def delete(self, request, **_):
        account = self.get_object()

        if account.members.count() > 1:
            raise ValidationError("Account has members and cannot be deleted.")

        account.deactivate()
        remove_active_account_session(request)
        other_account = request.accounts.exclude(id=account.id).first()
        if other_account:
            set_active_account_session(request, other_account)

        logger.info("Account deactivated", account_id=account.id, requested_by=request.user.id)

        serializer = AccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AccountSwitchAPIView(generics.GenericAPIView):
    queryset = Account.objects.none()

    def get_queryset(self):
        return self.request.accounts

    @extend_schema(operation_id="switch_account", request=None, responses={204: None})
    def post(self, request, **_):
        account = self.get_object()
        set_active_account_session(request, account)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(list=extend_schema(operation_id="list_invitations"))
class InvitationListCreateAPIView(generics.ListAPIView):
    queryset = Invitation.objects.none()
    serializer_class = InvitationSerializer
    filterset_fields = ["status"]
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Invitation.objects.for_account(self.request.account)

    @extend_schema(
        operation_id="create_invitation",
        request=InvitationCreateSerializer,
        responses={201: InvitationSerializer},
    )
    def post(self, request):
        serializer = InvitationCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)

        invitation = self.request.account.invite_member(
            email=serializer.validated_data["email"],
            invited_by=request.user,
        )
        send_invitation_email(invitation)

        logger.info(
            "Invitation created",
            account_id=self.request.account.id,
            invitation_id=invitation.id,
            invited_email=invitation.email,
            invited_by=request.user.id,
        )

        serializer = InvitationSerializer(invitation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_invitation"))
class InvitationRetrieveDestroyAPIView(generics.RetrieveAPIView):
    queryset = Invitation.objects.none()
    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Invitation.objects.for_account(self.request.account)

    @extend_schema(
        operation_id="delete_invitation",
        request=None,
        responses={204: None},
    )
    def delete(self, _, **__):
        invitation = self.get_object()

        invitation.delete()

        logger.info(
            "Invitation deleted",
            invitation_id=invitation.id,
            account_id=self.request.account.id,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class InvitationAcceptAPIView(generics.GenericAPIView):
    serializer_class = InvitationSerializer

    @extend_schema(
        operation_id="accept_invitation",
        request=InvitationAcceptSerializer,
        responses={200: MemberSerializer},
    )
    def post(self, request):
        serializer = InvitationAcceptSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        invitation = serializer.validated_data["invitation"]

        member = invitation.accept(user=request.user)
        set_active_account_session(request, member.account)

        logger.info(
            "Invitation accepted",
            invitation_id=invitation.id,
            account_id=invitation.account_id,
            user_id=request.user.id,
        )

        serializer = MemberSerializer(member, context={"request": request})
        return Response(serializer.data)


@extend_schema_view(list=extend_schema(operation_id="list_members"))
class MemberListAPIView(generics.ListAPIView):
    queryset = Member.objects.none()
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        account = get_object_or_404(self.request.accounts, id=self.kwargs["account_id"])
        return Member.objects.filter(account=account)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_member"))
class MemberRetrieveDestroyAPIView(generics.RetrieveAPIView):
    queryset = Member.objects.none()
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Member.objects.filter(account__in=self.request.accounts, account_id=self.kwargs["account_id"])

    @extend_schema(
        operation_id="delete_member",
        request=None,
        responses={204: None},
    )
    def delete(self, _, **__):
        member = self.get_object()

        if member.user.accounts_member_of.count() == 1:
            raise ValidationError("Cannot remove the last member of the account.")

        member.delete()

        logger.info("Member removed", account_id=self.request.account.id, member_id=member.id)

        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountTaxIdCreateAPIView(generics.GenericAPIView):
    queryset = Account.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return self.request.accounts

    @extend_schema(
        operation_id="create_account_tax_id",
        request=TaxIdCreateSerializer,
        responses={201: TaxIdSerializer},
    )
    def post(self, request, *_, **__):
        account = self.get_object()
        serializer = TaxIdCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if account.tax_ids.count() >= settings.MAX_TAX_IDS:
            raise ValidationError(f"You can add at most {settings.MAX_TAX_IDS} tax IDs to an account.")

        tax_id = TaxId.objects.create_tax_id(
            type_=data["type"],
            number=data["number"],
            country=data.get("country"),
        )
        account.tax_ids.add(tax_id)

        logger.info(
            "Account tax ID created",
            account_id=account.id,
            tax_id_id=tax_id.id,
        )

        serializer = TaxIdSerializer(tax_id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AccountTaxIdDestroyAPIView(generics.DestroyAPIView):
    queryset = TaxId.objects.none()
    serializer_class = TaxIdSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return TaxId.objects.filter(accounts__in=self.request.accounts, accounts__id=self.kwargs["account_id"])

    @extend_schema(operation_id="delete_account_tax_id", request=None, responses={204: None})
    def delete(self, *_, **__):
        tax_id = self.get_object()

        tax_id.delete()

        logger.info(
            "Account tax ID deleted",
            account_id=self.kwargs["account_id"],
            tax_id_id=tax_id.id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
