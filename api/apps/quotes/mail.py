from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import Quote


def send_quote(quote: Quote) -> None:
    context = {"quote": quote}
    subject = render_to_string("quotes/email/quote_email_subject.txt", context).strip()
    body_txt = render_to_string("quotes/email/quote_email_message.txt", context)
    body_html = render_to_string("quotes/email/quote_email_message.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=body_txt,
        to=quote.recipients,
    )

    message.attach(f"{quote.effective_number}.pdf", quote.pdf.data.read(), quote.pdf.content_type)
    message.attach_alternative(body_html, "text/html")
    message.send()
