import uuid

from django.db import models

from .choices import NoteVisibility
from .managers import NoteManager


class Note(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="notes")
    content = models.CharField(max_length=2048)
    visibility = models.CharField(max_length=20, choices=NoteVisibility.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = NoteManager()

    class Meta:
        ordering = ["-created_at"]
