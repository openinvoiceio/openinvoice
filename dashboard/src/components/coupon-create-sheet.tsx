import {
  getCouponsListQueryKey,
  useCreateCoupon,
} from "@/api/endpoints/coupons/coupons";
import { CurrencyEnum, type Coupon } from "@/api/models";
import { CurrencyCombobox } from "@/components/currency-combobox.tsx";
import { popModal } from "@/components/push-modals";
import { Button } from "@/components/ui/button";
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
  FormSheetContent,
  FormSheetDescription,
  FormSheetFooter,
  FormSheetGroup,
  FormSheetHeader,
  FormSheetTitle,
} from "@/components/ui/form-sheet";
import { Input, inputClassName } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select.tsx";
import { Spinner } from "@/components/ui/spinner";
import { useActiveAccount } from "@/hooks/use-active-account";
import { getErrorSummary } from "@/lib/api/errors";
import { isZeroDecimalCurrency, sanitizeCurrencyAmount } from "@/lib/currency";
import { cn } from "@/lib/utils";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useId } from "react";
import CurrencyInput from "react-currency-input-field";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  currency: z.enum(CurrencyEnum),
  amount: z.string(),
  percentage: z.string(),
  type: z.string(),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

export function CouponCreateSheet({
  name,
  currency: defaultCurrency,
  onSuccess,
}: {
  name?: string;
  currency?: CurrencyEnum;
  onSuccess?: (coupon: Coupon) => void;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const { account } = useActiveAccount();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: name || "",
      currency: defaultCurrency || account.default_currency,
      amount: "0",
      percentage: "",
      type: "amount",
    },
  });
  const currency = form.watch("currency");
  const type = form.watch("type");

  const { isPending, mutateAsync } = useCreateCoupon({
    mutation: {
      onSuccess: async (coupon) => {
        await queryClient.invalidateQueries({
          queryKey: getCouponsListQueryKey(),
        });
        onSuccess?.(coupon);
        toast.success("Coupon created");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  function onTypeChange(value: string) {
    form.setValue("type", value);
    if (value === "amount") {
      form.setValue("amount", "0");
      form.setValue("percentage", "");
    } else {
      form.setValue("amount", "");
      form.setValue("percentage", "0");
    }
  }

  async function onSubmit(values: FormValuesInput) {
    if (isPending) return;
    await mutateAsync({
      data: {
        name: values.name,
        currency: values.currency,
        amount: values.type === "amount" ? values.amount : null,
        percentage: values.type === "percentage" ? values.percentage : null,
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Create Coupon</FormSheetTitle>
        <FormSheetDescription>
          Coupons can be applied to invoices for discounts.
        </FormSheetDescription>
      </FormSheetHeader>
      <Form {...form}>
        <form id={formId} onSubmit={form.handleSubmit(onSubmit)}>
          <FormSheetGroup>
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input type="text" placeholder="Enter name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Type</FormLabel>
                  <FormControl>
                    <Select
                      value={field.value}
                      onValueChange={(value) => {
                        field.onChange(value);
                        onTypeChange(value);
                      }}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="amount">Fixed amount</SelectItem>
                        <SelectItem value="percentage">Percentage</SelectItem>
                      </SelectContent>
                    </Select>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {type === "amount" ? (
              <div className="grid gap-2">
                <FormLabel>Amount</FormLabel>
                <div className="flex">
                  <FormField
                    control={form.control}
                    name="amount"
                    render={({ field }) => (
                      <FormItem className="flex-1">
                        <FormControl>
                          <CurrencyInput
                            name={field.name}
                            placeholder="0"
                            className={cn(inputClassName, "rounded-r-none")}
                            value={field.value}
                            onValueChange={(value) => field.onChange(value)}
                            allowNegativeValue={false}
                            decimalsLimit={
                              isZeroDecimalCurrency(currency) ? 0 : 2
                            }
                            allowDecimals={!isZeroDecimalCurrency(currency)}
                            maxLength={19}
                            disableAbbreviations={true}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="currency"
                    render={({ field }) => (
                      <FormItem className="mt-auto w-24">
                        <FormControl>
                          <CurrencyCombobox
                            align="end"
                            selected={field.value}
                            onSelect={async (value) => {
                              const code = value ?? "";
                              field.onChange(code);
                              const amount = form.getValues("amount");
                              form.setValue(
                                "amount",
                                sanitizeCurrencyAmount(amount, code),
                              );
                            }}
                          >
                            <ComboboxButton className="rounded-l-none">
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
                </div>
              </div>
            ) : (
              <FormField
                control={form.control}
                name="percentage"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Percentage</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <CurrencyInput
                          placeholder="10"
                          className={inputClassName}
                          value={field.value}
                          onValueChange={(value) => {
                            field.onChange(value || "0");
                          }}
                          maxLength={3}
                          decimalsLimit={1}
                          allowNegativeValue={false}
                          disableAbbreviations={true}
                        />
                        <div className="text-muted-foreground absolute inset-y-0 end-0 flex items-center pe-3 text-sm">
                          %
                        </div>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}
          </FormSheetGroup>
        </form>
      </Form>
      <FormSheetFooter>
        <Button type="submit" form={formId} disabled={isPending}>
          {isPending && <Spinner />}
          Submit
        </Button>
      </FormSheetFooter>
    </FormSheetContent>
  );
}
