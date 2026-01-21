from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.core.files import File as DjangoFile
from django.core.files.uploadedfile import UploadedFile
from django.db import models

from .choices import FilePurpose
from .querysets import FileQuerySet

if TYPE_CHECKING:
    from apps.accounts.models import Account
    from apps.users.models import User

    from .models import File


class FileManager(models.Manager.from_queryset(FileQuerySet)["File"]):
    def upload_for_account(
        self,
        account: Account,
        purpose: FilePurpose | str,
        filename: str,
        data: UploadedFile,
        content_type: str,
        uploader_id: int | None = None,
    ) -> File:
        file_id = uuid.uuid4()
        return self.create(
            id=file_id,
            account=account,
            uploader_id=uploader_id,
            purpose=purpose,
            filename=filename,
            content_type=content_type,
            data=DjangoFile(data, name=f"accounts/{account.id}/{file_id}-{filename}"),
        )

    def upload_for_user(
        self,
        uploader: User,
        purpose: FilePurpose | str,
        filename: str,
        data: UploadedFile,
        content_type: str,
    ) -> File:
        file_id = uuid.uuid4()
        return self.create(
            id=file_id,
            uploader=uploader,
            purpose=purpose,
            filename=filename,
            content_type=content_type,
            data=DjangoFile(data, name=f"users/{uploader.id}/{file_id}-{filename}"),
        )
