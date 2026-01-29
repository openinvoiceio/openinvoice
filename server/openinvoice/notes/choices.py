from django.db import models


class NoteVisibility(models.TextChoices):
    INTERNAL = "internal", "Internal"
    PUBLIC = "public", "Public"
