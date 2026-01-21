from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember
from apps.invoices.choices import InvoiceStatus

from .choices import CreditNoteDeliveryMethod, CreditNotePreviewFormat, CreditNoteStatus
from .filters import CreditNoteFilter
from .mail import send_credit_note
from .models import CreditNote, CreditNoteLine, CreditNoteTax
from .permissions import MaxCreditNotesLimit
from .serializers import (
    CreditNoteCreateSerializer,
    CreditNoteIssueSerializer,
    CreditNoteLineCreateSerializer,
    CreditNoteLineSerializer,
    CreditNoteLineTaxCreateSerializer,
    CreditNoteLineUpdateSerializer,
    CreditNoteSerializer,
    CreditNoteUpdateSerializer,
    CreditNoteVoidSerializer,
)


@extend_schema_view(list=extend_schema(operation_id="list_credit_notes"))
class CreditNoteListCreateAPIView(generics.ListAPIView):
    queryset = CreditNote.objects.none()
    serializer_class = CreditNoteSerializer
    filterset_class = CreditNoteFilter
    permission_classes = [IsAuthenticated, IsAccountMember, MaxCreditNotesLimit]
    search_fields = [
        "number",
        "invoice__number",
        "customer__name",
        "customer__email",
    ]
    ordering_fields = ["created_at", "issue_date", "total_amount"]

    def get_queryset(self):
        return (
            CreditNote.objects.filter(account_id=self.request.account.id)
            .select_related(
                "invoice",
                "customer",
                "account",
                "invoice__customer_on_invoice",
                "invoice__customer_on_invoice__billing_address",
                "invoice__customer_on_invoice__shipping_address",
                "invoice__customer_on_invoice__logo",
                "invoice__account_on_invoice",
                "invoice__account_on_invoice__address",
                "invoice__account_on_invoice__logo",
                "customer__billing_address",
                "customer__shipping_address",
                "customer__logo",
                "account__address",
                "account__logo",
            )
            .prefetch_related(
                "customer__tax_ids",
                "account__tax_ids",
                "invoice__customer_on_invoice__tax_ids",
                "invoice__account_on_invoice__tax_ids",
                Prefetch(
                    "lines",
                    queryset=CreditNoteLine.objects.order_by("created_at").prefetch_related("taxes"),
                ),
                "taxes",
            )
        )

    @extend_schema(operation_id="create_credit_note", request=CreditNoteCreateSerializer)
    def post(self, request):
        serializer = CreditNoteCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        credit_note = CreditNote.objects.create_draft(
            account=request.account,
            invoice=data["invoice"],
            number=data.get("number"),
            numbering_system=data.get("numbering_system"),
            reason=data.get("reason"),
            metadata=data.get("metadata"),
            description=data.get("description"),
            delivery_method=data.get("delivery_method"),
            recipients=data.get("recipients"),
        )

        serializer = CreditNoteSerializer(credit_note)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_credit_note"))
class CreditNoteRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = CreditNote.objects.none()
    serializer_class = CreditNoteSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return (
            CreditNote.objects.filter(account_id=self.request.account.id)
            .select_related(
                "invoice",
                "customer",
                "account",
                "invoice__customer_on_invoice",
                "invoice__customer_on_invoice__billing_address",
                "invoice__customer_on_invoice__shipping_address",
                "invoice__customer_on_invoice__logo",
                "invoice__account_on_invoice",
                "invoice__account_on_invoice__address",
                "invoice__account_on_invoice__logo",
                "customer__billing_address",
                "customer__shipping_address",
                "customer__logo",
                "account__address",
                "account__logo",
            )
            .prefetch_related(
                "customer__tax_ids",
                "account__tax_ids",
                "invoice__customer_on_invoice__tax_ids",
                "invoice__account_on_invoice__tax_ids",
                Prefetch(
                    "lines",
                    queryset=CreditNoteLine.objects.order_by("created_at").prefetch_related("taxes"),
                ),
                "taxes",
            )
        )

    @extend_schema(operation_id="update_credit_note", request=CreditNoteUpdateSerializer)
    def put(self, request, **_):
        credit_note = self.get_object()
        serializer = CreditNoteUpdateSerializer(
            credit_note,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if credit_note.status != CreditNoteStatus.DRAFT:
            raise ValidationError("Cannot update issued credit note")

        credit_note.update(
            number=data.get("number", credit_note.number),
            numbering_system=data.get("numbering_system", credit_note.numbering_system),
            reason=data.get("reason", credit_note.reason),
            metadata=data.get("metadata", credit_note.metadata),
            description=data.get("description", credit_note.description),
            delivery_method=data.get("delivery_method", credit_note.delivery_method),
            recipients=data.get("recipients", credit_note.recipients),
        )

        serializer = CreditNoteSerializer(credit_note)
        return Response(serializer.data)

    @extend_schema(operation_id="delete_credit_note")
    def delete(self, *_, **__):
        credit_note = self.get_object()

        if credit_note.status != CreditNoteStatus.DRAFT:
            raise ValidationError("Only draft credit notes can be deleted")

        credit_note.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class CreditNoteLineCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAccountMember]
    serializer_class = CreditNoteLineSerializer

    @extend_schema(
        operation_id="create_credit_note_line",
        request=CreditNoteLineCreateSerializer,
        responses={201: CreditNoteLineSerializer},
    )
    def post(self, request, **_):
        serializer = CreditNoteLineCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        invoice_line = data.get("invoice_line")
        if invoice_line is not None:
            line = CreditNoteLine.objects.from_invoice_line(
                credit_note=data["credit_note"],
                invoice_line=invoice_line,
                quantity=data.get("quantity"),
                amount=data.get("amount"),
                amounts=data.get("calculated_amounts"),
            )
        else:
            line = CreditNoteLine.objects.create_line(
                credit_note=data["credit_note"],
                description=data.get("description"),
                quantity=data.get("quantity"),
                unit_amount=data.get("unit_amount"),
            )

        serializer = CreditNoteLineSerializer(line)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CreditNoteLineUpdateDestroyAPIView(generics.GenericAPIView):
    queryset = CreditNoteLine.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]
    serializer_class = CreditNoteLineSerializer

    def get_queryset(self):
        return CreditNoteLine.objects.filter(
            credit_note__account_id=self.request.account.id,
        ).prefetch_related("taxes")

    @extend_schema(
        operation_id="update_credit_note_line",
        request=CreditNoteLineUpdateSerializer,
        responses={200: CreditNoteLineSerializer},
    )
    def put(self, request, **_):
        line = self.get_object()
        serializer = CreditNoteLineUpdateSerializer(line, data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if line.credit_note.status != CreditNoteStatus.DRAFT:
            raise ValidationError("Cannot modify issued credit note")

        line.update(
            quantity=data.get("quantity"),
            description=data.get("description"),
            unit_amount=data.get("unit_amount"),
            amount=data.get("amount"),
            amounts=data.get("calculated_amounts"),
        )

        serializer = CreditNoteLineSerializer(line)
        return Response(serializer.data)

    @extend_schema(operation_id="delete_credit_note_line", request=None, responses={204: None})
    def delete(self, *_, **__):
        line = self.get_object()
        credit_note = line.credit_note

        if credit_note.status != CreditNoteStatus.DRAFT:
            raise ValidationError("Cannot modify issued credit note")

        line.delete()
        credit_note.recalculate()

        return Response(status=status.HTTP_204_NO_CONTENT)


class CreditNoteLineTaxCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAccountMember]
    serializer_class = CreditNoteLineSerializer

    @extend_schema(
        operation_id="create_credit_note_line_tax",
        request=CreditNoteLineTaxCreateSerializer,
        responses={201: CreditNoteLineSerializer},
    )
    def post(self, request, line_id, **_):
        line = get_object_or_404(
            CreditNoteLine.objects.prefetch_related("taxes").filter(credit_note__account_id=request.account.id),
            id=line_id,
        )
        context = {"line": line, **self.get_serializer_context()}
        serializer = CreditNoteLineTaxCreateSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)

        if line.credit_note.status != CreditNoteStatus.DRAFT:
            raise ValidationError("Cannot modify issued credit note")

        if line.invoice_line_id:
            raise ValidationError("Manual taxes can only be managed for custom lines")

        line.add_tax(tax_rate=serializer.validated_data["tax_rate"])
        line.refresh_from_db()

        serializer = CreditNoteLineSerializer(line)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CreditNoteLineTaxDestroyAPIView(generics.GenericAPIView):
    queryset = CreditNoteTax.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]
    serializer_class = CreditNoteLineSerializer

    def get_queryset(self):
        return (
            CreditNoteTax.objects.filter(
                credit_note__account_id=self.request.account.id,
                credit_note_line__isnull=False,  # TODO: instead of filtering raise validation error0
            )
            .select_related("credit_note", "credit_note_line")
            .prefetch_related("credit_note_line__taxes")
        )

    @extend_schema(operation_id="delete_credit_note_line_tax", request=None, responses={204: None})
    def delete(self, *_, **__):
        tax = self.get_object()
        credit_note = tax.credit_note
        line = tax.credit_note_line

        if credit_note.status != CreditNoteStatus.DRAFT:
            raise ValidationError("Cannot modify issued credit note")

        if line is None or line.invoice_line_id:
            raise ValidationError("Manual taxes can only be managed for custom lines")

        tax.delete()
        line.recalculate()
        credit_note.recalculate()

        return Response(status=status.HTTP_204_NO_CONTENT)


