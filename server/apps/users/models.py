from typing import TYPE_CHECKING, ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models

if TYPE_CHECKING:
    from apps.files.models import File


class User(AbstractUser):
    name = models.CharField(null=True, max_length=255)
    email = models.EmailField(unique=True)
    avatar = models.OneToOneField("files.File", on_delete=models.SET_NULL, null=True, related_name="user_avatar")
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    USERNAME_FIELD: str = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = ["username"]

    def update_profile(self, name: str | None, avatar: "File | None") -> None:
        self.name = name
        self.avatar = avatar
        self.save(update_fields=["name", "avatar"])
