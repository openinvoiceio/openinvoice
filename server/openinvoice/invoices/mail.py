from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import Invoice


def send_invoice(invoice: Invoice) -> None:
    document = invoice.primary_document
    context = {
        "invoice": invoice,
        "document": document,
        "language": document.language if document else None,
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
    if document and document.file:
        message.attach(f"{invoice.number}.pdf", document.file.data.read(), document.file.content_type)
    message.send()
