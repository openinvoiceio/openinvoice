import structlog
from django.conf import settings
from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember

from .enums import InvoiceDeliveryMethod, InvoicePreviewFormat, InvoiceStatus
from .filters import InvoiceFilter
from .mail import send_invoice
from .models import Invoice, InvoiceDiscount, InvoiceLine, InvoiceTax
from .permissions import MaxInvoicesLimit
from .serializers import (
    InvoiceCreateSerializer,
    InvoiceDiscountCreateSerializer,
    InvoiceDiscountSerializer,
    InvoiceLineCreateSerializer,
    InvoiceLineDiscountCreateSerializer,
    InvoiceLineDiscountSerializer,
    InvoiceLineSerializer,
    InvoiceLineTaxCreateSerializer,
    InvoiceLineTaxSerializer,
    InvoiceLineUpdateSerializer,
    InvoiceRevisionCreateSerializer,
    InvoiceSerializer,
    InvoiceTaxCreateSerializer,
    InvoiceTaxSerializer,
    InvoiceUpdateSerializer,
)

logger = structlog.get_logger(__name__)


@extend_schema_view(list=extend_schema(operation_id="list_invoices"))
class InvoiceListCreateAPIView(generics.ListAPIView):
    queryset = Invoice.objects.none()
    serializer_class = InvoiceSerializer
    filterset_class = InvoiceFilter
    search_fields = [
        "number",
        "customer__name",
        "customer__email",
        "customer_on_invoice__name",
        "customer_on_invoice__email",
        "description",
        "lines__description",
    ]
    ordering_fields = ["created_at", "issue_date", "due_date"]
    permission_classes = [IsAuthenticated, IsAccountMember, MaxInvoicesLimit]

    def get_queryset(self):
        return (
            Invoice.objects.filter(account_id=self.request.account.id)
            .prefetch_related(
                Prefetch(
                    "lines",
                    queryset=InvoiceLine.objects.order_by("created_at").prefetch_related("discounts", "taxes"),
                ),
            )
            .select_related("previous_revision")
        )

    @extend_schema(
        operation_id="create_invoice",
        request=InvoiceCreateSerializer,
        responses={201: InvoiceSerializer},
    )
    def post(self, request):
        serializer = InvoiceCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        invoice = Invoice.objects.create_draft(
            account=request.account,
            customer=data["customer"],
            number=data.get("number"),
            numbering_system=data.get("numbering_system"),
            currency=data.get("currency"),
            issue_date=data.get("issue_date"),
            sell_date=data.get("sell_date"),
            due_date=data.get("due_date"),
            net_payment_term=data.get("net_payment_term"),
            metadata=data.get("metadata"),
            custom_fields=data.get("custom_fields"),
            footer=data.get("footer"),
            description=data.get("description"),
            payment_provider=data.get("payment_provider"),
            payment_connection_id=getattr(data.get("payment_connection"), "id", None),
            delivery_method=data.get("delivery_method"),
            recipients=data.get("recipients"),
        )

        shipping = data.get("shipping")
        if shipping:
            invoice.add_shipping(
                shipping_rate=shipping["shipping_rate"],
                tax_rates=shipping.get("tax_rates", []),
            )

        logger.info(
            "Invoice created",
            invoice_id=invoice.id,
            customer_id=invoice.customer_id,
        )

        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_invoice"))
class InvoiceRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = Invoice.objects.none()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return (
            Invoice.objects.filter(account_id=self.request.account.id)
            .prefetch_related(
                Prefetch(
                    "lines",
                    queryset=InvoiceLine.objects.order_by("created_at").prefetch_related("discounts", "taxes"),
                ),
            )
            .select_related("previous_revision")
        )

    @extend_schema(
        operation_id="update_invoice",
        request=InvoiceUpdateSerializer,
        responses={200: InvoiceSerializer},
    )
    def put(self, request, **_):
        invoice = self.get_object()
        serializer = InvoiceUpdateSerializer(invoice, data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be updated")

        invoice.update(
            customer=data.get("customer", invoice.customer),
            number=data.get("number", invoice.number),
            numbering_system=data.get("numbering_system", invoice.numbering_system),
            currency=data.get("currency", invoice.currency),
            issue_date=data.get("issue_date", invoice.issue_date),
            sell_date=data.get("sell_date", invoice.sell_date),
            due_date=data.get("due_date", invoice.due_date),
            net_payment_term=data.get("net_payment_term", invoice.net_payment_term),
            metadata=data.get("metadata", invoice.metadata),
            custom_fields=data.get("custom_fields", invoice.custom_fields),
            footer=data.get("footer", invoice.footer),
            description=data.get("description", invoice.description),
            payment_provider=data.get("payment_provider", invoice.payment_provider),
            payment_connection_id=getattr(data.get("payment_connection"), "id", invoice.payment_connection_id),
            delivery_method=data.get("delivery_method", invoice.delivery_method),
            recipients=data.get("recipients", invoice.recipients),
        )

        if "shipping" in data:
            shipping = data.get("shipping")

            if invoice.shipping is not None:
                invoice.shipping.delete()
                invoice.refresh_from_db()
                invoice.recalculate()

            if shipping is not None:
                invoice.add_shipping(
                    shipping_rate=shipping["shipping_rate"],
                    tax_rates=shipping.get("tax_rates", []),
                )

        logger.info("Invoice updated", invoice_id=invoice.id, customer_id=invoice.customer_id)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data)

    @extend_schema(
        operation_id="delete_invoice",
        request=None,
        responses={204: None},
    )
    def delete(self, _, **__):
        invoice = self.get_object()

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be deleted")

        head = invoice.head
        is_root = head.root_id == invoice.id
        is_current = head.current_id == invoice.id

        if is_root:
            head.root = None
        if is_current:
            head.current = None
        if is_root or is_current:
            head.save()

        invoice.delete()

        if not head.revisions.exists():
            head.delete()

        logger.info("Invoice deleted", invoice_id=invoice.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvoiceRevisionsListCreateAPIView(generics.GenericAPIView):
    queryset = Invoice.objects.none()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAccountMember, MaxInvoicesLimit]

    def get_queryset(self):
        return (
            Invoice.objects.filter(account_id=self.request.account.id)
            .prefetch_related(
                Prefetch(
                    "lines",
                    queryset=InvoiceLine.objects.order_by("created_at").prefetch_related("discounts", "taxes"),
                )
            )
            .select_related("previous_revision")
        )

    @extend_schema(
        operation_id="list_invoice_revisions",
        responses={200: InvoiceSerializer(many=True)},
    )
    def get(self, _, **__):
        invoice = self.get_object()
        revisions = Invoice.objects.revisions(head_id=invoice.head_id)
        serializer = InvoiceSerializer(revisions, many=True)
        return Response(serializer.data)

    @extend_schema(
        operation_id="create_invoice_revision",
        request=InvoiceRevisionCreateSerializer,
        responses={201: InvoiceSerializer},
    )
    def post(self, request, **_):
        prevision_revision = self.get_object()
        serializer = InvoiceRevisionCreateSerializer(
            prevision_revision, data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if prevision_revision.status not in [InvoiceStatus.OPEN, InvoiceStatus.VOIDED]:
            raise ValidationError("Only open and voided invoices can be revised")

        if Invoice.objects.filter(previous_revision=prevision_revision).exists():
            raise ValidationError("Invoice already has a subsequent revision")

        if prevision_revision.head.revisions.count() > settings.MAX_REVISIONS_PER_INVOICE:
            raise ValidationError("Maximum number of invoice revisions reached")

        invoice = Invoice.objects.create_revision(
            account=request.account,
            previous_revision=prevision_revision,
            number=data.get("number"),
            numbering_system=data.get("numbering_system"),
            currency=data.get("currency"),
            issue_date=data.get("issue_date"),
            sell_date=data.get("sell_date"),
            due_date=data.get("due_date"),
            net_payment_term=data.get("net_payment_term"),
            metadata=data.get("metadata"),
            custom_fields=data.get("custom_fields"),
            footer=data.get("footer"),
            description=data.get("description"),
            payment_provider=data.get("payment_provider"),
            payment_connection_id=getattr(data.get("payment_connection"), "id", None),
            delivery_method=data.get("delivery_method"),
            recipients=data.get("recipients"),
        )

        # TODO: add shipping

        logger.info(
            "Invoice revision created",
            invoice_id=invoice.id,
            previous_revision_id=invoice.previous_revision_id,
        )

        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InvoiceVoidAPIView(generics.GenericAPIView):
    queryset = Invoice.objects.none()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return (
            Invoice.objects.filter(account_id=self.request.account.id)
            .prefetch_related(
                Prefetch(
                    "lines",
                    queryset=InvoiceLine.objects.order_by("created_at").prefetch_related("discounts", "taxes"),
                )
            )
            .select_related("previous_revision")
        )

    @extend_schema(
        operation_id="void_invoice",
        request=None,
        responses={200: InvoiceSerializer},
    )
    def post(self, _, **__):
        invoice = self.get_object()

        if invoice.status != InvoiceStatus.OPEN:
            raise ValidationError("Only open invoices can be voided")

        invoice.void()

        logger.info("Invoice voided", invoice_id=invoice.id)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data)


