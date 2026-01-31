from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .choices import InvoiceDocumentAudience
from .models import Invoice


def send_invoice(invoice: Invoice) -> None:
    context = {"invoice": invoice}
    subject = render_to_string("invoices/email/invoice_email_subject.txt", context).strip()
    body_txt = render_to_string("invoices/email/invoice_email_message.txt", context)
    body_html = render_to_string("invoices/email/invoice_email_message.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=body_txt,
        to=invoice.recipients,
    )
    message.attach_alternative(body_html, "text/html")

    documents = invoice.documents.filter(audience__contains=[InvoiceDocumentAudience.CUSTOMER]).select_related("file")
    for document in documents:
        if not document.file:
            continue
        filename = document.file.filename or f"{invoice.number}-{document.language}.pdf"
        document.file.data.open("rb")
        try:
            message.attach(
                filename,
                document.file.data.read(),
                document.file.content_type,
            )
        finally:
            document.file.data.close()
    message.send()
