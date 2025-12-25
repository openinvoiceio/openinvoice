import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
} from "@/api/endpoints/invoices/invoices";
import {
  getPaymentsListQueryKey,
  useRecordPayment,
} from "@/api/endpoints/payments/payments";
import type { Invoice } from "@/api/models";
import { popModal } from "@/components/push-modals";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogGroup,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input, inputClassName } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Spinner } from "@/components/ui/spinner";
import { getErrorSummary } from "@/lib/api/errors";
import { isZeroDecimalCurrency } from "@/lib/currency";
import { formatDatetime } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { CalendarIcon, ClockIcon } from "lucide-react";
import CurrencyInput from "react-currency-input-field";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import z from "zod";

const schema = z.object({
  amount: z.string().min(1, "Amount is required"),
  transaction_id: z.string().optional(),
  description: z.string().optional(),
  received_at: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export function PaymentRecordDialog({ invoice }: { invoice: Invoice }) {
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      amount: invoice.outstanding_amount,
      transaction_id: "",
      description: "",
      received_at: "",
    },
  });

  const { mutateAsync, isPending } = useRecordPayment({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getInvoicesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getInvoicesRetrieveQueryKey(invoice.id),
        });
        await queryClient.invalidateQueries({
          queryKey: getPaymentsListQueryKey(),
        });
        toast.success("Payment recorded");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      data: {
        invoice_id: invoice.id,
        amount: values.amount,
        currency: invoice.currency,
        transaction_id: values.transaction_id || undefined,
        description: values.description || undefined,
        received_at: values.received_at || undefined,
      },
    });
  }

  return (
    <DialogContent>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Record payment</DialogTitle>
          </DialogHeader>
          <DialogGroup>
            <FormField
              control={form.control}
              name="amount"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Amount</FormLabel>
                  <FormControl>
                    <div className="flex">
                      <CurrencyInput
                        name={field.name}
                        placeholder="0"
                        className={cn(inputClassName, "rounded-r-none")}
                        value={field.value}
                        onValueChange={(value) => field.onChange(value)}
                        allowNegativeValue={false}
                        decimalsLimit={
                          isZeroDecimalCurrency(invoice.currency) ? 0 : 2
                        }
                        allowDecimals={!isZeroDecimalCurrency(invoice.currency)}
                        maxLength={19}
                        disableAbbreviations={true}
                      />
                      <Button
                        type="button"
                        variant="secondary"
                        className="border-input rounded-l-none border"
                        disabled
                      >
                        {invoice.currency}
                      </Button>
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="transaction_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Transaction ID</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormDescription>
                    Optional identifier from your payment provider.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormDescription>
                    Optional notes that will be stored with the payment.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="received_at"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Received at</FormLabel>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        type="button"
                        variant="outline"
                        className="justify-between font-normal"
                      >
                        {field.value ? (
                          formatDatetime(field.value)
                        ) : (
                          <span className="text-muted-foreground">
                            Select time
                          </span>
                        )}
                        <CalendarIcon className="text-muted-foreground" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        className="p-2"
                        selected={
                          field.value ? new Date(field.value) : new Date()
                        }
                        onSelect={(selected) => {
                          if (selected) {
                            const current = field.value
                              ? new Date(field.value)
                              : new Date();
                            selected.setHours(
                              current.getHours(),
                              current.getMinutes(),
                              current.getSeconds(),
                            );
                            field.onChange(selected.toISOString());
                          } else {
                            field.onChange("");
                          }
                        }}
                      />
                      <div className="border-t p-2">
                        <div className="relative grow">
                          <Input
                            type="time"
                            step="1"
                            defaultValue="12:00:00"
                            className="appearance-none ps-9 [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-calendar-picker-indicator]:appearance-none"
                            onChange={(e) => {
                              const [h, m, s] = e.target.value
                                .split(":")
                                .map(Number);
                              const base = field.value
                                ? new Date(field.value)
                                : new Date();
                              base.setHours(h, m, s || 0);
                              field.onChange(base.toISOString());
                            }}
                          />
                          <div className="text-muted-foreground pointer-events-none absolute inset-y-0 start-0 flex items-center justify-center ps-3">
                            <ClockIcon className="size-4" />
                          </div>
                        </div>
                      </div>
                    </PopoverContent>
                  </Popover>
                  <FormDescription>
                    Optional date and time when the payment was received.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </DialogGroup>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="secondary" disabled={isPending}>
                Cancel
              </Button>
            </DialogClose>
            <Button type="submit" disabled={isPending}>
              {isPending && <Spinner />}
              Submit
            </Button>
          </DialogFooter>
        </form>
      </Form>
    </DialogContent>
  );
}
