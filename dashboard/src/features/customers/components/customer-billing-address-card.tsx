import {
  getCustomersListQueryKey,
  getCustomersRetrieveQueryKey,
  useUpdateCustomer,
} from "@/api/endpoints/customers/customers";
import { getInvoicesListQueryKey } from "@/api/endpoints/invoices/invoices";
import { CountryEnum, type Customer } from "@/api/models";
import { AddressCountryField } from "@/components/fields/address-country-field";
import { AddressLine1Field } from "@/components/fields/address-line1-field";
import { AddressLine2Field } from "@/components/fields/address-line2-field";
import { AddressLocalityField } from "@/components/fields/address-locality-field";
import { AddressPostalCodeField } from "@/components/fields/address-postal-code-field";
import { AddressStateField } from "@/components/fields/address-state-field";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";
import {
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardFooter,
  FormCardHeader,
  FormCardSeparator,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Spinner } from "@/components/ui/spinner";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  line1: z.string().optional(),
  line2: z.string().optional(),
  locality: z.string().optional(),
  state: z.string().optional(),
  postalCode: z.string().optional(),
  country: z.enum(CountryEnum).optional(),
});

type FormValues = z.infer<typeof schema>;

export function CustomerBillingAddressCard({
  customer,
}: {
  customer: Customer;
}) {
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      line1: customer.address.line1 || "",
      line2: customer.address.line2 || "",
      locality: customer.address.locality || "",
      state: customer.address.state || "",
      postalCode: customer.address.postal_code || "",
      country: customer.address.country || undefined,
    },
  });
  const { mutateAsync, isPending } = useUpdateCustomer({
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
        toast.success("Customer updated");
      },
      onError: async (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  async function onSubmit(values: FormValues) {
    await mutateAsync({
      id: customer.id,
      data: {
        address: {
          line1: values.line1 || null,
          line2: values.line2 || null,
          locality: values.locality || null,
          state: values.state || null,
          postal_code: values.postalCode || null,
          country: values.country || null,
        },
      },
    });
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormCard>
          <FormCardHeader>
            <FormCardTitle>Billing Address</FormCardTitle>
            <FormCardDescription>
              Manage your billing address.
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent>
            <AddressLine1Field />
            <AddressLine2Field />
          </FormCardContent>
          <FormCardSeparator />
          <FormCardContent className="grid-cols-2">
            <AddressLocalityField />
            <AddressPostalCodeField />
          </FormCardContent>
          <FormCardSeparator />
          <FormCardContent className="grid-cols-2">
            <AddressCountryField />
            <AddressStateField />
          </FormCardContent>
          <FormCardFooter>
            <Button type="submit" disabled={isPending}>
              {isPending && <Spinner />}
              Submit
            </Button>
          </FormCardFooter>
        </FormCard>
      </form>
    </Form>
  );
}