class InvoiceFinalizeAPIView(generics.GenericAPIView):
    queryset = Invoice.objects.none()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return (
            Invoice.objects.filter(account_id=self.request.account.id)
            .prefetch_related(
                Prefetch(
                    "lines",
                    queryset=InvoiceLine.objects.order_by("created_at").prefetch_related("discounts", "taxes"),
                )
            )
            .select_related("previous_revision")
        )

    @extend_schema(
        operation_id="finalize_invoice",
        request=None,
        responses={200: InvoiceSerializer},
    )
    def post(self, _, **__):
        invoice = self.get_object()

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be finalized")

        if invoice.effective_number is None:
            raise ValidationError("Invoice number or numbering system is missing")

        invoice.finalize()

        if invoice.delivery_method == InvoiceDeliveryMethod.AUTOMATIC and len(invoice.recipients) > 0:
            send_invoice(invoice=invoice)
            logger.info(
                "Invoice delivered automatically",
                invoice_id=invoice.id,
                recipients=invoice.recipients,
            )

        logger.info("Invoice finalized", invoice_id=invoice.id, pdf_id=invoice.pdf_id)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data)


class InvoicePreviewAPIView(generics.GenericAPIView):
    queryset = Invoice.objects.none()
    renderer_classes = [TemplateHTMLRenderer]
    filter_backends = []
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return (
            Invoice.objects.filter(account_id=self.request.account.id)
            .prefetch_related(
                Prefetch(
                    "lines",
                    queryset=InvoiceLine.objects.order_by("created_at").prefetch_related("discounts", "taxes"),
                )
            )
            .select_related("previous_revision")
        )

    @extend_schema(
        operation_id="preview_invoice",
        responses={(200, "text/html"): {"type": "string"}},
        parameters=[OpenApiParameter(name="format", type=str, enum=InvoicePreviewFormat.values)],
    )
    def get(self, request, **_):
        invoice = self.get_object()
        invoice_format = request.query_params.get("format", InvoicePreviewFormat.PDF)
        template_name = "invoices/pdf/classic.html"

        match invoice_format:
            case InvoicePreviewFormat.EMAIL:
                template_name = "invoices/email/invoice_email_message.html"

        return Response(
            {"invoice": invoice, "include_fonts": True},
            template_name=template_name,
        )


class InvoiceLineCreateAPIView(generics.GenericAPIView):
    serializer_class = InvoiceLineSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    @extend_schema(
        operation_id="create_invoice_line",
        request=InvoiceLineCreateSerializer,
        responses={200: InvoiceLineSerializer},
    )
    def post(self, request):
        serializer = InvoiceLineCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        invoice_line = InvoiceLine.objects.create_line(
            invoice=data["invoice"],
            description=data["description"],
            quantity=data["quantity"],
            unit_amount=data.get("unit_amount"),
            price=data.get("price"),
        )

        logger.info(
            "Invoice line created",
            invoice_line_id=invoice_line.id,
            invoice_id=invoice_line.invoice_id,
        )
        serializer = InvoiceLineSerializer(invoice_line)
        return Response(serializer.data)


