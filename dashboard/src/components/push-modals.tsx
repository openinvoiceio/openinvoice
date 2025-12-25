import { AccountCreateDialog } from "@/components/account-create-dialog";
import { AccountTaxIdCreateSheet } from "@/components/account-tax-id-create-sheet";
import { CouponCreateSheet } from "@/components/coupon-create-sheet";
import { CouponEditSheet } from "@/components/coupon-edit-sheet";
import { CreditNotePreviewDialog } from "@/components/credit-note-preview-dialog";
import { CustomerCreateSheet } from "@/components/customer-create-sheet";
import { CustomerPortalEditSheet } from "@/components/customer-portal-edit-sheet";
import { CustomerTaxIdCreateSheet } from "@/components/customer-tax-id-create-sheet";
import { DestructiveDialog } from "@/components/destructive-dialog";
import { InvoiceCreateDialog } from "@/components/invoice-create-dialog.tsx";
import { InvoicePreviewDialog } from "@/components/invoice-preview-dialog";
import { NumberingSystemCreateSheet } from "@/components/numbering-system-create-sheet";
import { PaymentRecordDialog } from "@/components/payment-record-dialog";
import { PriceCreateSheet } from "@/components/price-create-sheet";
import { PriceEditSheet } from "@/components/price-edit-sheet";
import { ProductCreateSheet } from "@/components/product-create-sheet";
import { ProductEditSheet } from "@/components/product-edit-sheet";
import { QuoteCreateDialog } from "@/components/quote-create-dialog.tsx";
import { QuotePreviewDialog } from "@/components/quote-preview-dialog.tsx";
import { SupportDialog } from "@/components/support-dialog";
import { TaxRateCreateSheet } from "@/components/tax-rate-create-sheet";
import { TaxRateEditSheet } from "@/components/tax-rate-edit-sheet";
import { createPushModal } from "pushmodal";

export const { pushModal, popModal, ModalProvider } = createPushModal({
  modals: {
    AccountCreateDialog,
    AccountTaxIdCreateSheet,
    CouponCreateSheet,
    CouponEditSheet,
    CreditNotePreviewDialog,
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
    SupportDialog,
    TaxRateCreateSheet,
    TaxRateEditSheet,
  },
});
