import {
  getShippingRatesListQueryKey,
  useCreateShippingRate,
} from "@/api/endpoints/shipping-rates/shipping-rates.ts";
import {
  CurrencyEnum,
  ShippingRateTaxPolicyEnum,
  type ShippingRate,
} from "@/api/models";
import { CurrencyCombobox } from "@/components/currency-combobox.tsx";
import { popModal } from "@/components/push-modals";
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
import { useActiveAccount } from "@/hooks/use-active-account.ts";
import { getErrorSummary } from "@/lib/api/errors";
import {
  isZeroDecimalCurrency,
  sanitizeCurrencyAmount,
} from "@/lib/currency.ts";
import { formatEnum } from "@/lib/formatters";
import { cn } from "@/lib/utils.ts";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useId } from "react";
import CurrencyInput from "react-currency-input-field";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  code: z.string().optional(),
  currency: z.enum(CurrencyEnum),
  amount: z.string(),
  tax_policy: z.enum(ShippingRateTaxPolicyEnum),
});

type FormValues = z.infer<typeof schema>;

export function ShippingRateCreateSheet({
  name,
  onSuccess,
}: {
  name?: string;
  onSuccess?: (shippingRate: ShippingRate) => void;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const { account } = useActiveAccount();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: name || "",
      code: "",
      currency: account.default_currency,
      amount: "0",
      tax_policy: ShippingRateTaxPolicyEnum.match_goods,
    },
  });
  const currency = form.watch("currency");

  const { isPending, mutateAsync } = useCreateShippingRate({
    mutation: {
      onSuccess: async (shippingRate) => {
        await queryClient.invalidateQueries({
          queryKey: getShippingRatesListQueryKey(),
        });
        onSuccess?.(shippingRate);
        toast.success("Shipping rate created");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      data: {
        name: values.name,
        code: values.code || null,
        currency: values.currency,
        amount: values.amount,
        tax_policy: values.tax_policy,
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Create Shipping Rate</FormSheetTitle>
        <FormSheetDescription>
          Define a new shipping rate for your account.
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
                    <Input type="text" placeholder="Shipping" {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    The shipping label shown on customer invoices.
                  </FormDescription>
                </FormItem>
              )}
            />
            <div className="flex">
              <FormField
                control={form.control}
                name="amount"
                render={({ field }) => (
                  <FormItem className="flex-1">
                    <FormLabel>Amount</FormLabel>
                    <FormControl>
                      <CurrencyInput
                        name={field.name}
                        placeholder="0"
                        className={cn(inputClassName, "rounded-r-none")}
                        value={field.value}
                        onValueChange={(value) => field.onChange(value)}
                        allowNegativeValue={false}
                        decimalsLimit={isZeroDecimalCurrency(currency) ? 0 : 2}
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
            <FormField
              control={form.control}
              name="tax_policy"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tax policy</FormLabel>
                  <FormControl>
                    <Select
                      value={field.value}
                      onValueChange={(value) => {
                        field.onChange(value);
                      }}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select tax policy" />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.values(ShippingRateTaxPolicyEnum).map(
                          (value) => (
                            <SelectItem key={value} value={value}>
                              {formatEnum(value)}
                            </SelectItem>
                          ),
                        )}
                      </SelectContent>
                    </Select>
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    Specify how taxes are calculated on this shipping rate.
                  </FormDescription>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="code"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Code</FormLabel>
                  <FormControl>
                    <Input type="text" placeholder="Enter code" {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    An internal code to identify the shipping rate.
                  </FormDescription>
                </FormItem>
              )}
            />
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
