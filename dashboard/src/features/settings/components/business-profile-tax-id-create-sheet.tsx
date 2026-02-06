import type { TaxId } from "@/api/models";
import { AccountTaxIdCreateSheet } from "@/features/settings/components/account-tax-id-create-sheet";

export function BusinessProfileTaxIdCreateSheet({
  accountId,
  businessProfileId,
  onSuccess,
}: {
  accountId: string;
  businessProfileId: string;
  onSuccess?: (taxId: TaxId) => void;
}) {
  return (
    <AccountTaxIdCreateSheet
      accountId={accountId}
      businessProfileId={businessProfileId}
      onSuccess={onSuccess}
    />
  );
}
