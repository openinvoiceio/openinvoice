import {
  getCustomersListQueryKey,
  getCustomersRetrieveQueryKey,
  useUpdateCustomer,
} from "@/api/endpoints/customers/customers";
import { useNumberingSystemsRetrieve } from "@/api/endpoints/numbering-systems/numbering-systems";
import {
  CurrencyEnum,
  NumberingSystemAppliesToEnum,
  type Customer,
} from "@/api/models";
import { CurrencyCombobox } from "@/components/currency-combobox.tsx";
import { NumberingSystemCombobox } from "@/components/numbering-system-combobox";
import { Button } from "@/components/ui/button";
import { ComboboxButton } from "@/components/ui/combobox-button.tsx";
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
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardFooter,
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  currency: z.enum(CurrencyEnum).optional(),
  invoiceNumberingSystemId: z.string().uuid().nullable(),
  creditNoteNumberingSystemId: z.string().uuid().nullable(),
  netPaymentTerm: z
    .union([z.string(), z.number()])
    .transform((v) => (typeof v === "string" ? Number(v) : v))
    .pipe(z.number().int().min(0).max(365)),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

export function CustomerInvoicingCard({
  customer,
  ...props
}: Omit<React.ComponentProps<"form">, "onSubmit"> & {
  customer: Customer;
}) {
  const queryClient = useQueryClient();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      currency: customer.currency || undefined,
      invoiceNumberingSystemId: customer.invoice_numbering_system_id || null,
      creditNoteNumberingSystemId:
        customer.credit_note_numbering_system_id || null,
      netPaymentTerm: customer.net_payment_term || "",
    },
  });
  const invoiceNumberingSystemId = form.watch("invoiceNumberingSystemId");
  const creditNoteNumberingSystemId = form.watch("creditNoteNumberingSystemId");
  const { data: invoiceNumberingSystem } = useNumberingSystemsRetrieve(
    invoiceNumberingSystemId || "",
    { query: { enabled: !!invoiceNumberingSystemId } },
  );
  const { data: creditNoteNumberingSystem } = useNumberingSystemsRetrieve(
    creditNoteNumberingSystemId || "",
    { query: { enabled: !!creditNoteNumberingSystemId } },
  );
  const { mutateAsync, isPending } = useUpdateCustomer({
    mutation: {
      onSuccess: async ({ id }) => {
        await queryClient.invalidateQueries({
          queryKey: getCustomersListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getCustomersRetrieveQueryKey(id),
        });
        toast.success("Customer updated");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  async function onSubmit(values: FormValuesOutput) {
    if (isPending) return;
    await mutateAsync({
      id: customer.id,
      data: {
        currency: values.currency || null,
        invoice_numbering_system_id: values.invoiceNumberingSystemId || null,
        credit_note_numbering_system_id:
          values.creditNoteNumberingSystemId || null,
        net_payment_term: values.netPaymentTerm || null,
      },
    });
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} {...props}>
        <FormCard>
          <FormCardHeader>
            <FormCardTitle>Invoicing settings</FormCardTitle>
            <FormCardDescription>
              Configure invoicing settings for this customer. This will be used
              for generating invoices and billing.
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent className="grid-cols-2">
            <FormField
              control={form.control}
              name="currency"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Currency</FormLabel>
                  <FormControl>
                    <CurrencyCombobox
                      selected={field.value || null}
                      onSelect={async (code) => field.onChange(code || "")}
                    >
                      <ComboboxButton>
                        {field.value ? (
                          <span>{field.value}</span>
                        ) : (
                          <span className="text-muted-foreground">
                            Select currency
                          </span>
                        )}
                      </ComboboxButton>
                    </CurrencyCombobox>
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    Default currency in which the customer will be billed.
                  </FormDescription>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="netPaymentTerm"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Net payment term</FormLabel>
                  <FormControl>
                    <Input type="number" {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    The number of days within which this customer must pay the
                    invoice.
                  </FormDescription>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="invoiceNumberingSystemId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Invoice numbering system</FormLabel>
                  <FormControl>
                    <NumberingSystemCombobox
                      appliesTo={NumberingSystemAppliesToEnum.invoice}
                      selected={invoiceNumberingSystem ?? null}
                      onSelect={async (value) => {
                        field.onChange(value?.id ?? null);
                      }}
                    >
                      <ComboboxButton>
                        {invoiceNumberingSystem ? (
                          <span>{invoiceNumberingSystem.description}</span>
                        ) : (
                          <span className="text-muted-foreground">
                            Select numbering system
                          </span>
                        )}
                      </ComboboxButton>
                    </NumberingSystemCombobox>
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    Used to generate invoice numbers for this customer when not
                    specified manually.
                  </FormDescription>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="creditNoteNumberingSystemId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Credit note numbering system</FormLabel>
                  <FormControl>
                    <NumberingSystemCombobox
                      appliesTo={NumberingSystemAppliesToEnum.credit_note}
                      selected={creditNoteNumberingSystem ?? null}
                      onSelect={async (value) => {
                        field.onChange(value?.id ?? null);
                      }}
                    >
                      <ComboboxButton>
                        {creditNoteNumberingSystem ? (
                          <span>{creditNoteNumberingSystem.description}</span>
                        ) : (
                          <span className="text-muted-foreground">
                            Select numbering system
                          </span>
                        )}
                      </ComboboxButton>
                    </NumberingSystemCombobox>
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    Applied when issuing credit notes for this customer.
                  </FormDescription>
                </FormItem>
              )}
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
