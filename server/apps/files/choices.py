from django.db import models


class FilePurpose(models.TextChoices):
    PRODUCT_IMAGE = "product_image"
    INVOICE_PDF = "invoice_pdf"
    QUOTE_PDF = "quote_pdf"
    CREDIT_NOTE_PDF = "credit_note_pdf"
    ACCOUNT_LOGO = "account_logo"
    PROFILE_AVATAR = "profile_avatar"
    CUSTOMER_LOGO = "customer_logo"
