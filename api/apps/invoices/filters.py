import django_filters

from common.filters import CharInFilter

from .models import Invoice


class InvoiceFilter(django_filters.FilterSet):
    status = CharInFilter(field_name="status")
    currency = CharInFilter(field_name="currency")
    customer_id = django_filters.UUIDFilter(field_name="customer_id", lookup_expr="exact")
    created_at_after = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_before = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")
    issue_date_after = django_filters.IsoDateTimeFilter(field_name="issue_date", lookup_expr="gte")
    issue_date_before = django_filters.IsoDateTimeFilter(field_name="issue_date", lookup_expr="lte")
    due_date_after = django_filters.IsoDateTimeFilter(field_name="due_date", lookup_expr="gte")
    due_date_before = django_filters.IsoDateTimeFilter(field_name="due_date", lookup_expr="lte")
    subtotal_amount_min = django_filters.NumberFilter(field_name="subtotal_amount", lookup_expr="gte")
    subtotal_amount_max = django_filters.NumberFilter(field_name="subtotal_amount", lookup_expr="lte")
    total_amount_min = django_filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    total_amount_max = django_filters.NumberFilter(field_name="total_amount", lookup_expr="lte")
    total_paid_amount_min = django_filters.NumberFilter(field_name="total_paid_amount", lookup_expr="gte")
    total_paid_amount_max = django_filters.NumberFilter(field_name="total_paid_amount", lookup_expr="lte")
    outstanding_amount_min = django_filters.NumberFilter(field_name="outstanding_amount", lookup_expr="gte")
    outstanding_amount_max = django_filters.NumberFilter(field_name="outstanding_amount", lookup_expr="lte")
    product_id = django_filters.UUIDFilter(field_name="lines__price__product_id", lookup_expr="exact", distinct=True)
    numbering_system_id = django_filters.UUIDFilter(field_name="numbering_system_id", lookup_expr="exact")
    previous_revision_id = django_filters.UUIDFilter(field_name="previous_revision_id", lookup_expr="exact")
    latest_revision_id = django_filters.UUIDFilter(field_name="latest_revision_id", lookup_expr="exact")

    class Meta:
        model = Invoice
        fields: list[str] = []
