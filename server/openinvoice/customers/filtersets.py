import django_filters

from openinvoice.core.filters import CharInFilter

from .models import BillingProfile, Customer, ShippingProfile


class CustomerFilterSet(django_filters.FilterSet):
    currency = CharInFilter(field_name="default_billing_profile__currency")
    created_at_after = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_before = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Customer
        fields = []


class BillingProfileFilterSet(django_filters.FilterSet):
    customer_id = django_filters.UUIDFilter(field_name="customers__id", lookup_expr="exact", distinct=True)

    class Meta:
        model = BillingProfile
        fields = []


class ShippingProfileFilterSet(django_filters.FilterSet):
    customer_id = django_filters.UUIDFilter(field_name="customers__id", lookup_expr="exact", distinct=True)

    class Meta:
        model = ShippingProfile
        fields = []
