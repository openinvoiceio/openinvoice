from django.db import models


class MemberRole(models.TextChoices):
    MEMBER = "member"
    OWNER = "owner"


class InvitationStatus(models.TextChoices):
    PENDING = "pending"
    ACCEPTED = "accepted"
