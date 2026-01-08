from decimal import Decimal

from django.utils import timezone
from factory import (
    DictFactory,
    LazyAttribute,
    LazyFunction,
    Maybe,
    SelfAttribute,
    Sequence,
    SubFactory,
    post_generation,
)
from factory.django import DjangoModelFactory, FileField, Password

from apps.accounts.enums import InvitationStatus, MemberRole
from apps.credit_notes.enums import CreditNoteDeliveryMethod, CreditNoteStatus
from apps.invoices.enums import InvoiceDeliveryMethod, InvoiceStatus
from apps.numbering_systems.enums import NumberingSystemAppliesTo, NumberingSystemResetInterval
from apps.portal.crypto import generate_portal_token
from apps.prices.enums import PriceModel
from apps.quotes.enums import QuoteDeliveryMethod, QuoteStatus
from apps.shipping_rates.enums import ShippingRateTaxPolicy
from apps.taxes.enums import TaxIdType


class UserFactory(DjangoModelFactory):
    class Meta:
        model = "users.User"
        django_get_or_create = ("email",)

    name = "alice"
    email = "alice@example.com"
    username = email
    password = Password("password")


class AddressFactory(DjangoModelFactory):
    class Meta:
        model = "addresses.Address"

    line1 = "123 Main St"
    line2 = "Apt 4B"
    locality = "Warsaw"
    postal_code = "00-001"
    state = "Mazowieckie"
    country = "PL"


class FileFactory(DjangoModelFactory):
    class Meta:
        model = "files.File"

    filename = "test_file.txt"
    content_type = "text/plain"
    data = FileField(data=b"This is a test file content.", filename=filename)
    uploader = SubFactory(UserFactory)


class AccountFactory(DjangoModelFactory):
    class Meta:
        model = "accounts.Account"

    name = "Test Account"
    legal_name = None
    legal_number = None
    email = "test@example.com"
    phone = None
    address = SubFactory(AddressFactory)
    created_by = SubFactory(UserFactory)
    country = "PL"
    default_currency = "PLN"
    invoice_footer = None
    net_payment_term = 0
    metadata = {}
    logo_id = None


class MemberFactory(DjangoModelFactory):
    class Meta:
        model = "accounts.Member"

    role = MemberRole.OWNER


class InvitationFactory(DjangoModelFactory):
    class Meta:
        model = "accounts.Invitation"

    email = "invitee@example.com"
    code = "invitation_code"
    status = InvitationStatus.PENDING
    invited_by = SubFactory(UserFactory)


class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = "customers.Customer"

    name = "Test Customer"
    legal_name = None
    legal_number = None
    email = "customer@example.com"
    phone = "123456789"
    description = "Test customer"
    currency = "PLN"
    net_payment_term = 0
    metadata = {}
    account = SubFactory(AccountFactory)
    billing_address = SubFactory(AddressFactory)
    shipping_address = SubFactory(AddressFactory)
    logo = None


class CouponFactory(DjangoModelFactory):
    class Meta:
        model = "coupons.Coupon"

    name = "Test Coupon"
    currency = "PLN"
    amount = None
    percentage = Decimal("10.00")
    account = SubFactory(AccountFactory)


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = "products.Product"

    account = SubFactory(AccountFactory)
    name = "Test Product"
    description = "Test product"
    is_active = True
    metadata = {}


class PriceFactory(DjangoModelFactory):
    class Meta:
        model = "prices.Price"

    account = SubFactory(AccountFactory)
    product = SubFactory(ProductFactory, account=SelfAttribute("..account"))
    amount = Decimal("10")
    currency = "PLN"
    model = PriceModel.FLAT
    is_active = True
    metadata = {}


class PriceTierFactory(DjangoModelFactory):
    class Meta:
        model = "prices.PriceTier"

    price = SubFactory(PriceFactory)
    unit_amount = Decimal("5")
    currency = LazyAttribute(lambda obj: obj.price.currency)
    from_value = 1
    to_value = None


class TaxRateFactory(DjangoModelFactory):
    class Meta:
        model = "taxes.TaxRate"

    account = SubFactory(AccountFactory)
    name = "VAT"
    description = "Value added tax"
    percentage = Decimal("10.00")
    country = "PL"
    is_active = True


class ShippingRateFactory(DjangoModelFactory):
    class Meta:
        model = "shipping_rates.ShippingRate"

    account = SubFactory(AccountFactory)
    name = "Standard Shipping"
    code = None
    currency = "PLN"
    amount = Decimal("20.00")
    tax_policy = ShippingRateTaxPolicy.MATCH_GOODS
    is_active = True
    metadata = {}


class InvoiceFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.Invoice"

    account = SubFactory(AccountFactory)
    customer = SubFactory(CustomerFactory, account=SelfAttribute("..account"))
    number = Sequence(lambda n: f"INV-{n}")
    numbering_system = None
    currency = "PLN"
    status = InvoiceStatus.DRAFT
    issue_date = None
    sell_date = None
    due_date = LazyFunction(lambda: timezone.now().date())
    footer = None
    description = None
    subtotal_amount = Decimal("0")
    total_discount_amount = Decimal("0")
    total_amount_excluding_tax = Decimal("0")
    shipping_amount = Decimal("0")
    total_amount = Decimal("0")
    total_tax_amount = Decimal("0")
    total_credit_amount = Decimal("0")
    total_paid_amount = Decimal("0")
    outstanding_amount = SelfAttribute("total_amount")
    metadata = {}
    custom_fields = {}
    paid_at = None
    delivery_method = InvoiceDeliveryMethod.MANUAL
    recipients = LazyFunction(list)


class InvoiceLineFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.InvoiceLine"

    invoice = SubFactory(InvoiceFactory)
    description = "Line"
    quantity = 1
    currency = SelfAttribute("invoice.currency")
    unit_amount = Decimal("0")
    amount = Decimal("0")
    total_amount_excluding_tax = Decimal("0")
    total_amount = Decimal("0")
    total_discount_amount = Decimal("0")
    total_tax_amount = Decimal("0")
    total_tax_rate = Decimal("0")
    total_credit_amount = Decimal("0")
    credit_quantity = 0
    outstanding_amount = SelfAttribute("total_amount")
    outstanding_quantity = SelfAttribute("quantity")
    price = None


class InvoiceDiscountFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.InvoiceDiscount"

    invoice_line = None
    invoice = Maybe(
        "invoice_line",
        yes_declaration=SelfAttribute("invoice_line.invoice"),
        no_declaration=SubFactory(InvoiceFactory),
    )
    coupon = SubFactory(
        CouponFactory,
        account=SelfAttribute("..invoice.account"),
        currency=SelfAttribute("..invoice.currency"),
    )
    currency = SelfAttribute("invoice.currency")
    amount = Decimal("0")


class InvoiceTaxFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.InvoiceTax"

    invoice_line = None
    invoice = Maybe(
        "invoice_line",
        yes_declaration=SelfAttribute("invoice_line.invoice"),
        no_declaration=SubFactory(InvoiceFactory),
    )
    tax_rate = SubFactory(TaxRateFactory, account=SelfAttribute("..invoice.account"))
    currency = SelfAttribute("invoice.currency")
    name = LazyAttribute(lambda o: o.tax_rate.name)
    description = LazyAttribute(lambda o: o.tax_rate.description)
    rate = LazyAttribute(lambda o: o.tax_rate.percentage)
    amount = Decimal("0")


class InvoiceShippingFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.InvoiceShipping"

    shipping_rate = SubFactory(ShippingRateFactory)
    currency = LazyAttribute(lambda o: o.shipping_rate.currency)
    amount = Decimal("0")
    tax_amount = Decimal("0")
    total_amount = Decimal("0")


class QuoteCustomerFactory(DjangoModelFactory):
    class Meta:
        model = "quotes.QuoteCustomer"

    customer = SubFactory(CustomerFactory)
    name = LazyAttribute(lambda o: o.customer.name)
    legal_name = LazyAttribute(lambda o: o.customer.legal_name)
    legal_number = LazyAttribute(lambda o: o.customer.legal_number)
    email = LazyAttribute(lambda o: o.customer.email)
    phone = LazyAttribute(lambda o: o.customer.phone)
    description = LazyAttribute(lambda o: o.customer.description)
    billing_address = SubFactory(AddressFactory)
    shipping_address = SubFactory(AddressFactory)
    logo = None

    @post_generation
    def tax_ids(self, create, extracted, **_):
        if not create:
            return
        if extracted is not None:
            self.tax_ids.set(extracted)
        else:
            self.tax_ids.set([])


class QuoteAccountFactory(DjangoModelFactory):
    class Meta:
        model = "quotes.QuoteAccount"

    account = SubFactory(AccountFactory)
    name = LazyAttribute(lambda o: o.account.name)
    legal_name = LazyAttribute(lambda o: o.account.legal_name)
    legal_number = LazyAttribute(lambda o: o.account.legal_number)
    email = LazyAttribute(lambda o: o.account.email)
    phone = LazyAttribute(lambda o: o.account.phone)
    address = SubFactory(AddressFactory)
    logo = None

    @post_generation
    def tax_ids(self, create, extracted, **_):
        if not create:
            return
        if extracted is not None:
            self.tax_ids.set(extracted)
        else:
            self.tax_ids.set([])


