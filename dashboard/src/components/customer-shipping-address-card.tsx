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
  const address = customer.shipping_address;

  return (
    <AddressCard
      title="Shipping Address"
      description="Manage your shipping address"
      defaultValues={{
        line1: address.line1 || "",
        line2: address.line2 || "",
        locality: address.locality || "",
        state: address.state || "",
        postalCode: address.postal_code || "",
        country: address.country || undefined,
      }}
      onSubmit={async (values) => {
        await mutateAsync({
          id: customer.id,
          data: {
            shipping_address: {
              line1: values.line1 || null,
              line2: values.line2 || null,
              locality: values.locality || null,
              state: values.state || null,
              postal_code: values.postalCode || null,
              country: values.country || null,
            },
          },
        });
      }}
    />
  );
}
