import structlog
from django.conf import settings
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from openinvoice.accounts.permissions import IsAccountMember
from openinvoice.comments.models import Comment
from openinvoice.comments.serializers import CommentCreateSerializer, CommentSerializer
from openinvoice.core.utils import numeric_overflow

from .choices import InvoiceDeliveryMethod, InvoicePreviewFormat, InvoiceStatus
from .filtersets import InvoiceFilterSet
from .mail import send_invoice
from .models import Invoice, InvoiceDocument, InvoiceLine
from .pdf import render_invoice_documents
from .permissions import MaxInvoicesLimit
from .serializers import (
    InvoiceCreateSerializer,
    InvoiceDocumentCreateSerializer,
    InvoiceDocumentSerializer,
    InvoiceDocumentUpdateSerializer,
    InvoiceLineCreateSerializer,
    InvoiceLineSerializer,
    InvoiceLineUpdateSerializer,
    InvoiceRevisionCreateSerializer,
    InvoiceSerializer,
    InvoiceUpdateSerializer,
)

logger = structlog.get_logger(__name__)


@extend_schema_view(list=extend_schema(operation_id="list_invoices"))
class InvoiceListCreateAPIView(generics.ListAPIView):
    queryset = Invoice.objects.none()
    serializer_class = InvoiceSerializer
    filterset_class = InvoiceFilterSet
    search_fields = [
        "number",
        "billing_profile__name",
        "billing_profile__email",
        "lines__description",
    ]
    ordering_fields = ["created_at", "issue_date", "due_date"]
    permission_classes = [IsAuthenticated, IsAccountMember, MaxInvoicesLimit]

    def get_queryset(self):
        return Invoice.objects.for_account(self.request.account).eager_load()

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
            billing_profile=data.get("billing_profile"),
            business_profile=data.get("business_profile"),
            number=data.get("number"),
            numbering_system=data.get("numbering_system"),
            currency=data.get("currency"),
            issue_date=data.get("issue_date"),
            due_date=data.get("due_date"),
            net_payment_term=data.get("net_payment_term"),
            metadata=data.get("metadata"),
            payment_provider=data.get("payment_provider"),
            payment_connection_id=getattr(data.get("payment_connection"), "id", None),
            delivery_method=data.get("delivery_method"),
            recipients=data.get("recipients"),
            tax_behavior=data.get("tax_behavior"),
        )

        if "coupons" in data:
            invoice.set_coupons(data["coupons"])

        if "tax_rates" in data:
            invoice.set_tax_rates(data["tax_rates"])

        shipping = data.get("shipping")
        if shipping:
            invoice.add_shipping(
                shipping_rate=shipping["shipping_rate"],
                tax_rates=shipping.get("tax_rates", []),
                shipping_profile=shipping.get("profile"),
            )

        with numeric_overflow():
            invoice.recalculate()

        logger.info(
            "Invoice created",
            invoice_id=invoice.id,
            customer_id=invoice.customer_id,
        )

        invoice = self.get_queryset().get(id=invoice.id)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_invoice"))
class InvoiceRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = Invoice.objects.none()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Invoice.objects.for_account(self.request.account).eager_load()

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
            billing_profile=data.get("billing_profile", invoice.billing_profile),
            business_profile=data.get("business_profile", invoice.business_profile),
            number=data.get("number", invoice.number),
            numbering_system=data.get("numbering_system", invoice.numbering_system),
            currency=data.get("currency", invoice.currency),
            issue_date=data.get("issue_date", invoice.issue_date),
            due_date=data.get("due_date", invoice.due_date),
            net_payment_term=data.get("net_payment_term", invoice.net_payment_term),
            metadata=data.get("metadata", invoice.metadata),
            payment_provider=data.get("payment_provider", invoice.payment_provider),
            payment_connection_id=getattr(data.get("payment_connection"), "id", invoice.payment_connection_id),
            delivery_method=data.get("delivery_method", invoice.delivery_method),
            recipients=data.get("recipients", invoice.recipients),
            tax_behavior=data.get("tax_behavior", invoice.tax_behavior),
        )

        if "coupons" in data:
            invoice.set_coupons(data["coupons"])

        if "tax_rates" in data:
            invoice.set_tax_rates(data["tax_rates"])

        if "shipping" in data:
            shipping = data.get("shipping")

            if invoice.shipping is not None:
                invoice.shipping.delete()
                invoice.refresh_from_db()

            if shipping is not None:
                invoice.add_shipping(
                    shipping_rate=shipping["shipping_rate"],
                    tax_rates=shipping.get("tax_rates", []),
                    shipping_profile=shipping.get("profile"),
                )

        with numeric_overflow():
            invoice.recalculate()

        logger.info("Invoice updated", invoice_id=invoice.id, customer_id=invoice.customer_id)

        invoice = self.get_object()
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
        return Invoice.objects.for_account(self.request.account).eager_load()

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
            billing_profile=data.get("billing_profile"),
            business_profile=data.get("business_profile"),
            number=data.get("number"),
            numbering_system=data.get("numbering_system"),
            currency=data.get("currency"),
            issue_date=data.get("issue_date"),
            due_date=data.get("due_date"),
            net_payment_term=data.get("net_payment_term"),
            metadata=data.get("metadata"),
            payment_provider=data.get("payment_provider"),
            payment_connection_id=getattr(data.get("payment_connection"), "id", None),
            delivery_method=data.get("delivery_method"),
            recipients=data.get("recipients"),
            tax_behavior=data.get("tax_behavior"),
        )

        if "coupons" in data:
            invoice.set_coupons(data["coupons"])

        if "tax_rates" in data:
            invoice.set_tax_rates(data["tax_rates"])

        shipping = data.get("shipping")
        if shipping:
            if invoice.shipping is not None:
                invoice.shipping.delete()
                invoice.refresh_from_db()

            invoice.add_shipping(
                shipping_rate=shipping["shipping_rate"],
                tax_rates=shipping.get("tax_rates", []),
                shipping_profile=shipping.get("profile"),
            )

        with numeric_overflow():
            invoice.recalculate()

        logger.info(
            "Invoice revision created",
            invoice_id=invoice.id,
            previous_revision_id=invoice.previous_revision_id,
        )

        invoice = self.get_queryset().get(id=invoice.id)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InvoiceCloneAPIView(generics.GenericAPIView):
    queryset = Invoice.objects.none()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAccountMember, MaxInvoicesLimit]

    def get_queryset(self):
        return Invoice.objects.for_account(self.request.account).eager_load()

    @extend_schema(
        operation_id="clone_invoice",
        request=None,
        responses={201: InvoiceSerializer},
    )
    def post(self, *_, **__):
        invoice = self.get_object()
        new_invoice = Invoice.objects.clone_invoice(invoice)

        with numeric_overflow():
            new_invoice.recalculate()

        logger.info(
            "Invoice cloned",
            invoice_id=invoice.id,
            new_invoice_id=new_invoice.id,
        )

        serializer = InvoiceSerializer(new_invoice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InvoiceVoidAPIView(generics.GenericAPIView):
    queryset = Invoice.objects.none()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Invoice.objects.for_account(self.request.account).eager_load()

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

        invoice = self.get_object()
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data)


class InvoiceFinalizeAPIView(generics.GenericAPIView):
    queryset = Invoice.objects.none()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Invoice.objects.for_account(self.request.account).eager_load()

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
        render_invoice_documents(invoice)

        if invoice.delivery_method == InvoiceDeliveryMethod.AUTOMATIC and len(invoice.recipients) > 0:
            send_invoice(invoice=invoice)
            logger.info(
                "Invoice delivered automatically",
                invoice_id=invoice.id,
                recipients=invoice.recipients,
            )

        logger.info("Invoice finalized", invoice_id=invoice.id)
        invoice = self.get_object()
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data)


