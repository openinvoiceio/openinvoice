from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string

from common.pdf import generate_pdf
from openinvoice.files.choices import FilePurpose
from openinvoice.files.models import File

from .models import Invoice, InvoiceDocument


def generate_invoice_documents_pdf(invoice: Invoice) -> None:
    documents = list(invoice.documents.all())
    content_type = "application/pdf"

    for document in documents:
        filename = f"{document.id}.pdf"
        html = render_to_string(
            "invoices/pdf/classic.html",
            {
                "invoice": invoice,
                "document": document,
                "language": document.language,
            },
        )
        content = generate_pdf(html)
        file = File.objects.upload_for_account(
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
        document.file = file

    InvoiceDocument.objects.bulk_update(documents, fields=["file"])
