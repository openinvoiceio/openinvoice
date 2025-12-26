import structlog
from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember

from .enums import QuoteDeliveryMethod, QuotePreviewFormat, QuoteStatus
from .filters import QuoteFilter
from .mail import send_quote
from .models import Quote, QuoteDiscount, QuoteLine, QuoteTax
from .permissions import MaxQuotesLimit
from .serializers import (
    QuoteCreateSerializer,
    QuoteDiscountCreateSerializer,
    QuoteDiscountSerializer,
    QuoteLineCreateSerializer,
    QuoteLineDiscountCreateSerializer,
    QuoteLineDiscountSerializer,
    QuoteLineSerializer,
    QuoteLineTaxCreateSerializer,
    QuoteLineTaxSerializer,
    QuoteLineUpdateSerializer,
    QuotePreviewSerializer,
    QuoteSerializer,
    QuoteTaxCreateSerializer,
    QuoteTaxSerializer,
    QuoteUpdateSerializer,
)

logger = structlog.get_logger(__name__)


@extend_schema_view(list=extend_schema(operation_id="list_quotes"))
class QuoteListCreateAPIView(generics.ListAPIView):
    queryset = Quote.objects.none()
    serializer_class = QuoteSerializer
    filterset_class = QuoteFilter
    search_fields = [
        "number",
        "customer_on_quote__name",
        "customer_on_quote__email",
        "customer__name",
        "customer__email",
        "description",
        "lines__description",
    ]
    ordering_fields = ["created_at", "issue_date"]
    permission_classes = [IsAuthenticated, IsAccountMember, MaxQuotesLimit]

    def get_queryset(self):
        return (
            Quote.objects.filter(account_id=self.request.account.id)
            .prefetch_related(
                Prefetch(
                    "lines",
                    queryset=QuoteLine.objects.order_by("created_at").prefetch_related("discounts", "taxes"),
                )
            )
            .select_related("invoice", "customer", "customer_on_quote", "account_on_quote")
        )

    @extend_schema(operation_id="create_quote", request=QuoteCreateSerializer, responses={200: QuoteSerializer})
    def post(self, request):
        serializer = QuoteCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        quote = Quote.objects.create_draft(
            account=request.account,
            customer=data.get("customer"),
            number=data.get("number"),
            numbering_system=data.get("numbering_system"),
            currency=data.get("currency"),
            issue_date=data.get("issue_date"),
            metadata=data.get("metadata"),
            custom_fields=data.get("custom_fields"),
            footer=data.get("footer"),
            description=data.get("description"),
            delivery_method=data.get("delivery_method"),
            recipients=data.get("recipients"),
        )
        logger.info("Quote created", quote_id=quote.id, customer_id=quote.customer_id)

        response_serializer = QuoteSerializer(quote)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_quote"))
class QuoteRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = Quote.objects.none()
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return (
            Quote.objects.filter(account_id=self.request.account.id)
            .prefetch_related(
                Prefetch(
                    "lines",
                    queryset=QuoteLine.objects.order_by("created_at").prefetch_related("discounts", "taxes"),
                )
            )
            .select_related("invoice", "customer", "customer_on_quote", "account_on_quote")
        )

    @extend_schema(operation_id="update_quote", request=QuoteUpdateSerializer, responses={200: QuoteSerializer})
    def put(self, request, **_):
        quote = self.get_object()
        serializer = QuoteUpdateSerializer(quote, data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Only draft quotes can be updated")

        quote.update(
            customer=data.get("customer", quote.customer),
            number=data.get("number", quote.number),
            numbering_system=data.get("numbering_system", quote.numbering_system),
            currency=data.get("currency", quote.currency),
            issue_date=data.get("issue_date", quote.issue_date),
            metadata=data.get("metadata", quote.metadata),
            custom_fields=data.get("custom_fields", quote.custom_fields),
            footer=data.get("footer", quote.footer),
            description=data.get("description", quote.description),
            delivery_method=data.get("delivery_method", quote.delivery_method),
            recipients=data.get("recipients", quote.recipients),
        )

        logger.info("Quote updated", quote_id=quote.id, customer_id=quote.customer_id)
        response_serializer = QuoteSerializer(quote)
        return Response(response_serializer.data)

    @extend_schema(operation_id="delete_quote", request=None, responses={204: None})
    def delete(self, _, pk):
        quote = self.get_object()

        if quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Only draft quotes can be deleted")

        quote.delete()

        logger.info("Quote deleted", quote_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuoteFinalizeAPIView(generics.GenericAPIView):
    queryset = Quote.objects.none()
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Quote.objects.filter(account_id=self.request.account.id)

    @extend_schema(operation_id="finalize_quote", request=None, responses={200: QuoteSerializer})
    def post(self, _, quote_id: str):
        quote = get_object_or_404(self.get_queryset(), pk=quote_id)

        if quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Only draft quotes can be finalized")

        if not (quote.number or quote.numbering_system):
            raise ValidationError("Number or numbering system is required before finalizing a quote")

        quote.finalize()

        if quote.delivery_method == QuoteDeliveryMethod.AUTOMATIC and len(quote.recipients) > 0:
            send_quote(quote)

        logger.info("Quote finalized", quote_id=quote.id, customer_id=quote.customer_id)
        serializer = QuoteSerializer(quote)
        return Response(serializer.data)


class QuoteAcceptAPIView(generics.GenericAPIView):
    queryset = Quote.objects.none()
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Quote.objects.filter(account_id=self.request.account.id)

    @extend_schema(operation_id="accept_quote", request=None, responses={200: QuoteSerializer})
    def post(self, _, quote_id: str):
        quote = get_object_or_404(self.get_queryset(), pk=quote_id)

        if quote.status != QuoteStatus.OPEN:
            raise ValidationError("Only open quotes can be accepted")

        invoice = quote.accept()

        logger.info("Quote converted to invoice", quote_id=quote.id, invoice_id=invoice.id)
        serializer = QuoteSerializer(quote)
        return Response(serializer.data)


class QuoteCancelAPIView(generics.GenericAPIView):
    queryset = Quote.objects.none()
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Quote.objects.filter(account_id=self.request.account.id)

    @extend_schema(operation_id="cancel_quote", request=None, responses={200: QuoteSerializer})
    def post(self, _, quote_id: str):
        quote = get_object_or_404(self.get_queryset(), pk=quote_id)

        if quote.status == QuoteStatus.ACCEPTED:
            raise ValidationError("Accepted quotes cannot be canceled")

        if quote.status == QuoteStatus.CANCELED:
            raise ValidationError("Quote is already canceled")

        quote.cancel()

        logger.info("Quote canceled", quote_id=quote.id)
        serializer = QuoteSerializer(quote)
        return Response(serializer.data)


class QuotePreviewAPIView(generics.GenericAPIView):
    queryset = Quote.objects.none()
    serializer_class = QuotePreviewSerializer
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return (
            Quote.objects.filter(account_id=self.request.account.id)
            .select_related("account", "customer", "customer_on_quote", "account_on_quote")
            .prefetch_related("lines__discounts", "lines__taxes", "discounts", "taxes")
        )

    @extend_schema(
        operation_id="preview_quote",
        responses={(200, "text/html"): {"type": "string"}},
        parameters=[
            OpenApiParameter(name="format", required=False, type=str, enum=QuotePreviewFormat.values),
        ],
    )
    def get(self, request, quote_id: str):
        quote = get_object_or_404(self.get_queryset(), pk=quote_id)
        serializer = QuotePreviewSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        template_name = "quotes/pdf/classic.html"

        if data["format"] == QuotePreviewFormat.EMAIL:
            template_name = "quotes/email/quote_email_message.html"

        return Response({"quote": quote, "include_fonts": True}, template_name=template_name)


class QuoteLineCreateAPIView(generics.GenericAPIView):
    queryset = QuoteLine.objects.none()
    serializer_class = QuoteLineCreateSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    @extend_schema(
        operation_id="create_quote_line", request=QuoteLineCreateSerializer, responses={200: QuoteLineSerializer}
    )
    def post(self, request):
        serializer = QuoteLineCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        line = QuoteLine.objects.create_line(
            quote=data["quote"],
            description=data["description"],
            quantity=data["quantity"],
            unit_amount=data.get("unit_amount"),
            price=data.get("price"),
        )

        logger.info("Quote line created", quote_id=data["quote"].id, quote_line_id=line.id)
        response_serializer = QuoteLineSerializer(line)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class QuoteLineUpdateDestroyAPIView(generics.GenericAPIView):
    queryset = QuoteLine.objects.none()
    serializer_class = QuoteLineUpdateSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return QuoteLine.objects.filter(quote__account_id=self.request.account.id)

    @extend_schema(
        operation_id="update_quote_line", request=QuoteLineUpdateSerializer, responses={200: QuoteLineSerializer}
    )
    def put(self, request, quote_line_id: str):
        quote_line = get_object_or_404(self.get_queryset(), pk=quote_line_id)
        serializer = QuoteLineUpdateSerializer(quote_line, data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if quote_line.quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Only draft quotes can be modified")

        quote_line.update(
            description=data.get("description", quote_line.description),
            quantity=data.get("quantity", quote_line.quantity),
            unit_amount=data.get("unit_amount", quote_line.unit_amount),
            price=data.get("price", quote_line.price),
        )

        logger.info("Quote line updated", quote_id=quote_line.quote_id, quote_line_id=quote_line.id)
        serializer = QuoteLineSerializer(quote_line)
        return Response(serializer.data)

    @extend_schema(operation_id="delete_quote_line", request=None, responses={204: None})
    def delete(self, _, quote_line_id: str):
        quote_line = get_object_or_404(self.get_queryset(), pk=quote_line_id)
        quote = quote_line.quote

        if quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Only draft quotes can be modified")

        quote_line.delete()
        quote.recalculate()

        logger.info("Quote line deleted", quote_id=quote.id, quote_line_id=quote_line_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuoteLineDiscountCreateAPIView(generics.GenericAPIView):
    queryset = QuoteLine.objects.none()
    serializer_class = QuoteLineDiscountCreateSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return QuoteLine.objects.filter(quote__account_id=self.request.account.id)

    @extend_schema(
        operation_id="add_quote_line_discount",
        request=QuoteLineDiscountCreateSerializer,
        responses={200: QuoteLineDiscountSerializer},
    )
    def post(self, request, quote_line_id: str):
        quote_line = get_object_or_404(self.get_queryset(), pk=quote_line_id)

        if quote_line.quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Only draft quotes can be modified")

        serializer = QuoteLineDiscountCreateSerializer(
            data=request.data, context={"quote_line": quote_line, **self.get_serializer_context()}
        )
        serializer.is_valid(raise_exception=True)
        discount = quote_line.add_discount(serializer.validated_data["coupon"])

        logger.info(
            "Quote line discount added",
            quote_id=quote_line.quote_id,
            quote_line_id=quote_line.id,
            discount_id=discount.id,
        )
        serializer = QuoteLineDiscountSerializer(discount)
        return Response(serializer.data)


class QuoteLineDiscountDestroyAPIView(generics.GenericAPIView):
    queryset = QuoteDiscount.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return QuoteDiscount.objects.filter(quote__account_id=self.request.account.id)

    @extend_schema(operation_id="remove_quote_line_discount", request=None, responses={204: None})
    def delete(self, _, quote_line_discount_id: str, quote_line_id: str):
        discount = get_object_or_404(self.get_queryset(), pk=quote_line_discount_id)
        quote_line = discount.quote_line

        if discount.quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Only draft quotes can be modified")

        discount.delete()
        quote_line.recalculate()

        logger.info(
            "Quote line discount removed",
            quote_id=quote_line.quote_id,
            quote_line_id=quote_line_id,
            discount_id=quote_line_discount_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuoteDiscountCreateAPIView(generics.GenericAPIView):
    queryset = Quote.objects.none()
    serializer_class = QuoteDiscountCreateSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Quote.objects.filter(account_id=self.request.account.id).select_related("customer")

    @extend_schema(
        operation_id="add_quote_discount",
        request=QuoteDiscountCreateSerializer,
        responses={200: QuoteDiscountSerializer},
    )
    def post(self, request, quote_id: str):
        quote = get_object_or_404(self.get_queryset(), pk=quote_id)

        if quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Only draft quotes can be modified")

        serializer = QuoteDiscountCreateSerializer(
            data=request.data, context={"quote": quote, **self.get_serializer_context()}
        )
        serializer.is_valid(raise_exception=True)
        discount = quote.add_discount(serializer.validated_data["coupon"])

        logger.info("Quote discount added", quote_id=quote.id, discount_id=discount.id)
        serializer = QuoteDiscountSerializer(discount)
        return Response(serializer.data)


class QuoteDiscountDestroyAPIView(generics.GenericAPIView):
    queryset = QuoteDiscount.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return QuoteDiscount.objects.filter(quote__account_id=self.request.account.id)

    @extend_schema(operation_id="remove_quote_discount", request=None, responses={204: None})
    def delete(self, _, quote_discount_id: str, quote_id: str):
        discount = get_object_or_404(self.get_queryset(), pk=quote_discount_id)
        quote = discount.quote

        if quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Only draft quotes can be modified")

        discount.delete()
        quote.recalculate()

        logger.info("Quote discount removed", quote_id=quote_id, discount_id=quote_discount_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuoteLineTaxCreateAPIView(generics.GenericAPIView):
    queryset = QuoteLine.objects.none()
    serializer_class = QuoteLineTaxCreateSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return QuoteLine.objects.filter(quote__account_id=self.request.account.id)

    @extend_schema(
        operation_id="add_quote_line_tax",
        request=QuoteLineTaxCreateSerializer,
        responses={200: QuoteLineTaxSerializer},
    )
    def post(self, request, quote_line_id: str):
        quote_line = get_object_or_404(self.get_queryset(), pk=quote_line_id)

        if quote_line.quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Only draft quotes can be modified")

        serializer = QuoteLineTaxCreateSerializer(
            data=request.data, context={"quote_line": quote_line, **self.get_serializer_context()}
        )
        serializer.is_valid(raise_exception=True)
        tax = quote_line.add_tax(serializer.validated_data["tax_rate"])

        logger.info(
            "Quote line tax added",
            quote_id=quote_line.quote_id,
            quote_line_id=quote_line.id,
            tax_id=tax.id,
        )
        return Response(QuoteLineTaxSerializer(tax).data, status=status.HTTP_200_OK)


class QuoteLineTaxDestroyAPIView(generics.GenericAPIView):
    queryset = QuoteTax.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return QuoteTax.objects.filter(quote__account_id=self.request.account.id)

    @extend_schema(operation_id="remove_quote_line_tax", request=None, responses={204: None})
    def delete(self, _, quote_line_tax_id: str, quote_line_id: str):
        tax = get_object_or_404(self.get_queryset(), pk=quote_line_tax_id)
        quote_line = tax.quote_line

        if tax.quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Only draft quotes can be modified")

        tax.delete()
        quote_line.recalculate()

        logger.info(
            "Quote line tax removed",
            quote_id=quote_line.quote_id,
            quote_line_id=quote_line_id,
            tax_id=quote_line_tax_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuoteTaxCreateAPIView(generics.GenericAPIView):
    queryset = Quote.objects.none()
    serializer_class = QuoteTaxCreateSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Quote.objects.filter(account_id=self.request.account.id).select_related("customer")

    @extend_schema(
        operation_id="add_quote_tax",
        request=QuoteTaxCreateSerializer,
        responses={200: QuoteTaxSerializer},
    )
    def post(self, request, quote_id: str):
        quote = get_object_or_404(self.get_queryset(), pk=quote_id)

        if quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Only draft quotes can be modified")

        serializer = QuoteTaxCreateSerializer(
            data=request.data, context={"quote": quote, **self.get_serializer_context()}
        )
        serializer.is_valid(raise_exception=True)
        tax = quote.add_tax(serializer.validated_data["tax_rate"])

        logger.info("Quote tax added", quote_id=quote.id, tax_id=tax.id)
        serializer = QuoteTaxSerializer(tax)
        return Response(serializer.data)


class QuoteTaxDestroyAPIView(generics.GenericAPIView):
    queryset = QuoteTax.objects.none()
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return QuoteTax.objects.filter(quote__account_id=self.request.account.id)

    @extend_schema(operation_id="remove_quote_tax", request=None, responses={204: None})
    def delete(self, _, quote_tax_id: str, quote_id: str):
        tax = get_object_or_404(self.get_queryset(), pk=quote_tax_id)
        quote = tax.quote

        if tax.quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Only draft quotes can be modified")

        tax.delete()
        quote.recalculate()

        logger.info("Quote tax removed", quote_id=quote_id, tax_id=quote_tax_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
