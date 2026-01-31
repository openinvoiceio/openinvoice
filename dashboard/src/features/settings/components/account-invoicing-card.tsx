import {
  getAccountsListQueryKey,
  getAccountsRetrieveQueryKey,
  useUpdateAccount,
} from "@/api/endpoints/accounts/accounts";
import { useNumberingSystemsRetrieve } from "@/api/endpoints/numbering-systems/numbering-systems";
import {
  CurrencyEnum,
  NumberingSystemAppliesToEnum,
  type Account,
} from "@/api/models";
import { CurrencyCombobox } from "@/components/currency-combobox.tsx";
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
  FormCardSeparator,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { NumberingSystemCombobox } from "@/features/settings/components/numbering-system-combobox";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import z from "zod";

const schema = z.object({
  defaultCurrency: z.enum(CurrencyEnum),
  invoiceFooter: z.string().max(500).optional(),
  invoiceNumberingSystemId: z.string().uuid().nullable(),
  creditNoteNumberingSystemId: z.string().uuid().nullable(),
  netPaymentTerm: z
    .union([z.string(), z.number()])
    .transform((v) => (typeof v === "string" ? Number(v) : v))
    .pipe(z.number().int().min(0).max(365)),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

export function AccountInvoicingCard({ account }: { account: Account }) {
  const queryClient = useQueryClient();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      defaultCurrency: account.default_currency,
      invoiceFooter: account.invoice_footer || "",
      invoiceNumberingSystemId: account.invoice_numbering_system_id || null,
      creditNoteNumberingSystemId:
        account.credit_note_numbering_system_id || null,
      netPaymentTerm: account.net_payment_term,
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
  const { mutateAsync, isPending } = useUpdateAccount({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getAccountsListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getAccountsRetrieveQueryKey(account.id),
        });
        toast.success("Account updated");
      },
      onError: async (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  async function onSubmit(values: FormValuesOutput) {
    if (isPending) return;
    await mutateAsync({
      id: account.id,
      data: {
        default_currency: values.defaultCurrency,
        invoice_footer: values.invoiceFooter || null,
        invoice_numbering_system_id: values.invoiceNumberingSystemId || null,
        credit_note_numbering_system_id:
          values.creditNoteNumberingSystemId || null,
        net_payment_term: values.netPaymentTerm,
      },
    });
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormCard>
          <FormCardHeader>
            <FormCardTitle>Invoicing settings</FormCardTitle>
            <FormCardDescription>
              Configure your invoicing preferences, including default currency,
              invoice footer, and payment terms.
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent className="grid-cols-2">
            <FormField
              control={form.control}
              name="defaultCurrency"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Currency</FormLabel>
                  <FormControl>
                    <CurrencyCombobox
                      selected={field.value}
                      onSelect={async (value) => field.onChange(value ?? "")}
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
                    The default currency for your invoices. This will be used
                    for all operations unless specified otherwise.
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
                    The default number of days within which the customer must
                    pay the invoice.
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
                    Used to generate invoice numbers when one is not provided.
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
                    Applied when creating credit notes without a manual number.
                  </FormDescription>
                </FormItem>
              )}
            />
          </FormCardContent>
          <FormCardSeparator />
          <FormCardContent>
            <FormField
              control={form.control}
              name="invoiceFooter"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Invoice footer</FormLabel>
                  <FormControl>
                    <Textarea {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    Default footer text that will appear on your invoices. This
                    can include payment instructions, terms, or any other
                    relevant information.
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
