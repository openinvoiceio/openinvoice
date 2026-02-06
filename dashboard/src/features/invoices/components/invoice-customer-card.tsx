import { useBillingProfilesRetrieve } from "@/api/endpoints/billing-profiles/billing-profiles";
import { useCustomersRetrieve } from "@/api/endpoints/customers/customers";
import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
  useUpdateInvoice,
} from "@/api/endpoints/invoices/invoices";
import { type Invoice } from "@/api/models";
import { Button } from "@/components/ui/button";
import {
  ComboboxButton,
  ComboboxButtonAvatar,
} from "@/components/ui/combobox-button.tsx";
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
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card";
import { BillingProfileCombobox } from "@/features/customers/components/billing-profile-combobox";
import { CustomerCombobox } from "@/features/customers/components/customer-combobox.tsx";
import { CustomerDropdown } from "@/features/customers/components/customer-dropdown";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { MoreHorizontalIcon, UserIcon } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import z from "zod";

const schema = z.object({
  customer_id: z.string().uuid().nullable().optional(),
  billing_profile_id: z.string().uuid().nullable().optional(),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

export function InvoiceCustomerCard({ invoice }: { invoice: Invoice }) {
  const queryClient = useQueryClient();
  const invoiceCustomerId = (invoice as { customer_id?: string }).customer_id;
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      customer_id: invoiceCustomerId ?? null,
      billing_profile_id: invoice.billing_profile?.id ?? null,
    },
  });
  const customerId = form.watch("customer_id");
  const billingProfileId = form.watch("billing_profile_id");
  const { data: customer } = useCustomersRetrieve(customerId || "", {
    query: { enabled: !!customerId },
  });
  const { data: billingProfile } = useBillingProfilesRetrieve(
    billingProfileId || "",
    { query: { enabled: !!billingProfileId } },
  );
  const isRevision = !!invoice.previous_revision_id;

  const { isPending, mutateAsync } = useUpdateInvoice({
    mutation: {
      onSuccess: async ({ id }) => {
        await queryClient.invalidateQueries({
          queryKey: getInvoicesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getInvoicesRetrieveQueryKey(id),
        });
        await queryClient.invalidateQueries({
          queryKey: getPreviewInvoiceQueryKey(id),
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  async function onSubmit(values: FormValuesInput) {
    if (isPending) return;

    await mutateAsync({
      id: invoice.id,
      data: {
        ...(values.customer_id ? { customer_id: values.customer_id } : {}),
        billing_profile_id: values.billing_profile_id || undefined,
      },
    });
  }

  const submit = form.handleSubmit(onSubmit);

  return (
    <Form {...form}>
      <form>
        <FormCard className="pb-4">
          <FormCardHeader>
            <FormCardTitle>Customer</FormCardTitle>
            <FormCardDescription>
              Choose a customer for this invoice.
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent className="grid-cols-2 gap-2">
            <FormField
              control={form.control}
              name="customer_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Customer</FormLabel>
                  <FormControl>
                    <CustomerCombobox
                      selected={customer}
                      onSelect={
                        isRevision
                          ? undefined
                          : async (selected) => {
                              if (!selected) return;
                              field.onChange(selected.id);
                              form.setValue("billing_profile_id", null);
                              await submit();
                            }
                      }
                    >
                      <ComboboxButton disabled={isRevision}>
                        <ComboboxButtonAvatar src={customer?.logo_url}>
                          <UserIcon />
                        </ComboboxButtonAvatar>
                        <span>
                          {customer?.name || invoice.billing_profile.legal_name}
                        </span>
                      </ComboboxButton>
                    </CustomerCombobox>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {customer && (
              <CustomerDropdown customer={customer} actions={{ delete: false }}>
                <Button size="icon" variant="ghost">
                  <MoreHorizontalIcon />
                </Button>
              </CustomerDropdown>
            )}
            <FormField
              control={form.control}
              name="billing_profile_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Billing profile</FormLabel>
                  <FormControl>
                    <BillingProfileCombobox
                      customerId={customerId || undefined}
                      selected={billingProfile ?? null}
                      onSelect={async (selected) => {
                        if (!selected) return;
                        field.onChange(selected.id);
                        await submit();
                      }}
                    >
                      <ComboboxButton>
                        {billingProfile ? (
                          <span>{billingProfile.legal_name || "Untitled"}</span>
                        ) : (
                          <span className="text-muted-foreground">
                            Select billing profile
                          </span>
                        )}
                      </ComboboxButton>
                    </BillingProfileCombobox>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormCardContent>
        </FormCard>
      </form>
    </Form>
  );
}
