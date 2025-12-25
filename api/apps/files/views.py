import structlog
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAccountMember

from .enums import FilePurpose
from .models import File
from .serializers import FileSerializer, FileUploadSerializer

logger = structlog.get_logger(__name__)


@extend_schema_view(list=extend_schema(operation_id="list_files"))
class FileListCreateAPIView(generics.ListAPIView):
    queryset = File.objects.none()
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return File.objects.visible_to(self.request.account, self.request.user)

    @extend_schema(
        operation_id="upload_file",
        request={
            "multipart/form-data": {
                "type": "object",
                "required": ["file", "purpose"],
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                    "purpose": {"type": "string"},
                },
            }
        },
        responses={201: FileSerializer},
    )
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]

        if serializer.validated_data["purpose"] in [FilePurpose.PROFILE_AVATAR]:
            file = File.objects.upload_for_user(
                uploader=request.user,
                purpose=serializer.validated_data["purpose"],
                filename=uploaded_file.name,
                data=uploaded_file,
                content_type=uploaded_file.content_type or "",
            )
            logger.info(
                "File uploaded",
                filename=uploaded_file.name,
                file_id=str(file.id),
                uploader_id=request.user.id,
            )
        else:
            file = File.objects.upload_for_account(
                account=request.account,
                purpose=serializer.validated_data["purpose"],
                filename=uploaded_file.name,
                data=uploaded_file,
                content_type=uploaded_file.content_type or "",
                uploader_id=request.user.id,
            )
            logger.info(
                "File uploaded",
                filename=uploaded_file.name,
                file_id=str(file.id),
                account_id=str(request.account.id),
                uploader_id=request.user.id,
            )

        serializer = FileSerializer(file)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(retrieve=extend_schema(operation_id="retrieve_file"))
class FileRetrieveAPIView(generics.RetrieveAPIView):
    queryset = File.objects.none()
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated, IsAccountMember]

    def get_queryset(self):
        return File.objects.visible_to(self.request.account, self.request.user)
