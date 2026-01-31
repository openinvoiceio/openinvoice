import {
  getPreviewQuoteQueryKey,
  getQuotesListQueryKey,
  getQuotesRetrieveQueryKey,
  useUpdateQuote,
} from "@/api/endpoints/quotes/quotes";
import { CurrencyEnum, type Quote } from "@/api/models";
import { CurrencyCombobox } from "@/components/currency-combobox.tsx";
import { ComboboxButton } from "@/components/ui/combobox-button.tsx";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form";
import {
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import z from "zod";

const schema = z.object({
  currency: z.enum(CurrencyEnum),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

export function QuoteCurrencyCard({ quote }: { quote: Quote }) {
  const queryClient = useQueryClient();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      currency: quote.currency || "",
    },
  });

  const { isPending, mutateAsync } = useUpdateQuote({
    mutation: {
      onSuccess: async ({ id }) => {
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
        currency: values.currency,
      },
    });
  }

  const submit = form.handleSubmit(onSubmit);

  return (
    <Form {...form}>
      <form>
        <FormCard className="pb-4">
          <FormCardHeader>
            <FormCardTitle>Currency</FormCardTitle>
            <FormCardDescription>
              Select the currency for this quote.
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent>
            <FormField
              control={form.control}
              name="currency"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <CurrencyCombobox
                      selected={field.value}
                      onSelect={async (value) => {
                        field.onChange(value ?? "");
                        await submit();
                      }}
                    >
                      <ComboboxButton className="w-1/2">
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
                    Selecting a new currency will clear all lines from the
                    quote.
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
