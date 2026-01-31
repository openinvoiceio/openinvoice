import {
  getCreditNotesListQueryKey,
  getCreditNotesRetrieveQueryKey,
  getPreviewCreditNoteQueryKey,
  useUpdateCreditNote,
} from "@/api/endpoints/credit-notes/credit-notes";
import { useInvoicesRetrieve } from "@/api/endpoints/invoices/invoices.ts";
import {
  CreditNoteReasonEnum,
  InvoiceStatusEnum,
  type CreditNote,
} from "@/api/models";
import { ComboboxButton } from "@/components/ui/combobox-button.tsx";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { InvoiceCombobox } from "@/features/invoices/components/invoice-combobox.tsx";
import { getErrorSummary } from "@/lib/api/errors";
import { formatEnum } from "@/lib/formatters.ts";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  invoice_id: z.uuid(),
  reason: z.custom<CreditNoteReasonEnum>(),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

export function CreditNoteInvoiceCard({
  creditNote,
}: {
  creditNote: CreditNote;
}) {
  const queryClient = useQueryClient();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      invoice_id: creditNote.invoice_id,
      reason: creditNote.reason,
    },
  });

  const invoiceId = form.watch("invoice_id");
  const { data: invoice } = useInvoicesRetrieve(invoiceId);

  const { isPending, mutateAsync } = useUpdateCreditNote({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getCreditNotesRetrieveQueryKey(creditNote.id),
        });
        await queryClient.invalidateQueries({
          queryKey: getCreditNotesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getPreviewCreditNoteQueryKey(creditNote.id),
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  async function onSubmit(values: FormValuesInput) {
    if (isPending) return;
    await mutateAsync({
      id: creditNote.id,
      data: {
        reason: values.reason,
      },
    });
  }

  const submit = form.handleSubmit(onSubmit);

  return (
    <Form {...form}>
      <form>
        <FormCard className="pb-4">
          <FormCardHeader>
            <FormCardTitle>Credited for</FormCardTitle>
            <FormCardDescription>Invoice to be credited</FormCardDescription>
          </FormCardHeader>
          <FormCardContent className="md:grid-cols-2">
            <FormField
              control={form.control}
              name="invoice_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Invoice</FormLabel>
                  <FormControl>
                    <InvoiceCombobox
                      selected={invoice}
                      onSelect={async (selected) => {
                        if (!selected) return;
                        field.onChange(selected.id);
                        await submit();
                      }}
                      status={[InvoiceStatusEnum.open, InvoiceStatusEnum.paid]}
                      minOutstandingAmount={0.01}
                    >
                      <ComboboxButton>
                        <span>{invoice?.number}</span>
                      </ComboboxButton>
                    </InvoiceCombobox>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="reason"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Reason</FormLabel>
                  <FormControl>
                    <Select
                      value={field.value}
                      onValueChange={async (value) => {
                        field.onChange(value as CreditNoteReasonEnum);
                        await submit();
                      }}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select reason">
                          {formatEnum(field.value)}
                        </SelectValue>
                      </SelectTrigger>
                      <SelectContent>
                        {Object.values(CreditNoteReasonEnum).map((value) => (
                          <SelectItem key={value} value={value}>
                            {formatEnum(value)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
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
