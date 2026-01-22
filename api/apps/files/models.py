from __future__ import annotations

import base64
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models

from .choices import FilePurpose
from .managers import FileManager
from .querysets import FileQuerySet


class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="files", null=True)
    uploader = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True)
    purpose = models.CharField(max_length=50, choices=FilePurpose.choices)
    filename = models.CharField(max_length=1000, null=True)
    content_type = models.CharField(max_length=100)
    data = models.FileField(upload_to="files/")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = FileManager.from_queryset(FileQuerySet)()

    class Meta:
        ordering = ["-created_at"]

    def base64(self) -> str:
        try:
            return base64.b64encode(self.data.read()).decode("utf-8")
        except (FileNotFoundError, OSError, ValueError, AttributeError, TypeError):
            return ""

    def clone(self) -> File:
        self.data.open("rb")
        try:
            content = self.data.read()
        finally:
            self.data.seek(0)

        return File.objects.upload_for_account(
            account=self.account,
            purpose=self.purpose,
            filename=self.filename or "",
            data=SimpleUploadedFile(
                name=self.filename or "",
                content=content,
                content_type=self.content_type,
            ),
            content_type=self.content_type,
            uploader_id=self.uploader_id,
        )
