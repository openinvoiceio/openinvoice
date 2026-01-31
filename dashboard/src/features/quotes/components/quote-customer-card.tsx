import { useCustomersRetrieve } from "@/api/endpoints/customers/customers";
import {
  getPreviewQuoteQueryKey,
  getQuotesListQueryKey,
  getQuotesRetrieveQueryKey,
  useUpdateQuote,
} from "@/api/endpoints/quotes/quotes";
import { type Quote } from "@/api/models";
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
  FormMessage,
} from "@/components/ui/form";
import {
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card";
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
  customer_id: z.uuid(),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

export function QuoteCustomerCard({ quote }: { quote: Quote }) {
  const queryClient = useQueryClient();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      customer_id: quote.customer.id,
    },
  });
  const customerId = form.watch("customer_id");
  const { data: customer } = useCustomersRetrieve(customerId);

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
        customer_id: values.customer_id,
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
              Choose a customer for this quote.
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent className="grid-cols-2 gap-2">
            <FormField
              control={form.control}
              name="customer_id"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <CustomerCombobox
                      selected={customer}
                      onSelect={async (selected) => {
                        if (!selected) return;
                        field.onChange(selected.id);
                        await submit();
                      }}
                    >
                      <ComboboxButton>
                        <ComboboxButtonAvatar src={customer?.logo_url}>
                          <UserIcon />
                        </ComboboxButtonAvatar>
                        <span>{customer?.name}</span>
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
          </FormCardContent>
        </FormCard>
      </form>
    </Form>
  );
}
