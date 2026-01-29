from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from .choices import NoteVisibility

if TYPE_CHECKING:
    from openinvoice.users.models import User


class NoteManager(models.Manager):
    def create_note(
        self,
        author: User,
        content: str,
        visibility: NoteVisibility | None = None,
    ):
        return self.create(
            author=author,
            content=content,
            visibility=visibility or NoteVisibility.PUBLIC,
        )
