from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string

from common.pdf import generate_pdf
from openinvoice.files.choices import FilePurpose
from openinvoice.files.models import File

from .models import Invoice


def generate_invoice_pdf(invoice: Invoice) -> File:
    filename = f"{invoice.id}.pdf"
    content_type = "application/pdf"
    html = render_to_string("invoices/pdf/classic.html", {"invoice": invoice})
    content = generate_pdf(html)

    return File.objects.upload_for_account(
        account=invoice.account,
        purpose=FilePurpose.INVOICE_PDF,
        filename=filename,
        data=SimpleUploadedFile(
            name=filename,
            content=content,
            content_type=content_type,
        ),
        content_type=content_type,
    )
