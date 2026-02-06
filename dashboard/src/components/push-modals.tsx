import { DestructiveDialog } from "@/components/destructive-dialog";
import { SupportDialog } from "@/components/support-dialog";
import { CouponCreateSheet } from "@/features/coupons/components/coupon-create-sheet";
import { CouponEditSheet } from "@/features/coupons/components/coupon-edit-sheet";
import { CreditNotePreviewDialog } from "@/features/credit-notes/components/credit-note-preview-dialog";
import { BillingProfileCreateSheet } from "@/features/customers/components/billing-profile-create-sheet";
import { BillingProfileEditSheet } from "@/features/customers/components/billing-profile-edit-sheet";
import { CustomerCreateSheet } from "@/features/customers/components/customer-create-sheet";
import { CustomerPortalEditSheet } from "@/features/customers/components/customer-portal-edit-sheet";
import { CustomerTaxIdCreateSheet } from "@/features/customers/components/customer-tax-id-create-sheet";
import { ShippingProfileCreateSheet } from "@/features/customers/components/shipping-profile-create-sheet";
import { ShippingProfileEditSheet } from "@/features/customers/components/shipping-profile-edit-sheet";
import { InvoiceCreateDialog } from "@/features/invoices/components/invoice-create-dialog.tsx";
import { InvoicePreviewDialog } from "@/features/invoices/components/invoice-preview-dialog";
import { PaymentRecordDialog } from "@/features/invoices/components/payment-record-dialog";
import { PriceCreateSheet } from "@/features/products/components/price-create-sheet";
import { PriceEditSheet } from "@/features/products/components/price-edit-sheet";
import { ProductCreateSheet } from "@/features/products/components/product-create-sheet";
import { ProductEditSheet } from "@/features/products/components/product-edit-sheet";
import { QuoteCreateDialog } from "@/features/quotes/components/quote-create-dialog.tsx";
import { QuotePreviewDialog } from "@/features/quotes/components/quote-preview-dialog.tsx";
import { AccountCreateDialog } from "@/features/settings/components/account-create-dialog";
import { AccountTaxIdCreateSheet } from "@/features/settings/components/account-tax-id-create-sheet";
import { BusinessProfileCreateSheet } from "@/features/settings/components/business-profile-create-sheet";
import { BusinessProfileEditSheet } from "@/features/settings/components/business-profile-edit-sheet";
import { NumberingSystemCreateSheet } from "@/features/settings/components/numbering-system-create-sheet";
import { ShippingRateCreateSheet } from "@/features/shipping-rates/components/shipping-rate-create-sheet.tsx";
import { ShippingRateEditSheet } from "@/features/shipping-rates/components/shipping-rate-edit-sheet.tsx";
import { TaxRateCreateSheet } from "@/features/tax-rates/components/tax-rate-create-sheet";
import { TaxRateEditSheet } from "@/features/tax-rates/components/tax-rate-edit-sheet";
import { createPushModal } from "pushmodal";

export const { pushModal, popModal, ModalProvider } = createPushModal({
  modals: {
    AccountCreateDialog,
    AccountTaxIdCreateSheet,
    CouponCreateSheet,
    CouponEditSheet,
    CreditNotePreviewDialog,
    BillingProfileCreateSheet,
    BillingProfileEditSheet,
    CustomerCreateSheet,
    CustomerPortalEditSheet,
    CustomerTaxIdCreateSheet,
    DestructiveDialog,
    InvoiceCreateDialog,
    InvoicePreviewDialog,
    NumberingSystemCreateSheet,
    PaymentRecordDialog,
    PriceCreateSheet,
    PriceEditSheet,
    ProductCreateSheet,
    ProductEditSheet,
    QuoteCreateDialog,
    QuotePreviewDialog,
    BusinessProfileCreateSheet,
    BusinessProfileEditSheet,
    ShippingRateCreateSheet,
    ShippingRateEditSheet,
    ShippingProfileCreateSheet,
    ShippingProfileEditSheet,
    SupportDialog,
    TaxRateCreateSheet,
    TaxRateEditSheet,
  },
});
