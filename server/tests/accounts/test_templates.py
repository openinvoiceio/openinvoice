import pytest
from django.template.loader import render_to_string

pytestmark = pytest.mark.django_db


def test_invitation_subject_template():
    context = {"account_name": "Acme Corp"}
    subject = render_to_string("accounts/email/invitation_subject.txt", context).strip()
    assert subject == "Join Acme Corp on Invoicence"


def test_invitation_message_text_template():
    context = {
        "account_name": "Acme Corp",
        "invitation_url": "https://example.com/invite",
        "invitee_email": "owner@example.com",
    }
    body = render_to_string("accounts/email/invitation_message.txt", context)
    assert "Acme Corp" in body
    assert "https://example.com/invite" in body
    assert "owner@example.com" in body


def test_invitation_message_html_template():
    context = {
        "account_name": "Acme Corp",
        "invitation_url": "https://example.com/invite",
        "invitee_email": "owner@example.com",
    }
    body = render_to_string("accounts/email/invitation_message.html", context)
    assert "Acme Corp" in body
    assert "https://example.com/invite" in body
    assert "owner@example.com" in body


def test_account_already_exists_subject_template():
    subject = render_to_string("account/email/account_already_exists_subject.txt").strip()
    assert subject == "Account already exists"


def test_account_already_exists_message_text_template():
    context = {
        "email": "user@example.com",
        "password_reset_url": "https://example.com/reset",
    }
    body = render_to_string("account/email/account_already_exists_message.txt", context)
    assert "user@example.com" in body
    assert "https://example.com/reset" in body


def test_account_already_exists_message_html_template():
    context = {
        "email": "user@example.com",
        "password_reset_url": "https://example.com/reset",
    }
    body = render_to_string("account/email/account_already_exists_message.html", context)
    assert "user@example.com" in body
    assert "https://example.com/reset" in body


def test_email_confirmation_subject_template():
    subject = render_to_string("account/email/email_confirmation_subject.txt").strip()
    assert subject == "Confirm email for Invoicence"


def test_email_confirmation_message_text_template(user):
    context = {"user": user, "code": "123456"}
    body = render_to_string("account/email/email_confirmation_message.txt", context)
    assert f"Hi {user.email}" in body
    assert "123456" in body


def test_email_confirmation_message_html_template(user):
    context = {"user": user, "code": "123456"}
    body = render_to_string("account/email/email_confirmation_message.html", context)
    assert f"Hi {user.email}" in body
    assert "123456" in body


def test_email_confirmation_signup_subject_template():
    subject = render_to_string("account/email/email_confirmation_signup_subject.txt").strip()
    assert subject == "Confirm email for Invoicence"


def test_email_confirmation_signup_message_text_template(user):
    context = {"user": user, "code": "123456"}
    body = render_to_string("account/email/email_confirmation_signup_message.txt", context)
    assert f"Hi {user.email}" in body
    assert "123456" in body


def test_email_confirmation_signup_message_html_template(user):
    context = {"user": user, "code": "123456"}
    body = render_to_string("account/email/email_confirmation_signup_message.html", context)
    assert f"Hi {user.email}" in body
    assert "123456" in body


def test_login_code_subject_template():
    subject = render_to_string("account/email/login_code_subject.txt").strip()
    assert subject == "Sign-in code"


def test_login_code_message_text_template():
    context = {"code": "123456"}
    body = render_to_string("account/email/login_code_message.txt", context)
    assert "123456" in body


def test_login_code_message_html_template():
    context = {"code": "123456"}
    body = render_to_string("account/email/login_code_message.html", context)
    assert "123456" in body


def test_password_reset_code_subject_template():
    subject = render_to_string("account/email/password_reset_code_subject.txt").strip()
    assert subject == "Password reset code"


def test_password_reset_code_message_text_template():
    context = {"code": "123456"}
    body = render_to_string("account/email/password_reset_code_message.txt", context)
    assert "123456" in body


def test_password_reset_code_message_html_template():
    context = {"code": "123456"}
    body = render_to_string("account/email/password_reset_code_message.html", context)
    assert "123456" in body


def test_password_reset_key_subject_template():
    subject = render_to_string("account/email/password_reset_key_subject.txt").strip()
    assert subject == "Password reset email"


def test_password_reset_key_message_text_template():
    context = {
        "password_reset_url": "https://example.com/reset",
        "username": "john",
    }
    body = render_to_string("account/email/password_reset_key_message.txt", context)
    assert "https://example.com/reset" in body
    assert "john" in body


def test_password_reset_key_message_html_template():
    context = {
        "password_reset_url": "https://example.com/reset",
        "username": "john",
    }
    body = render_to_string("account/email/password_reset_key_message.html", context)
    assert "https://example.com/reset" in body
    assert "john" in body
