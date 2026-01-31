import {
  getCouponsListQueryKey,
  useUpdateCoupon,
} from "@/api/endpoints/coupons/coupons";
import type { Coupon } from "@/api/models";
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
import { getErrorSummary } from "@/lib/api/errors";
import { isZeroDecimalCurrency } from "@/lib/currency";
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
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

export function CouponEditSheet({
  coupon,
  onSuccess,
}: {
  coupon: Coupon;
  onSuccess?: (coupon: Coupon) => void;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: coupon.name,
    },
  });

  const { isPending, mutateAsync } = useUpdateCoupon({
    mutation: {
      onSuccess: async (coupon) => {
        await queryClient.invalidateQueries({
          queryKey: getCouponsListQueryKey(),
        });
        onSuccess?.(coupon);
        toast.success("Coupon updated");
        popModal();
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
      id: coupon.id,
      data: {
        name: values.name,
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Update coupon</FormSheetTitle>
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

            <div className="grid gap-2">
              <FormLabel>Type</FormLabel>
              <Select value={coupon.amount ? "amount" : "percentage"} disabled>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="amount">Fixed amount</SelectItem>
                  <SelectItem value="percentage">Percentage</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {coupon.amount ? (
              <div className="grid gap-2">
                <FormLabel>Amount</FormLabel>
                <div className="flex">
                  <CurrencyInput
                    placeholder="0"
                    className={cn(inputClassName, "rounded-r-none")}
                    value={coupon.amount as string}
                    allowNegativeValue={false}
                    decimalsLimit={
                      isZeroDecimalCurrency(coupon.currency) ? 0 : 2
                    }
                    allowDecimals={!isZeroDecimalCurrency(coupon.currency)}
                    maxLength={19}
                    disableAbbreviations={true}
                    disabled
                  />
                  <div className="mt-auto w-24">
                    <CurrencyCombobox selected={coupon.currency}>
                      <ComboboxButton className="rounded-l-none" disabled>
                        {coupon.currency}
                      </ComboboxButton>
                    </CurrencyCombobox>
                  </div>
                </div>
              </div>
            ) : (
              <div className="grid gap-2">
                <FormLabel>Percentage</FormLabel>
                <div className="relative">
                  <CurrencyInput
                    placeholder="10"
                    className={inputClassName}
                    value={coupon.percentage as string}
                    maxLength={3}
                    decimalsLimit={1}
                    allowNegativeValue={false}
                    disableAbbreviations={true}
                    disabled
                  />
                  <div className="text-muted-foreground absolute inset-y-0 end-0 flex items-center pe-3 text-sm">
                    %
                  </div>
                </div>
              </div>
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
