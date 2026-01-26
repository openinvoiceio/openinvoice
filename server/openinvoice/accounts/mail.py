from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

if TYPE_CHECKING:
    from .models import Invitation


def send_invitation_email(invitation: Invitation) -> None:
    context = {
        "account_name": invitation.account.name,
        "invitation_url": settings.INVITATION_URL.format(code=invitation.code),
        "invitee_email": invitation.invited_by.email,
    }
    subject = render_to_string("accounts/email/invitation_subject.txt", context).strip()
    body_txt = render_to_string("accounts/email/invitation_message.txt", context)
    body_html = render_to_string("accounts/email/invitation_message.html", context)

    message = EmailMultiAlternatives(subject=subject, body=body_txt, to=[invitation.email])
    message.attach_alternative(body_html, "text/html")
    message.send()
