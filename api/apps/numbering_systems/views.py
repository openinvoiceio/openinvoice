from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember

from .choices import NumberingSystemStatus
from .filtersets import NumberingSystemFilterSet
from .models import NumberingSystem
from .permissions import CustomNumberingSystemFeature
from .serializers import NumberingSystemCreateSerializer, NumberingSystemSerializer, NumberingSystemUpdateSerializer


@extend_schema_view(list=extend_schema(operation_id="list_numbering_systems"))
class NumberingSystemListCreateAPIView(generics.ListAPIView):
    queryset = NumberingSystem.objects.none()
    serializer_class = NumberingSystemSerializer
    filterset_class = NumberingSystemFilterSet
    search_fields = ["description"]
    ordering_fields = ["created_at"]
    permission_classes = [
        IsAuthenticated,
        IsAccountMember,
        CustomNumberingSystemFeature,
    ]

    def get_queryset(self):
        return NumberingSystem.objects.for_account(self.request.account)

    @extend_schema(
        operation_id="create_numbering_system",
        request=NumberingSystemCreateSerializer,
        responses={201: NumberingSystemSerializer},
    )
    def post(self, request):
        serializer = NumberingSystemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        numbering_system = NumberingSystem.objects.create_numbering_system(
            account_id=request.account.id,
            template=data["template"],
            description=data.get("description"),
            applies_to=data["applies_to"],
            reset_interval=data.get("reset_interval"),
        )

        serializer = NumberingSystemSerializer(numbering_system)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_numbering_system"))
class NumberingSystemRetrieveUpdateDestroyAPIView(generics.RetrieveAPIView):
    queryset = NumberingSystem.objects.none()
    serializer_class = NumberingSystemSerializer
    permission_classes = [
        IsAuthenticated,
        IsAccountMember,
        CustomNumberingSystemFeature,
    ]

    def get_queryset(self):
        return NumberingSystem.objects.for_account(self.request.account)

    @extend_schema(
        operation_id="update_numbering_system",
        request=NumberingSystemUpdateSerializer,
        responses={200: NumberingSystemSerializer},
    )
    def put(self, request, **__):
        numbering_system = self.get_object()
        serializer = NumberingSystemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if numbering_system.status == NumberingSystemStatus.ARCHIVED:
            raise ValidationError("Cannot update once archived.")

        numbering_system.update(
            template=data["template"],
            description=data["description"],
            reset_interval=data["reset_interval"],
        )

        serializer = NumberingSystemSerializer(numbering_system)
        return Response(serializer.data)

    @extend_schema(
        operation_id="delete_numbering_system",
        request=None,
        responses={204: None},
    )
    def delete(self, *_, **__):
        numbering_system = self.get_object()

        if numbering_system.has_documents():
            raise ValidationError("Cannot delete numbering system with associated documents")

        numbering_system.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class NumberingSystemArchiveAPIView(generics.GenericAPIView):
    queryset = NumberingSystem.objects.none()
    serializer_class = NumberingSystemSerializer
    permission_classes = [
        IsAuthenticated,
        IsAccountMember,
        CustomNumberingSystemFeature,
    ]

    def get_queryset(self):
        return NumberingSystem.objects.for_account(self.request.account)

    @extend_schema(operation_id="archive_numbering_system", request=None, responses={200: NumberingSystemSerializer})
    def post(self, _, **__):
        numbering_system = self.get_object()

        numbering_system.archive()

        serializer = NumberingSystemSerializer(numbering_system)
        return Response(serializer.data)


class NumberingSystemRestoreAPIView(generics.GenericAPIView):
    queryset = NumberingSystem.objects.none()
    serializer_class = NumberingSystemSerializer
    permission_classes = [
        IsAuthenticated,
        IsAccountMember,
        CustomNumberingSystemFeature,
    ]

    def get_queryset(self):
        return NumberingSystem.objects.for_account(self.request.account)

    @extend_schema(operation_id="restore_numbering_system", request=None, responses={200: NumberingSystemSerializer})
    def post(self, _, **__):
        numbering_system = self.get_object()

        numbering_system.restore()

        serializer = NumberingSystemSerializer(numbering_system)
        return Response(serializer.data)