class InvoicePreviewAPIView(generics.GenericAPIView):
    queryset = Invoice.objects.none()
    renderer_classes = [TemplateHTMLRenderer]
    filter_backends = []
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Invoice.objects.for_account(self.request.account).eager_load()

    @extend_schema(
        operation_id="preview_invoice",
        responses={(200, "text/html"): {"type": "string"}},
        parameters=[OpenApiParameter(name="format", type=str, enum=InvoicePreviewFormat.values)],
    )
    def get(self, request, **_):
        invoice = self.get_object()
        language = request.query_params.get("language")
        invoice_format = request.query_params.get("format", InvoicePreviewFormat.PDF)
        template_name = "invoices/pdf/classic.html"

        document = None
        if invoice_format == InvoicePreviewFormat.PDF:
            documents = invoice.documents.order_by("created_at")
            if language:
                documents = documents.filter(language=language)

            document = documents.first()
            if not document:
                raise NotFound("Invoice has no customer documents")

        match invoice_format:
            case InvoicePreviewFormat.EMAIL:
                template_name = "invoices/email/invoice_email_message.html"

        return Response(
            {
                "invoice": invoice,
                "document": document,
            },
            template_name=template_name,
        )


@extend_schema_view(list=extend_schema(operation_id="list_invoice_documents"))
class InvoiceDocumentListCreateAPIView(generics.ListAPIView):
    queryset = InvoiceDocument.objects.none()
    serializer_class = InvoiceDocumentSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        invoice = get_object_or_404(Invoice.objects.for_account(self.request.account), id=self.kwargs["invoice_id"])
        return InvoiceDocument.objects.filter(invoice=invoice).select_related("file").order_by("created_at")

    @extend_schema(
        operation_id="create_invoice_document",
        request=InvoiceDocumentCreateSerializer,
        responses={201: InvoiceDocumentSerializer},
    )
    def post(self, request, **_):
        invoice = get_object_or_404(Invoice.objects.for_account(self.request.account), id=self.kwargs["invoice_id"])

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be modified")

        serializer = InvoiceDocumentCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        document = InvoiceDocument.objects.create_document(
            invoice=invoice,
            audience=data.get("audience"),
            language=data["language"],
            footer=data.get("footer"),
            memo=data.get("memo"),
            custom_fields=data.get("custom_fields"),
        )

        logger.info(
            "Invoice document created",
            invoice_id=invoice.id,
            document_id=document.id,
        )

        serializer = self.get_serializer(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InvoiceDocumentRetrieveUpdateDestroyAPIView(generics.GenericAPIView):
    queryset = InvoiceDocument.objects.none()
    serializer_class = InvoiceDocumentSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        invoice = get_object_or_404(Invoice.objects.for_account(self.request.account), id=self.kwargs["invoice_id"])
        return InvoiceDocument.objects.filter(invoice=invoice)

    @extend_schema(
        operation_id="update_invoice_document",
        request=InvoiceDocumentUpdateSerializer,
        responses={200: InvoiceDocumentSerializer},
    )
    def put(self, request, **_):
        document = self.get_object()

        if document.invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be modified")

        serializer = InvoiceDocumentUpdateSerializer(document, data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        document.update(
            language=data.get("language", document.language),
            audience=data.get("audience", document.audience),
            footer=data.get("footer", document.footer),
            memo=data.get("memo", document.memo),
            custom_fields=data.get("custom_fields", document.custom_fields),
        )

        logger.info(
            "Invoice document updated",
            invoice_id=document.invoice_id,
            document_id=document.id,
        )

        serializer = self.get_serializer(document)
        return Response(serializer.data)

    @extend_schema(operation_id="delete_invoice_document", request=None, responses={204: None})
    def delete(self, *_, **__):
        document = self.get_object()
        invoice = document.invoice

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Only draft invoices can be modified")

        document.delete()
        logger.info("Invoice document deleted", invoice_id=invoice.id, document_id=document.id)

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(list=extend_schema(operation_id="list_invoice_comments"))
class InvoiceCommentsListCreateAPIView(generics.ListAPIView):
    queryset = Comment.objects.none()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        get_object_or_404(Invoice.objects.for_account(self.request.account), id=self.kwargs["invoice_id"])
        return (
            Comment.objects.filter(
                invoices__id=self.kwargs["invoice_id"],
                invoices__account=self.request.account,
            )
            .select_related("author", "author__avatar")
            .order_by("created_at")
        )

    @extend_schema(
        operation_id="create_invoice_comment",
        request=CommentCreateSerializer,
        responses={201: CommentSerializer},
    )
    def post(self, request, *_, **__):
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice = get_object_or_404(Invoice.objects.for_account(self.request.account), id=self.kwargs["invoice_id"])

        comment = invoice.comments.create_comment(
            author=request.user,
            content=serializer.data["content"],
            visibility=serializer.data["visibility"],
        )
        logger.info("Invoice comment created", comment_id=comment.id, invoice_id=invoice.id)

        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InvoiceCommentDestroyAPIView(generics.DestroyAPIView):
    queryset = Comment.objects.none()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Comment.objects.filter(
            invoices__id=self.kwargs["invoice_id"],
            invoices__account=self.request.account,
        )

    @extend_schema(operation_id="delete_invoice_comment", request=None, responses={204: None})
    def delete(self, *_, **__):
        comment = self.get_object()

        comment.delete()
        logger.info("Invoice comment deleted", comment_id=comment.id, invoice_id=self.kwargs["invoice_id"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class InvoiceLineCreateAPIView(generics.GenericAPIView):
    serializer_class = InvoiceLineSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return InvoiceLine.objects.for_account(self.request.account).eager_load()

    @extend_schema(
        operation_id="create_invoice_line",
        request=InvoiceLineCreateSerializer,
        responses={201: InvoiceLineSerializer},
    )
    def post(self, request):
        serializer = InvoiceLineCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        invoice = data["invoice"]
        invoice_line = InvoiceLine.objects.create_line(
            invoice=invoice,
            description=data["description"],
            quantity=data["quantity"],
            unit_amount=data.get("unit_amount"),
            price=data.get("price"),
        )

        if "coupons" in data:
            invoice_line.set_coupons(data["coupons"])

        if "tax_rates" in data:
            invoice_line.set_tax_rates(data["tax_rates"])

        with numeric_overflow():
            invoice.recalculate()

        invoice_line.refresh_from_db()

        logger.info(
            "Invoice line created",
            invoice_line_id=invoice_line.id,
            invoice_id=invoice.id,
        )

        invoice_line = self.get_queryset().get(id=invoice_line.id)
        serializer = InvoiceLineSerializer(invoice_line)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InvoiceLineUpdateDestroyAPIView(generics.GenericAPIView):
    queryset = InvoiceLine.objects.none()
    serializer_class = InvoiceLineSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return InvoiceLine.objects.for_account(self.request.account).eager_load()

    @extend_schema(
        operation_id="update_invoice_line",
        request=InvoiceLineUpdateSerializer,
        responses={200: InvoiceLineSerializer},
    )
    def put(self, request, **_):
        invoice_line = self.get_object()
        invoice = invoice_line.invoice
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

        if "coupons" in data:
            invoice_line.set_coupons(data["coupons"])

        if "tax_rates" in data:
            invoice_line.set_tax_rates(data["tax_rates"])

        with numeric_overflow():
            invoice.recalculate()

        logger.info(
            "Invoice line updated",
            invoice_line_id=invoice_line.id,
            invoice_id=invoice.id,
        )
        invoice_line = self.get_object()
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

        with numeric_overflow():
            invoice.recalculate()

        logger.info("Invoice line deleted", invoice_line_id=pk, invoice_id=invoice.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
