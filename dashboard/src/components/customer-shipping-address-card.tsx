import {
  getCustomersListQueryKey,
  getCustomersRetrieveQueryKey,
  useUpdateCustomer,
} from "@/api/endpoints/customers/customers";
import { getInvoicesListQueryKey } from "@/api/endpoints/invoices/invoices";
import type { Customer } from "@/api/models";
import { AddressCard } from "@/components/address-card";
import { getErrorSummary } from "@/lib/api/errors";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

export function CustomerShippingAddressCard({
  customer,
}: {
  customer: Customer;
}) {
  const queryClient = useQueryClient();
  const { mutateAsync } = useUpdateCustomer({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getCustomersListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getCustomersRetrieveQueryKey(customer.id),
        });
        await queryClient.invalidateQueries({
          queryKey: getInvoicesListQueryKey(),
        });
        toast.success("Updated successfully");
      },
      onError: async (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });
  if (!customer.shipping?.address) return null;

  return (
    <AddressCard
      title="Shipping Address"
      description="Manage your shipping address"
      defaultValues={{
        line1: customer.shipping.address.line1 || "",
        line2: customer.shipping.address.line2 || "",
        locality: customer.shipping.address.locality || "",
        state: customer.shipping.address.state || "",
        postalCode: customer.shipping.address.postal_code || "",
        country: customer.shipping.address.country || undefined,
      }}
      onSubmit={async (values) => {
        await mutateAsync({
          id: customer.id,
          data: {
            shipping: {
              address: {
                line1: values.line1 || null,
                line2: values.line2 || null,
                locality: values.locality || null,
                state: values.state || null,
                postal_code: values.postalCode || null,
                country: values.country || null,
              },
            },
          },
        });
      }}
    />
  );
}
