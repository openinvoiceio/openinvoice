from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember
from apps.customers.models import Customer
from apps.invoices.models import Invoice
from apps.products.models import Product

from .serializers import SearchSerializer


class SearchAPIView(generics.GenericAPIView):
    serializer_class = SearchSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def apply_search_filter(self, qs, search_fields):
        dummy_view = type("DummyView", (), {"search_fields": search_fields})()
        search_filter = SearchFilter()
        return search_filter.filter_queryset(self.request, qs, dummy_view)

    def get_queryset_products(self):
        qs = Product.objects.for_account(self.request.account).eager_load()
        return self.apply_search_filter(qs, ["id", "name", "description"])[:5]

    def get_queryset_invoices(self):
        qs = Invoice.objects.for_account(self.request.account).eager_load()
        return self.apply_search_filter(qs, ["id", "number", "customer__name", "customer__email"])[:5]

    def get_queryset_customers(self):
        qs = Customer.objects.for_account(self.request.account).eager_load()
        return self.apply_search_filter(qs, ["id", "name", "email", "phone", "description"])[:5]

    @extend_schema(
        operation_id="search",
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location="query",
                description="Search term applied across products, invoices, and customers",
                required=False,
            ),
        ],
        responses=SearchSerializer,
    )
    def get(self, _):
        products = self.get_queryset_products()
        invoices = self.get_queryset_invoices()
        customers = self.get_queryset_customers()

        serializer = self.get_serializer(
            {
                "products": products,
                "invoices": invoices,
                "customers": customers,
            }
        )
        return Response(serializer.data)
