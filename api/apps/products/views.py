from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember
from apps.prices.models import Price

from .choices import ProductStatus
from .filtersets import ProductFilterSet
from .models import Product
from .permissions import MaxProductsLimit
from .serializers import ProductCreateSerializer, ProductSerializer, ProductUpdateSerializer


@extend_schema_view(list=extend_schema(operation_id="list_products"))
class ProductListCreateAPIView(generics.ListAPIView):
    queryset = Product.objects.none()
    serializer_class = ProductSerializer
    filterset_class = ProductFilterSet
    search_fields = ["name", "description"]
    ordering_fields = ["created_at"]
    permission_classes = [IsAuthenticated, IsAccountMember, MaxProductsLimit]

    def get_queryset(self):
        return Product.objects.for_account(self.request.account).with_prices().order_by("-created_at")

    @extend_schema(
        operation_id="create_product",
        request=ProductCreateSerializer,
        responses={201: ProductSerializer},
    )
    def post(self, request):
        serializer = ProductCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = Product.objects.create_product(
            account=request.account,
            name=data["name"],
            description=data.get("description"),
            url=data.get("url"),
            image=data.get("image"),
            metadata=data.get("metadata"),
        )

        default_price = data.get("default_price")
        if default_price:
            product.default_price = Price.objects.create_price(
                amount=default_price["amount"],
                product=product,
                currency=default_price["currency"],
                metadata=default_price.get("metadata"),
                code=default_price.get("code"),
            )
            product.save(update_fields=["default_price", "updated_at"])

        product.prices_count = 1 if default_price else 0

        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_product"))
class ProductRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.none()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Product.objects.for_account(self.request.account).with_prices()

    @extend_schema(
        operation_id="update_product",
        request=ProductUpdateSerializer,
        responses={200: ProductSerializer},
    )
    def put(self, request, **_):
        product = self.get_object()
        serializer = ProductUpdateSerializer(product, data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if product.status == ProductStatus.ARCHIVED:
            raise ValidationError("Cannot update once archived.")

        product.update(
            name=data.get("name", product.name),
            description=data.get("description", product.description),
            url=data.get("url", product.url),
            image=data.get("image", product.image),
            default_price=data.get("default_price", product.default_price),
            metadata=data.get("metadata", product.metadata),
        )

        serializer = ProductSerializer(product)
        return Response(serializer.data)

    @extend_schema(
        operation_id="delete_product",
        request=None,
        responses={204: None},
    )
    def delete(self, _, **__):
        product = self.get_object()

        if product.prices.exists():
            raise ValidationError("Product is restricted and cannot be deleted.")

        product.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductArchiveAPIView(generics.GenericAPIView):
    queryset = Product.objects.none()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Product.objects.for_account(self.request.account).with_prices()

    @extend_schema(
        operation_id="archive_product",
        request=None,
        responses={200: ProductSerializer},
    )
    def post(self, _, **__):
        product = self.get_object()

        product.archive()

        serializer = ProductSerializer(product)
        return Response(serializer.data)


class ProductRestoreAPIView(generics.GenericAPIView):
    queryset = Product.objects.none()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return Product.objects.for_account(self.request.account).with_prices()

    @extend_schema(
        operation_id="restore_product",
        request=None,
        responses={200: ProductSerializer},
    )
    def post(self, _, **__):
        product = self.get_object()

        product.restore()

        serializer = ProductSerializer(product)
        return Response(serializer.data)