class CreditNoteIssueAPIView(generics.GenericAPIView):
    queryset = CreditNote.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]
    serializer_class = CreditNoteIssueSerializer

    def get_queryset(self):
        return CreditNote.objects.filter(account_id=self.request.account.id)

    @extend_schema(
        operation_id="issue_credit_note",
        request=CreditNoteIssueSerializer,
        responses={200: CreditNoteSerializer},
    )
    def post(self, request, **_):
        credit_note = self.get_object()
        serializer = CreditNoteIssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if credit_note.status != CreditNoteStatus.DRAFT:
            raise ValidationError("Credit note already issued")

        if credit_note.effective_number is None:
            raise ValidationError("Credit note number is required before issuing")

        if not credit_note.lines.exists():
            raise ValidationError("Credit note must contain at least one line")

        credit_note.issue(issue_date=serializer.validated_data.get("issue_date", credit_note.issue_date))

        if credit_note.delivery_method == CreditNoteDeliveryMethod.AUTOMATIC and len(credit_note.recipients) > 0:
            send_credit_note(credit_note=credit_note)

        serializer = CreditNoteSerializer(credit_note)
        return Response(serializer.data)


class CreditNoteVoidAPIView(generics.GenericAPIView):
    queryset = CreditNote.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]
    serializer_class = CreditNoteVoidSerializer

    def get_queryset(self):
        return CreditNote.objects.filter(account_id=self.request.account.id)

    @extend_schema(
        operation_id="void_credit_note",
        request=CreditNoteVoidSerializer,
        responses={200: CreditNoteSerializer},
    )
    def post(self, request, **_):
        credit_note = self.get_object()
        serializer = CreditNoteVoidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if credit_note.status == CreditNoteStatus.VOIDED:
            raise ValidationError("Credit note already voided")

        if credit_note.status == CreditNoteStatus.ISSUED and credit_note.invoice.status == InvoiceStatus.PAID:
            raise ValidationError("Cannot void credit note for paid invoice")

        credit_note.void()

        serializer = CreditNoteSerializer(credit_note)
        return Response(serializer.data)


class CreditNotePreviewAPIView(generics.GenericAPIView):
    queryset = CreditNote.objects.none()
    renderer_classes = [TemplateHTMLRenderer]
    filter_backends = []
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return (
            CreditNote.objects.filter(account_id=self.request.account.id)
            .select_related(
                "invoice",
                "customer",
                "account",
                "invoice__customer_on_invoice",
                "invoice__customer_on_invoice__billing_address",
                "invoice__customer_on_invoice__shipping_address",
                "invoice__customer_on_invoice__logo",
                "invoice__account_on_invoice",
                "invoice__account_on_invoice__address",
                "invoice__account_on_invoice__logo",
                "customer__billing_address",
                "customer__shipping_address",
                "customer__logo",
                "account__address",
                "account__logo",
            )
            .prefetch_related(
                "customer__tax_ids",
                "account__tax_ids",
                "invoice__customer_on_invoice__tax_ids",
                "invoice__account_on_invoice__tax_ids",
                Prefetch(
                    "lines",
                    queryset=CreditNoteLine.objects.order_by("created_at").prefetch_related("taxes"),
                ),
                Prefetch("taxes", queryset=CreditNoteTax.objects.order_by("created_at")),
            )
        )

    @extend_schema(
        operation_id="preview_credit_note",
        responses={(200, "text/html"): {"type": "string"}},
        parameters=[OpenApiParameter(name="format", type=str, enum=CreditNotePreviewFormat.values)],
    )
    def get(self, request, **_):
        credit_note = self.get_object()
        credit_note_format = request.query_params.get("format", CreditNotePreviewFormat.PDF)
        template_name = "credit_notes/pdf/classic.html"

        match credit_note_format:
            case CreditNotePreviewFormat.EMAIL:
                template_name = "credit_notes/email/credit_note_email_message.html"

        return Response(
            {"credit_note": credit_note, "include_fonts": True},
            template_name=template_name,
        )