class InvoiceLineUpdateDestroyAPIView(generics.GenericAPIView):
    queryset = InvoiceLine.objects.none()
    serializer_class = InvoiceLineSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return InvoiceLine.objects.filter(invoice__account_id=self.request.account.id)

    @extend_schema(
        operation_id="update_invoice_line",
        request=InvoiceLineUpdateSerializer,
        responses={200: InvoiceLineSerializer},
    )
    def put(self, request, **_):
        invoice_line = self.get_object()
        serializer = InvoiceLineUpdateSerializer(invoice_line, data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if invoice_line.invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be modified")

        invoice_line.update(
            description=data.get("description", invoice_line.description),
            quantity=data.get("quantity", invoice_line.quantity),
            unit_amount=data.get("unit_amount", invoice_line.unit_amount),
            price=data.get("price", invoice_line.price),
        )

        logger.info(
            "Invoice line updated",
            invoice_line_id=invoice_line.id,
            invoice_id=invoice_line.invoice_id,
        )
        serializer = InvoiceLineSerializer(invoice_line)
        return Response(serializer.data)

    @extend_schema(
        operation_id="delete_invoice_line",
        request=None,
        responses={204: None},
    )
    def delete(self, _, pk, **__):
        invoice_line = self.get_object()
        invoice = invoice_line.invoice

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be modified")

        invoice_line.delete()
        invoice.recalculate()

        logger.info("Invoice line deleted", invoice_line_id=pk, invoice_id=invoice.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvoiceLineDiscountCreateAPIView(generics.GenericAPIView):
    serializer_class = InvoiceLineDiscountSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    @extend_schema(
        operation_id="apply_invoice_line_discount",
        request=InvoiceLineDiscountCreateSerializer,
        responses={200: InvoiceLineDiscountSerializer},
    )
    def post(self, request, pk):
        invoice_line = get_object_or_404(InvoiceLine, pk=pk, invoice__account_id=request.account.id)
        context = {"invoice_line": invoice_line, **self.get_serializer_context()}
        serializer = InvoiceLineDiscountCreateSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)

        if invoice_line.invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be modified")

        if invoice_line.discounts.count() >= settings.MAX_DISCOUNTS:
            raise ValidationError("Maximum number of invoice line discounts reached")

        discount = invoice_line.add_discount(coupon=serializer.validated_data["coupon"])

        logger.info(
            "Invoice line discount applied",
            invoice_line_discount=discount.id,
            invoice_line=invoice_line.id,
        )
        serializer = InvoiceLineDiscountSerializer(discount)
        return Response(serializer.data)


class InvoiceLineDiscountDestroyAPIView(generics.GenericAPIView):
    serializer_class = InvoiceLineDiscountSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return InvoiceDiscount.objects.filter(
            invoice_line__invoice__account_id=self.request.account.id,
            invoice_line_id=self.kwargs["invoice_line_id"],
        )

    @extend_schema(
        operation_id="delete_invoice_line_discount",
        responses={204: None},
    )
    def delete(self, *_, pk, invoice_line_id, **__):
        discount = self.get_object()
        invoice_line = discount.invoice_line

        if discount.invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be modified")

        discount.delete()
        invoice_line.recalculate()

        logger.info(
            "Invoice line discount deleted",
            invoice_line_discount_id=pk,
            invoice_line_id=invoice_line_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvoiceDiscountCreateAPIView(generics.GenericAPIView):
    serializer_class = InvoiceDiscountSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    @extend_schema(
        operation_id="apply_invoice_discount",
        request=InvoiceDiscountCreateSerializer,
        responses={200: InvoiceDiscountSerializer},
    )
    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk, account_id=request.account.id)
        context = {"invoice": invoice, **self.get_serializer_context()}
        serializer = InvoiceDiscountCreateSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be modified")

        if invoice.discounts.count() >= settings.MAX_DISCOUNTS:
            raise ValidationError("Maximum number of invoice discounts reached")

        discount = invoice.add_discount(coupon=serializer.validated_data["coupon"])

        logger.info(
            "Invoice discount applied",
            invoice_discount=discount.id,
            invoice=invoice.id,
        )
        serializer = InvoiceDiscountSerializer(discount)
        return Response(serializer.data)


class InvoiceDiscountDestroyAPIView(generics.GenericAPIView):
    serializer_class = InvoiceDiscountSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return InvoiceDiscount.objects.filter(
            invoice__account_id=self.request.account.id, invoice_id=self.kwargs["invoice_id"]
        )

    @extend_schema(
        operation_id="delete_invoice_discount",
        responses={204: None},
    )
    def delete(self, *_, pk, invoice_id, **__):
        discount = self.get_object()
        invoice = discount.invoice

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be modified")

        discount.delete()
        invoice.recalculate()

        logger.info(
            "Invoice discount deleted",
            invoice_discount=pk,
            invoice=invoice_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvoiceLineTaxCreateAPIView(generics.GenericAPIView):
    serializer_class = InvoiceLineTaxSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    @extend_schema(
        operation_id="apply_invoice_line_tax",
        request=InvoiceLineTaxCreateSerializer,
        responses={200: InvoiceLineTaxSerializer},
    )
    def post(self, request, pk):
        invoice_line = get_object_or_404(InvoiceLine, pk=pk, invoice__account_id=request.account.id)
        context = {"invoice_line": invoice_line, **self.get_serializer_context()}
        serializer = InvoiceLineTaxCreateSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)

        if invoice_line.invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be modified")

        if invoice_line.taxes.count() >= settings.MAX_TAXES:
            raise ValidationError("Maximum number of invoice line taxes reached")

        tax = invoice_line.add_tax(tax_rate=serializer.validated_data["tax_rate"])

        logger.info(
            "Invoice line tax applied",
            invoice_line_tax_id=tax.id,
            invoice_line_id=invoice_line.id,
        )
        serializer = InvoiceLineTaxSerializer(tax)
        return Response(serializer.data)


class InvoiceLineTaxDestroyAPIView(generics.GenericAPIView):
    serializer_class = InvoiceLineTaxSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return InvoiceTax.objects.filter(
            invoice_line__invoice__account_id=self.request.account.id,
            invoice_line_id=self.kwargs["invoice_line_id"],
        )

    @extend_schema(
        operation_id="delete_invoice_line_tax",
        responses={204: None},
    )
    def delete(self, *_, invoice_line_id, **__):
        tax = self.get_object()
        invoice_line = tax.invoice_line

        if tax.invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be modified")

        tax.delete()
        invoice_line.recalculate()

        logger.info(
            "Invoice line tax deleted",
            invoice_line_tax=tax.id,
            invoice_line=invoice_line_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvoiceTaxCreateAPIView(generics.GenericAPIView):
    serializer_class = InvoiceTaxSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    @extend_schema(
        operation_id="apply_invoice_tax",
        request=InvoiceTaxCreateSerializer,
        responses={200: InvoiceTaxSerializer},
    )
    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk, account_id=request.account.id)
        context = {"invoice": invoice, **self.get_serializer_context()}
        serializer = InvoiceTaxCreateSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be modified")

        if invoice.taxes.count() >= settings.MAX_TAXES:
            raise ValidationError("Maximum number of invoice taxes reached")

        tax = invoice.add_tax(tax_rate=serializer.validated_data["tax_rate"])

        logger.info(
            "Invoice tax applied",
            invoice_tax=tax.id,
            invoice=invoice.id,
        )
        serializer = InvoiceTaxSerializer(tax)
        return Response(serializer.data)


class InvoiceTaxDestroyAPIView(generics.GenericAPIView):
    serializer_class = InvoiceTaxSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return InvoiceTax.objects.filter(
            invoice__account_id=self.request.account.id, invoice_id=self.kwargs["invoice_id"]
        )

    @extend_schema(
        operation_id="delete_invoice_tax",
        responses={204: None},
    )
    def delete(self, *_, invoice_id, **__):
        tax = self.get_object()
        invoice = tax.invoice

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be modified")

        tax.delete()
        invoice.recalculate()

        logger.info(
            "Invoice tax deleted",
            invoice_tax=tax.id,
            invoice=invoice_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
