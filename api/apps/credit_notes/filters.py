import django_filters

from common.filters import CharInFilter

from .models import CreditNote


class CreditNoteFilter(django_filters.FilterSet):
    status = CharInFilter(field_name="status")
    invoice_id = django_filters.UUIDFilter(field_name="invoice_id", lookup_expr="exact")
    customer_id = django_filters.UUIDFilter(field_name="customer_id", lookup_expr="exact")
    created_at_after = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_before = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")
    issue_date_after = django_filters.IsoDateTimeFilter(field_name="issue_date", lookup_expr="gte")
    issue_date_before = django_filters.IsoDateTimeFilter(field_name="issue_date", lookup_expr="lte")
    total_amount_min = django_filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    total_amount_max = django_filters.NumberFilter(field_name="total_amount", lookup_expr="lte")
    numbering_system_id = django_filters.UUIDFilter(field_name="numbering_system_id", lookup_expr="exact")

    class Meta:
        model = CreditNote
        fields = []
