import { useNumberingSystemsRetrieve } from "@/api/endpoints/numbering-systems/numbering-systems";
import {
  getPreviewQuoteQueryKey,
  getQuotesListQueryKey,
  getQuotesRetrieveQueryKey,
  useUpdateQuote,
} from "@/api/endpoints/quotes/quotes";
import { NumberingSystemAppliesToEnum, type Quote } from "@/api/models";
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

export function QuoteNumberingCard({ quote }: { quote: Quote }) {
  const queryClient = useQueryClient();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      number: quote.number || "",
      numbering_system_id: quote.numbering_system_id,
    },
  });
  const numberingSystemId = form.watch("numbering_system_id");
  const { data: numberingSystem } = useNumberingSystemsRetrieve(
    numberingSystemId || "",
    { query: { enabled: !!numberingSystemId } },
  );

  const { isPending, mutateAsync } = useUpdateQuote({
    mutation: {
      onSuccess: async ({ id, number }) => {
        form.setValue("number", number || "");
        await queryClient.invalidateQueries({
          queryKey: getQuotesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getQuotesRetrieveQueryKey(id),
        });
        await queryClient.invalidateQueries({
          queryKey: getPreviewQuoteQueryKey(id),
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
      id: quote.id,
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
              Configure quote number and numbering system
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
                    Unique number for the quote document
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
                      appliesTo={NumberingSystemAppliesToEnum.quote}
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
                    This is used to generate quote number. To manually enter the
                    quote number leave this empty
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
