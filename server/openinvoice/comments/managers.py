from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from .choices import CommentVisibility

if TYPE_CHECKING:
    from openinvoice.users.models import User


class CommentManager(models.Manager):
    def create_comment(
        self,
        author: User,
        content: str,
        visibility: CommentVisibility | None = None,
    ):
        return self.create(
            author=author,
            content=content,
            visibility=visibility or CommentVisibility.PUBLIC,
        )
