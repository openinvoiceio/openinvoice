import type { TaxId } from "@/api/models";
import { CustomerTaxIdCreateSheet } from "@/features/customers/components/customer-tax-id-create-sheet";

export function BillingProfileTaxIdCreateSheet({
  customerId,
  billingProfileId,
  onSuccess,
}: {
  customerId: string;
  billingProfileId: string;
  onSuccess?: (taxId: TaxId) => void;
}) {
  return (
    <CustomerTaxIdCreateSheet
      customerId={customerId}
      billingProfileId={billingProfileId}
      onSuccess={onSuccess}
    />
  );
}
