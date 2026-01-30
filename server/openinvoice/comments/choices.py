from django.db import models


class CommentVisibility(models.TextChoices):
    INTERNAL = "internal", "Internal"
    PUBLIC = "public", "Public"
