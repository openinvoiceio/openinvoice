import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
  useUpdateInvoice,
} from "@/api/endpoints/invoices/invoices";
import { useNumberingSystemsRetrieve } from "@/api/endpoints/numbering-systems/numbering-systems";
import { NumberingSystemAppliesToEnum, type Invoice } from "@/api/models";
import { NumberingSystemCombobox } from "@/components/numbering-system-combobox.tsx";
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
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Input } from "@/components/ui/input";
import { useDebouncedCallback } from "@/hooks/use-debounced-callback";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import z from "zod";

const schema = z.object({
  number: z.string(),
  numbering_system_id: z.uuid().nullable(),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

export function InvoiceNumberingCard({ invoice }: { invoice: Invoice }) {
  const queryClient = useQueryClient();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      number: invoice.number || "",
      numbering_system_id: invoice.numbering_system_id,
    },
  });
  const numberingSystemId = form.watch("numbering_system_id");
  const { data: numberingSystem } = useNumberingSystemsRetrieve(
    numberingSystemId || "",
    { query: { enabled: !!numberingSystemId } },
  );

  const { isPending, mutateAsync } = useUpdateInvoice({
    mutation: {
      onSuccess: async ({ id, number }) => {
        form.setValue("number", number || "");
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
        number: values.numbering_system_id ? null : values.number || null,
        numbering_system_id: values.numbering_system_id || null,
      },
    });
  }

  const submit = form.handleSubmit(onSubmit);
  const debouncedSubmit = useDebouncedCallback(() => submit(), 500);

  return (
    <Form {...form}>
      <form>
        <FormCard className="pb-4">
          <FormCardHeader>
            <FormCardTitle>Numbering</FormCardTitle>
            <FormCardDescription>
              Configure invoice number and numbering system
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent className="md:grid-cols-2">
            <FormField
              control={form.control}
              name="number"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Number</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Enter number"
                      disabled={!!numberingSystemId}
                      {...field}
                      onChange={(e) => {
                        field.onChange(e);
                        debouncedSubmit();
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    Unique number for the invoice document
                  </FormDescription>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="numbering_system_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Numbering system</FormLabel>
                  <FormControl>
                    <NumberingSystemCombobox
                      appliesTo={NumberingSystemAppliesToEnum.invoice}
                      selected={numberingSystem}
                      onSelect={async (selected) => {
                        field.onChange(selected ? selected.id : null);
                        await submit();
                      }}
                    >
                      <ComboboxButton>
                        {numberingSystem ? (
                          <span>{numberingSystem.description}</span>
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
                    This is used to generate invoice number. To manually enter
                    the invoice number leave this empty
                  </FormDescription>
                </FormItem>
              )}
            />
          </FormCardContent>
        </FormCard>
      </form>
    </Form>
  );
}
