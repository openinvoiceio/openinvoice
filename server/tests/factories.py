from decimal import Decimal

from django.utils import timezone
from factory import (
    DictFactory,
    LazyAttribute,
    LazyFunction,
    SelfAttribute,
    Sequence,
    SubFactory,
    post_generation,
)
from factory.django import DjangoModelFactory, FileField, Password

from openinvoice.accounts.choices import InvitationStatus, MemberRole
from openinvoice.comments.choices import CommentVisibility
from openinvoice.coupons.choices import CouponStatus
from openinvoice.credit_notes.choices import CreditNoteDeliveryMethod, CreditNoteStatus
from openinvoice.invoices.choices import (
    InvoiceDeliveryMethod,
    InvoiceDocumentAudience,
    InvoiceStatus,
    InvoiceTaxBehavior,
)
from openinvoice.numbering_systems.choices import (
    NumberingSystemAppliesTo,
    NumberingSystemResetInterval,
    NumberingSystemStatus,
)
from openinvoice.portal.crypto import sign_portal_token
from openinvoice.prices.choices import PriceModel, PriceStatus
from openinvoice.products.choices import ProductStatus
from openinvoice.quotes.choices import QuoteDeliveryMethod, QuoteStatus
from openinvoice.shipping_rates.choices import ShippingRateStatus
from openinvoice.tax_ids.choices import TaxIdType
from openinvoice.tax_rates.choices import TaxRateStatus


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


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = "comments.Comment"

    author = SubFactory(UserFactory)
    content = Sequence(lambda n: f"Comment {n}")
    visibility = CommentVisibility.PUBLIC


class AccountFactory(DjangoModelFactory):
    class Meta:
        model = "accounts.Account"

    is_active = True
    created_by = SubFactory(UserFactory)
    country = "PL"
    default_currency = "PLN"
    language = "en-us"
    invoice_footer = None
    invoice_numbering_system = None
    credit_note_numbering_system = None
    net_payment_term = 0
    metadata = {}
    logo = None
    default_business_profile = SubFactory("tests.factories.BusinessProfileFactory")

    @post_generation
    def business_profiles(self, create, extracted, **_):
        if not create:
            return
        if extracted is not None:
            self.business_profiles.set(extracted)
        else:
            self.business_profiles.add(self.default_business_profile)


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


class BusinessProfileFactory(DjangoModelFactory):
    class Meta:
        model = "accounts.BusinessProfile"

    name = "Test Business"
    legal_name = None
    legal_number = None
    email = "business@example.com"
    phone = None
    address = SubFactory(AddressFactory)


class BillingProfileFactory(DjangoModelFactory):
    class Meta:
        model = "customers.BillingProfile"

    name = "Test Customer"
    legal_name = None
    legal_number = None
    email = "customer@example.com"
    phone = "123456789"
    address = SubFactory(AddressFactory)
    currency = "PLN"
    language = "en-us"
    net_payment_term = 0
    invoice_numbering_system = None
    credit_note_numbering_system = None


class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = "customers.Customer"

    description = "Test customer"
    metadata = {}
    account = SubFactory(AccountFactory)
    logo = None
    default_billing_profile = SubFactory("tests.factories.BillingProfileFactory")
    default_shipping_profile = None

    @post_generation
    def billing_profiles(self, create, extracted, **_):
        if not create:
            return
        if extracted is not None:
            self.billing_profiles.set(extracted)
        else:
            self.billing_profiles.add(self.default_billing_profile)

    @post_generation
    def shipping_profiles(self, create, extracted, **_):
        if not create:
            return
        if extracted is not None:
            self.shipping_profiles.set(extracted)
        elif self.default_shipping_profile:
            self.shipping_profiles.add(self.default_shipping_profile)

    @post_generation
    def shipping(self, create, extracted, **_):
        if not create or extracted is None:
            return
        if self.default_shipping_profile is None:
            self.default_shipping_profile = extracted
            self.save(update_fields=["default_shipping_profile"])
        self.shipping_profiles.add(extracted)


class ShippingProfileFactory(DjangoModelFactory):
    class Meta:
        model = "customers.ShippingProfile"

    name = "Shipping Customer"
    phone = "987654321"
    address = SubFactory(AddressFactory)


# TODO: DELETE ME
CustomerShippingFactory = ShippingProfileFactory


class CouponFactory(DjangoModelFactory):
    class Meta:
        model = "coupons.Coupon"

    name = "Test Coupon"
    currency = "PLN"
    amount = None
    percentage = Decimal("10.00")
    account = SubFactory(AccountFactory)
    status = CouponStatus.ACTIVE


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = "products.Product"

    account = SubFactory(AccountFactory)
    name = "Test Product"
    description = "Test product"
    status = ProductStatus.ACTIVE
    metadata = {}


class PriceFactory(DjangoModelFactory):
    class Meta:
        model = "prices.Price"

    account = SubFactory(AccountFactory)
    product = SubFactory(ProductFactory, account=SelfAttribute("..account"))
    amount = Decimal("10")
    currency = "PLN"
    model = PriceModel.FLAT
    status = PriceStatus.ACTIVE
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
        model = "tax_rates.TaxRate"

    account = SubFactory(AccountFactory)
    name = "VAT"
    description = "Value added tax"
    percentage = Decimal("10.00")
    country = "PL"
    status = TaxRateStatus.ACTIVE


class ShippingRateFactory(DjangoModelFactory):
    class Meta:
        model = "shipping_rates.ShippingRate"

    account = SubFactory(AccountFactory)
    name = "Standard Shipping"
    code = None
    currency = "PLN"
    amount = Decimal("20.00")
    status = ShippingRateStatus.ACTIVE
    metadata = {}


class InvoiceHeadFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.InvoiceHead"

    root = None
    current = None


class InvoiceFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.Invoice"
        skip_postgeneration_save = True

    head = SubFactory(InvoiceHeadFactory)
    account = SubFactory(AccountFactory)
    customer = SubFactory(CustomerFactory, account=SelfAttribute("..account"))
    billing_profile = LazyAttribute(lambda obj: obj.customer.default_billing_profile)
    business_profile = LazyAttribute(lambda obj: obj.account.default_business_profile)
    number = Sequence(lambda n: f"INV-{n}")
    numbering_system = None
    currency = LazyAttribute(lambda obj: obj.billing_profile.currency or obj.account.default_currency)
    status = InvoiceStatus.DRAFT
    issue_date = None
    due_date = LazyFunction(lambda: timezone.now().date())
    subtotal_amount = SelfAttribute("total_amount")
    total_discount_amount = Decimal("0")
    total_excluding_tax_amount = Decimal("0")
    shipping_amount = Decimal("0")
    total_amount = Decimal("0")
    total_tax_amount = Decimal("0")
    total_credit_amount = Decimal("0")
    total_paid_amount = Decimal("0")
    outstanding_amount = SelfAttribute("total_amount")
    metadata = {}
    paid_at = None
    delivery_method = InvoiceDeliveryMethod.MANUAL
    tax_behavior = InvoiceTaxBehavior.AUTOMATIC
    recipients = LazyFunction(list)

    @post_generation
    def init_head(self, create, _, **__):
        if not create:
            return

        if self.previous_revision is None:
            self.head.root = self
            self.head.save()

        if self.status != InvoiceStatus.DRAFT:
            self.head.current = self
            self.head.save()


class InvoiceDocumentFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.InvoiceDocument"

    invoice = SubFactory(InvoiceFactory)
    audience = [InvoiceDocumentAudience.INTERNAL]
    language = "en-us"
    footer = None
    memo = None
    custom_fields = {}


class InvoiceLineFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.InvoiceLine"

    invoice = SubFactory(InvoiceFactory)
    description = "Line"
    quantity = 1
    currency = SelfAttribute("invoice.currency")
    unit_amount = Decimal("0")
    unit_excluding_tax_amount = SelfAttribute("unit_amount")
    amount = Decimal("0")
    subtotal_amount = Decimal("0")
    total_discount_amount = Decimal("0")
    total_taxable_amount = Decimal("0")
    total_excluding_tax_amount = Decimal("0")
    total_tax_amount = Decimal("0")
    total_tax_rate = Decimal("0")
    total_amount = Decimal("0")
    total_credit_amount = Decimal("0")
    credit_quantity = 0
    outstanding_amount = SelfAttribute("total_amount")
    outstanding_quantity = SelfAttribute("quantity")
    price = None


class InvoiceShippingFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.InvoiceShipping"

    shipping_rate = SubFactory(ShippingRateFactory)
    currency = LazyAttribute(lambda o: o.shipping_rate.currency)
    amount = Decimal("0")
    total_excluding_tax_amount = Decimal("0")
    total_tax_amount = Decimal("0")
    total_tax_rate = Decimal("0")
    total_amount = Decimal("0")


class InvoiceCouponFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.InvoiceCoupon"

    invoice = SubFactory(InvoiceFactory)
    coupon = SubFactory(
        CouponFactory,
        account=SelfAttribute("..invoice.account"),
        currency=SelfAttribute("..invoice.currency"),
    )
    position = Sequence(lambda n: n)


class InvoiceTaxRateFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.InvoiceTaxRate"

    invoice = SubFactory(InvoiceFactory)
    tax_rate = SubFactory(TaxRateFactory, account=SelfAttribute("..invoice.account"))
    position = Sequence(lambda n: n)


class InvoiceLineCouponFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.InvoiceLineCoupon"

    invoice_line = SubFactory(InvoiceLineFactory)
    coupon = SubFactory(
        CouponFactory,
        account=SelfAttribute("..invoice_line.invoice.account"),
        currency=SelfAttribute("..invoice_line.invoice.currency"),
    )
    position = Sequence(lambda n: n)


class InvoiceLineTaxRateFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.InvoiceLineTaxRate"

    invoice_line = SubFactory(InvoiceLineFactory)
    tax_rate = SubFactory(TaxRateFactory, account=SelfAttribute("..invoice_line.invoice.account"))
    position = Sequence(lambda n: n)


class InvoiceShippingTaxRateFactory(DjangoModelFactory):
    class Meta:
        model = "invoices.InvoiceShippingTaxRate"

    invoice_shipping = SubFactory(InvoiceShippingFactory)
    tax_rate = SubFactory(TaxRateFactory, account=SelfAttribute("..invoice_shipping.shipping_rate.account"))
    position = Sequence(lambda n: n)


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
    currency = LazyAttribute(lambda obj: obj.billing_profile.currency or obj.account.default_currency)
    status = QuoteStatus.DRAFT
    issue_date = LazyFunction(lambda: timezone.now().date())
    billing_profile = LazyAttribute(lambda obj: obj.customer.default_billing_profile)
    business_profile = LazyAttribute(lambda obj: obj.account.default_business_profile)
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
        kwargs.setdefault("billing_profile", customer.default_billing_profile)
        kwargs.setdefault("business_profile", account.default_business_profile)
        kwargs.setdefault("currency", customer.default_billing_profile.currency or account.default_currency)

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
    token = LazyAttribute(lambda o: sign_portal_token(o.customer))


class TaxIdFactory(DjangoModelFactory):
    class Meta:
        model = "tax_ids.TaxId"

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
    status = NumberingSystemStatus.ACTIVE


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
