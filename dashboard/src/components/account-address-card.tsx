import {
  getAccountsListQueryKey,
  getAccountsRetrieveQueryKey,
  useUpdateAccount,
} from "@/api/endpoints/accounts/accounts";
import { getInvoicesListQueryKey } from "@/api/endpoints/invoices/invoices";
import type { Account, CountryEnum } from "@/api/models";
import { AddressCard } from "@/components/address-card";
import { getErrorSummary } from "@/lib/api/errors";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

export function AccountAddressCard({ account }: { account: Account }) {
  const queryClient = useQueryClient();
  const { mutateAsync } = useUpdateAccount({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getAccountsListQueryKey(),
          refetchType: "inactive", // TODO: return to ui flip later
        });
        await queryClient.invalidateQueries({
          queryKey: getAccountsRetrieveQueryKey(account.id),
        });
        await queryClient.invalidateQueries({
          queryKey: getInvoicesListQueryKey(),
        });
        toast.success("Account updated");
      },
      onError: async (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  return (
    <AddressCard
      description="Manage your company's or individual's address for legal and billing purposes."
      defaultValues={{
        line1: account.address.line1 || "",
        line2: account.address.line2 || "",
        locality: account.address.locality || "",
        state: account.address.state || "",
        postalCode: account.address.postal_code || "",
        country: account.address.country || undefined,
      }}
      onSubmit={async (values) => {
        await mutateAsync({
          id: account.id,
          data: {
            address: {
              line1: values.line1 || null,
              line2: values.line2 || null,
              locality: values.locality || null,
              state: values.state || null,
              postal_code: values.postalCode || null,
              country: (values.country as CountryEnum) || null,
            },
          },
        });
      }}
    />
  );
}
