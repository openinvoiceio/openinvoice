import {
  getBillingProfilesListQueryKey,
  useCreateBillingProfile,
} from "@/api/endpoints/billing-profiles/billing-profiles";
import { CountryEnum, type BillingProfile } from "@/api/models";
import { AddressCountryField } from "@/components/fields/address-country-field";
import { AddressLine1Field } from "@/components/fields/address-line1-field";
import { AddressLine2Field } from "@/components/fields/address-line2-field";
import { AddressLocalityField } from "@/components/fields/address-locality-field";
import { AddressPostalCodeField } from "@/components/fields/address-postal-code-field";
import { AddressStateField } from "@/components/fields/address-state-field";
import { popModal } from "@/components/push-modals";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  FormSheetContent,
  FormSheetDescription,
  FormSheetFooter,
  FormSheetGroup,
  FormSheetHeader,
  FormSheetTitle,
} from "@/components/ui/form-sheet";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { MAX_TAX_IDS } from "@/config/tax-ids";
import { CustomerTaxIdsCombobox } from "@/features/customers/components/customer-tax-ids-combobox";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useId } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  legal_name: z.string().optional(),
  legal_number: z.string().optional(),
  email: z.email("Invalid email address").optional(),
  phone: z.string().optional(),
  tax_ids: z.array(z.string()).optional(),
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

export function BillingProfileCreateSheet({
  customerId,
  onSuccess,
}: {
  customerId: string;
  onSuccess?: (profile: BillingProfile) => void;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      legal_name: "",
      legal_number: "",
      email: "",
      phone: "",
      tax_ids: [],
      address: {
        line1: "",
        line2: "",
        locality: "",
        state: "",
        postalCode: "",
        country: undefined,
      },
    },
  });
  const selectedTaxIds = form.watch("tax_ids") ?? [];
  const taxIdsLimitReached = selectedTaxIds.length >= MAX_TAX_IDS;
  const { mutateAsync, isPending } = useCreateBillingProfile({
    mutation: {
      onSuccess: async (profile) => {
        await queryClient.invalidateQueries({
          queryKey: getBillingProfilesListQueryKey(),
        });
        onSuccess?.(profile);
        toast.success("Billing profile created");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      data: {
        customer_id: customerId,
        legal_name: values.legal_name || null,
        legal_number: values.legal_number || null,
        email: values.email || null,
        phone: values.phone || null,
        tax_ids: values.tax_ids ?? [],
        address: {
          line1: values.address.line1 || null,
          line2: values.address.line2 || null,
          locality: values.address.locality || null,
          state: values.address.state || null,
          postal_code: values.address.postalCode || null,
          country: values.address.country || null,
        },
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Create billing profile</FormSheetTitle>
        <FormSheetDescription>
          Add billing details for this customer.
        </FormSheetDescription>
      </FormSheetHeader>
      <Form {...form}>
        <form id={formId} onSubmit={form.handleSubmit(onSubmit)}>
          <FormSheetGroup>
            <FormField
              control={form.control}
              name="legal_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Legal name</FormLabel>
                  <FormControl>
                    <Input placeholder="Acme Corporation LLC" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="legal_number"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Legal number</FormLabel>
                  <FormControl>
                    <Input placeholder="123456789" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormSheetGroup>
          <FormSheetGroup>
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      placeholder="name@example.com"
                      autoCapitalize="none"
                      autoComplete="email"
                      autoCorrect="off"
                      {...field}
                    />
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
          </FormSheetGroup>
          <FormSheetGroup>
            <FormField
              control={form.control}
              name="tax_ids"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tax IDs</FormLabel>
                  <FormControl>
                    <CustomerTaxIdsCombobox
                      customerId={customerId}
                      value={field.value ?? []}
                      onChange={field.onChange}
                      multiple
                    />
                  </FormControl>
                  <FormDescription>
                    {taxIdsLimitReached
                      ? `Limit reached (${MAX_TAX_IDS} tax ids).`
                      : "Select tax IDs to apply by default."}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormSheetGroup>
          <FormSheetGroup>
            <AddressLine1Field name="address.line1" />
            <AddressLine2Field name="address.line2" />
          </FormSheetGroup>
          <FormSheetGroup className="grid-cols-2">
            <AddressLocalityField name="address.locality" />
            <AddressPostalCodeField name="address.postalCode" />
          </FormSheetGroup>
          <FormSheetGroup className="grid-cols-2">
            <AddressCountryField name="address.country" />
            <AddressStateField
              name="address.state"
              countryName="address.country"
            />
          </FormSheetGroup>
        </form>
      </Form>
      <FormSheetFooter>
        <Button type="submit" form={formId} disabled={isPending}>
          {isPending && <Spinner />}
          Submit
        </Button>
      </FormSheetFooter>
    </FormSheetContent>
  );
}
