from unittest.mock import patch

import pytest


@pytest.fixture
def email_send_mock():
    with patch("apps.invoices.mail.EmailMultiAlternatives.send") as mock:
        yield mock
