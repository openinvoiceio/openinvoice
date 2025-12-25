import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
  useUpdateInvoice,
} from "@/api/endpoints/invoices/invoices";
import { type Invoice } from "@/api/models";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
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
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select.tsx";
import { getErrorSummary } from "@/lib/api/errors";
import {
  formatDate,
  formatDueDate,
  formatISODate,
  formatNetPaymentTerm,
} from "@/lib/formatters";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { enUS } from "date-fns/locale";
import { CalendarIcon } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import z from "zod";

const options = [0, 1, 7, 14, 30, 60, 90, -1];

const schema = z.object({
  due_date: z.string().optional(),
  net_payment_term: z.int(),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

export function InvoicePaymentCollectionCard({
  invoice,
}: {
  invoice: Invoice;
}) {
  const queryClient = useQueryClient();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      due_date: invoice.due_date || undefined,
      net_payment_term: invoice.due_date ? -1 : invoice.net_payment_term,
    },
  });
  const netPaymentTerm = form.watch("net_payment_term");
  const isCustomDueDate = form.watch("due_date") !== undefined;
  const selectedOption = options.find((option) => option === netPaymentTerm)!;

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
        due_date: values.due_date || null,
        net_payment_term: Math.max(values.net_payment_term, 0),
      },
    });
  }

  const submit = form.handleSubmit(onSubmit);

  return (
    <Form {...form}>
      <form>
        <FormCard className="pb-4">
          <FormCardHeader>
            <FormCardTitle>Payment collection</FormCardTitle>
            <FormCardDescription>
              Configure payment collection settings for this invoice
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent className="md:grid-cols-2">
            <FormField
              control={form.control}
              name="net_payment_term"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Due date</FormLabel>
                  <FormControl>
                    <Select
                      value={field.value.toString()}
                      onValueChange={(value) => {
                        if (value === "-1") {
                          field.onChange(-1);
                          form.setValue("due_date", formatISODate(new Date()));
                        } else {
                          field.onChange(Number(value));
                          form.setValue("due_date", undefined);
                        }
                        void submit();
                      }}
                    >
                      <SelectTrigger className="w-full">
                        {formatDueDate(selectedOption)}
                      </SelectTrigger>
                      <SelectContent>
                        {options.map((value) => (
                          <SelectItem key={value} value={value.toString()}>
                            {formatNetPaymentTerm(value)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    Date due which the invoice must be paid by customer after
                    finalization.
                  </FormDescription>
                </FormItem>
              )}
            />
            {isCustomDueDate && (
              <FormField
                control={form.control}
                name="due_date"
                render={({ field }) => (
                  <FormItem>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          type="button"
                          variant="outline"
                          className="mt-5.5 justify-between font-normal"
                        >
                          {field.value ? (
                            formatDate(field.value)
                          ) : (
                            <span className="text-muted-foreground">
                              Select date
                            </span>
                          )}
                          <CalendarIcon className="text-muted-foreground" />
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0">
                        <Calendar
                          mode="single"
                          selected={
                            field.value ? new Date(field.value) : undefined
                          }
                          onDayClick={async (data) => {
                            field.onChange(formatISODate(data));
                            await submit();
                          }}
                          locale={enUS}
                        />
                      </PopoverContent>
                    </Popover>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}
          </FormCardContent>
        </FormCard>
      </form>
    </Form>
  );
}
