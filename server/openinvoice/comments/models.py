import uuid

from django.db import models

from .choices import CommentVisibility
from .managers import CommentManager


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="comments")
    content = models.CharField(max_length=2048)
    visibility = models.CharField(max_length=20, choices=CommentVisibility.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CommentManager()

    class Meta:
        ordering = ["-created_at"]
