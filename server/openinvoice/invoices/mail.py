from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import Invoice


def send_invoice(invoice: Invoice) -> None:
    context = {
        "invoice": invoice,
        "document": invoice.primary_document,
    }
    subject = render_to_string("invoices/email/invoice_email_subject.txt", context).strip()
    body_txt = render_to_string("invoices/email/invoice_email_message.txt", context)
    body_html = render_to_string("invoices/email/invoice_email_message.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=body_txt,
        to=invoice.recipients,
    )
    message.attach_alternative(body_html, "text/html")
    if invoice.primary_document.file:
        message.attach(
            f"{invoice.number}.pdf",
            invoice.primary_document.file.data.read(),
            invoice.primary_document.file.content_type,
        )
    message.send()
