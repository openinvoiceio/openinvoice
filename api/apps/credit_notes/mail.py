from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import CreditNote


def send_credit_note(credit_note: CreditNote) -> None:
    context = {"credit_note": credit_note}
    subject = render_to_string("credit_notes/email/credit_note_email_subject.txt", context).strip()
    body_txt = render_to_string("credit_notes/email/credit_note_email_message.txt", context)
    body_html = render_to_string("credit_notes/email/credit_note_email_message.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=body_txt,
        to=list(credit_note.recipients),
    )
    message.attach_alternative(body_html, "text/html")
    if credit_note.pdf:
        message.attach(
            f"{credit_note.effective_number}.pdf",
            credit_note.pdf.data.read(),
            credit_note.pdf.content_type,
        )
    message.send()
