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
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardFooter,
  FormCardHeader,
  FormCardSeparator,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  name: z.string().optional(),
  phone: z.string().optional(),
  address: z.object({
    line1: z.string().optional(),
    line2: z.string().optional(),
    locality: z.string().optional(),
    state: z.string().optional(),
    postalCode: z.string().optional(),
    country: z.enum(CountryEnum).optional(),
  }),
});

type FormValues = z.infer<typeof schema>;

export function CustomerShippingCard({ customer }: { customer: Customer }) {
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: customer.shipping?.name || "",
      phone: customer.shipping?.phone || "",
      address: {
        line1: customer.shipping?.address?.line1 || "",
        line2: customer.shipping?.address?.line2 || "",
        locality: customer.shipping?.address?.locality || "",
        state: customer.shipping?.address?.state || "",
        postalCode: customer.shipping?.address?.postal_code || "",
        country: customer.shipping?.address?.country || undefined,
      },
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
        shipping: {
          name: values.name || null,
          phone: values.phone || null,
          address: {
            line1: values.address.line1 || null,
            line2: values.address.line2 || null,
            locality: values.address.locality || null,
            state: values.address.state || null,
            postal_code: values.address.postalCode || null,
            country: values.address.country || null,
          },
        },
      },
    });
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormCard>
          <FormCardHeader>
            <FormCardTitle>Shipping</FormCardTitle>
            <FormCardDescription>
              Manage shipping contact details and address.
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent>
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Recipient name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="phone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Phone</FormLabel>
                  <FormControl>
                    <Input placeholder="+1234567890" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormCardContent>
          <FormCardSeparator />
          <FormCardContent>
            <AddressLine1Field name="address.line1" />
            <AddressLine2Field name="address.line2" />
          </FormCardContent>
          <FormCardSeparator />
          <FormCardContent className="grid-cols-2">
            <AddressLocalityField name="address.locality" />
            <AddressPostalCodeField name="address.postalCode" />
          </FormCardContent>
          <FormCardSeparator />
          <FormCardContent className="grid-cols-2">
            <AddressCountryField name="address.country" />
            <AddressStateField
              name="address.state"
              countryName="address.country"
            />
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
