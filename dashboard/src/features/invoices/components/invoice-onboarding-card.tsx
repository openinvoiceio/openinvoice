import { useCustomersRetrieve } from "@/api/endpoints/customers/customers";
import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  useCreateInvoice,
} from "@/api/endpoints/invoices/invoices.ts";
import { CurrencyEnum, type Customer } from "@/api/models";
import { CurrencyCombobox } from "@/components/currency-combobox.tsx";
import { Button } from "@/components/ui/button.tsx";
import {
  ComboboxButton,
  ComboboxButtonAvatar,
} from "@/components/ui/combobox-button.tsx";
import {
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardFooter,
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card.tsx";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form.tsx";
import { CustomerCombobox } from "@/features/customers/components/customer-combobox";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { UserIcon } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  customer_id: z.uuid(),
  currency: z.enum(CurrencyEnum).optional(),
});

type FormValues = z.infer<typeof schema>;

export function InvoiceOnboardingCard({
  firstCustomer,
  currency,
}: {
  firstCustomer?: Customer;
  currency?: CurrencyEnum;
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      customer_id: firstCustomer?.id,
      currency,
    },
  });
  const customerId = form.watch("customer_id");
  const { data: customer } = useCustomersRetrieve(customerId, {
    query: { enabled: !!customerId },
  });

  const { mutateAsync, isPending } = useCreateInvoice({
    mutation: {
      onSuccess: async (invoice) => {
        await queryClient.invalidateQueries({
          queryKey: getInvoicesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getInvoicesRetrieveQueryKey(invoice.id),
        });
        toast.success("Invoice created", {
          action: {
            label: "Edit",
            onClick: () =>
              navigate({
                to: "/invoices/$id/edit",
                params: { id: invoice.id },
              }),
          },
        });
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      data: {
        customer_id: values.customer_id,
        currency: values.currency || null,
      },
    });
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormCard>
          <FormCardHeader>
            <FormCardTitle>Issue an invoice</FormCardTitle>
            <FormCardDescription>
              Create your first invoice and start editing it.
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent className="md:grid-cols-2">
            <FormField
              control={form.control}
              name="customer_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Customer</FormLabel>
                  <FormControl>
                    <CustomerCombobox
                      selected={customer}
                      onSelect={async (selected) => {
                        if (!selected) return;
                        field.onChange(selected.id);
                      }}
                    >
                      <ComboboxButton>
                        {customer ? (
                          <>
                            <ComboboxButtonAvatar src={customer.logo_url}>
                              <UserIcon />
                            </ComboboxButtonAvatar>
                            <span>{customer.name}</span>
                          </>
                        ) : (
                          <span className="text-muted-foreground">
                            Select customer
                          </span>
                        )}
                      </ComboboxButton>
                    </CustomerCombobox>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="currency"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Currency</FormLabel>
                  <FormControl>
                    <CurrencyCombobox
                      selected={field.value || null}
                      onSelect={async (code) =>
                        field.onChange(code || undefined)
                      }
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
                </FormItem>
              )}
            />
          </FormCardContent>
          <FormCardFooter>
            <Button type="submit">Issue</Button>
          </FormCardFooter>
        </FormCard>
      </form>
    </Form>
  );
}