class QuoteFactory(DjangoModelFactory):
    class Meta:
        model = "quotes.Quote"

    account = SubFactory(AccountFactory)
    number = None
    numbering_system = None
    currency = "PLN"
    status = QuoteStatus.DRAFT
    issue_date = LazyFunction(lambda: timezone.now().date())
    subtotal_amount = Decimal("0")
    total_discount_amount = Decimal("0")
    total_amount_excluding_tax = Decimal("0")
    total_tax_amount = Decimal("0")
    total_amount = Decimal("0")
    delivery_method = QuoteDeliveryMethod.MANUAL
    recipients = LazyFunction(list)
    metadata = {}
    custom_fields = {}
    footer = None
    description = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        account = kwargs.get("account")
        if account is None:
            account = AccountFactory()
            kwargs["account"] = account
        customer = kwargs.pop("customer", None)
        if customer is None:
            customer = CustomerFactory(account=account)

        kwargs["customer"] = customer

        return super()._create(model_class, *args, **kwargs)


class QuoteLineFactory(DjangoModelFactory):
    class Meta:
        model = "quotes.QuoteLine"

    quote = SubFactory(QuoteFactory)
    description = "Quote line"
    quantity = 1
    currency = SelfAttribute("quote.currency")
    unit_amount = Decimal("0")
    amount = Decimal("0")
    total_amount_excluding_tax = Decimal("0")
    total_amount = Decimal("0")
    total_discount_amount = Decimal("0")
    total_tax_amount = Decimal("0")
    total_tax_rate = Decimal("0")
    price = None


class CreditNoteFactory(DjangoModelFactory):
    class Meta:
        model = "credit_notes.CreditNote"

    invoice = SubFactory(InvoiceFactory)
    account = SelfAttribute("invoice.account")
    customer = SelfAttribute("invoice.customer")
    currency = SelfAttribute("invoice.currency")
    status = CreditNoteStatus.DRAFT
    subtotal_amount = Decimal("0")
    total_amount_excluding_tax = Decimal("0")
    total_tax_amount = Decimal("0")
    total_amount = Decimal("0")
    delivery_method = CreditNoteDeliveryMethod.MANUAL
    recipients = LazyFunction(list)


class CreditNoteLineFactory(DjangoModelFactory):
    class Meta:
        model = "credit_notes.CreditNoteLine"

    credit_note = SubFactory(CreditNoteFactory)
    invoice_line = SubFactory(InvoiceLineFactory, invoice=SelfAttribute("..credit_note.invoice"))
    description = "Credit note line"
    quantity = 1
    currency = SelfAttribute("credit_note.currency")
    unit_amount = Decimal("0")
    amount = Decimal("0")
    total_amount_excluding_tax = Decimal("0")
    total_tax_amount = Decimal("0")
    total_amount = Decimal("0")


class PortalTokenFactory(DictFactory):
    customer = SubFactory(CustomerFactory)
    token = LazyAttribute(lambda o: generate_portal_token(o.customer))


class TaxIdFactory(DjangoModelFactory):
    class Meta:
        model = "taxes.TaxId"

    type = TaxIdType.US_EIN
    number = Sequence(lambda n: f"12345{n}")
    country = None


class NumberingSystemFactory(DjangoModelFactory):
    class Meta:
        model = "numbering_systems.NumberingSystem"

    account = SubFactory(AccountFactory)
    template = "INV-{n}"
    applies_to = NumberingSystemAppliesTo.INVOICE
    reset_interval = NumberingSystemResetInterval.NEVER


class StripeCustomerFactory(DjangoModelFactory):
    class Meta:
        model = "stripe.StripeCustomer"

    account = SubFactory(AccountFactory)
    customer_id = "cus_123"


class StripeSubscriptionFactory(DjangoModelFactory):
    class Meta:
        model = "stripe.StripeSubscription"

    stripe_customer = SubFactory(StripeCustomerFactory)
    subscription_id = "sub_123"
    price_id = "price_123"
    product_name = "Pro"
    status = "active"
    started_at = LazyFunction(lambda: timezone.now())
    ended_at = None
    canceled_at = None


class StripeConnectionFactory(DjangoModelFactory):
    class Meta:
        model = "stripe_integrations.StripeConnection"

    account = SubFactory(AccountFactory)
    name = "My Stripe Connection"
    code = "code_123"
    api_key = "sk_test_123"
    webhook_endpoint_id = "we_123"
    webhook_secret = "sk_test_456"  # noqa: S105
    redirect_url = None


class PaymentFactory(DjangoModelFactory):
    class Meta:
        model = "payments.Payment"

    account = SubFactory(AccountFactory)
    status = "succeeded"
    currency = "PLN"
    amount = Decimal("0")
    description = None
    transaction_id = None
    url = None
    message = None
    extra_data = LazyFunction(dict)
    received_at = LazyFunction(lambda: timezone.now())
