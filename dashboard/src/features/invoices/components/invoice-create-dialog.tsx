import { useCouponsRetrieve } from "@/api/endpoints/coupons/coupons";
import { useCustomersRetrieve } from "@/api/endpoints/customers/customers";
import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
  useCreateInvoice,
} from "@/api/endpoints/invoices/invoices";
import { useNumberingSystemsRetrieve } from "@/api/endpoints/numbering-systems/numbering-systems";
import { useTaxRatesRetrieve } from "@/api/endpoints/tax-rates/tax-rates";
import {
  CouponsListStatus,
  CurrencyEnum,
  NumberingSystemsListAppliesTo,
  NumberingSystemsListStatus,
  TaxRatesListStatus,
  type Customer,
} from "@/api/models";
import { CurrencyCombobox } from "@/components/currency-combobox";
import { popModal } from "@/components/push-modals.tsx";
import { Button } from "@/components/ui/button";
import {
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Form } from "@/components/ui/form.tsx";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select.tsx";
import { Spinner } from "@/components/ui/spinner";
import { CouponCombobox } from "@/features/coupons/components/coupon-combobox";
import { CustomerCombobox } from "@/features/customers/components/customer-combobox";
import { NumberingSystemCombobox } from "@/features/settings/components/numbering-system-combobox";
import { TaxRateCombobox } from "@/features/tax-rates/components/tax-rate-combobox";
import { useActiveAccount } from "@/hooks/use-active-account";
import { getErrorSummary } from "@/lib/api/errors";
import { formatDueDate, formatNetPaymentTerm } from "@/lib/formatters";
import { cn } from "@/lib/utils.ts";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import {
  CalendarIcon,
  CurrencyIcon,
  HashIcon,
  PercentIcon,
  TagIcon,
} from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  customer_id: z.uuid(),
  currency: z.enum(CurrencyEnum),
  numbering_system_id: z.uuid().nullable(),
  coupon_id: z.uuid().nullable(),
  tax_rate_id: z.uuid().nullable(),
  net_payment_term: z.number().int(),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

export function InvoiceCreateDialog({
  defaultCustomer,
}: {
  defaultCustomer?: Customer;
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { account } = useActiveAccount();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      customer_id: defaultCustomer?.id || "",
      currency:
        defaultCustomer?.default_billing_profile?.currency ||
        account.default_currency,
      numbering_system_id:
        defaultCustomer?.default_billing_profile?.invoice_numbering_system_id ||
        account.invoice_numbering_system_id,
      coupon_id: null,
      tax_rate_id:
        defaultCustomer?.default_billing_profile?.tax_rates?.[0]?.id || null,
      net_payment_term:
        defaultCustomer?.default_billing_profile?.net_payment_term != null
          ? defaultCustomer.default_billing_profile.net_payment_term
          : account.net_payment_term,
    },
  });
  const customerId = form.watch("customer_id");
  const currency = form.watch("currency");
  const numberingSystemId = form.watch("numbering_system_id");
  const couponId = form.watch("coupon_id");
  const taxRateId = form.watch("tax_rate_id");
  const netPaymentTerm = form.watch("net_payment_term");

  const { data: customer } = useCustomersRetrieve(customerId ?? "", {
    query: { enabled: !!customerId },
  });
  const { data: numberingSystem } = useNumberingSystemsRetrieve(
    numberingSystemId ?? "",
    {
      query: {
        enabled: !!numberingSystemId,
        placeholderData: undefined,
      },
    },
  );
  const { data: coupon } = useCouponsRetrieve(couponId ?? "", {
    query: { enabled: !!couponId },
  });
  const { data: taxRate } = useTaxRatesRetrieve(taxRateId ?? "", {
    query: {
      enabled: !!taxRateId,
      placeholderData: undefined,
    },
  });

  const { mutateAsync, isPending } = useCreateInvoice({
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
        toast.success("Invoice created");
        popModal();
        await navigate({ to: "/invoices/$id/edit", params: { id } });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  async function onCustomerChange(customer: Customer | null) {
    if (!customer) return;

    form.setValue("customer_id", customer.id);
    form.setValue(
      "currency",
      customer.default_billing_profile?.currency || account.default_currency,
    );
    form.setValue(
      "numbering_system_id",
      customer.default_billing_profile?.invoice_numbering_system_id ||
        account.invoice_numbering_system_id,
    );
    form.setValue(
      "tax_rate_id",
      customer.default_billing_profile?.tax_rates?.[0]?.id || null,
    );
    form.setValue(
      "net_payment_term",
      customer.default_billing_profile?.net_payment_term != null
        ? customer.default_billing_profile.net_payment_term
        : account.net_payment_term,
    );
  }

  async function onSubmit(values: FormValuesInput) {
    // TODO: allow api to accept a list of tax_rate ids and coupon ids
    await mutateAsync({
      data: {
        customer_id: values.customer_id,
        billing_profile_id: customer?.default_billing_profile?.id,
        business_profile_id: account.default_business_profile?.id,
        currency: values.currency,
        numbering_system_id: values.numbering_system_id,
        net_payment_term: values.net_payment_term,
        ...(values.coupon_id ? { coupons: [values.coupon_id] } : {}),
        ...(values.tax_rate_id ? { tax_rates: [values.tax_rate_id] } : {}),
      },
    });
  }

  return (
    <DialogContent className="top-[20%] min-w-1/2 p-0">
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-4"
        >
          <DialogHeader className="px-3 pt-3">
            <DialogTitle className="text-muted-foreground text-base">
              New invoice
            </DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4 px-3">
            <div className="flex items-center gap-1">
              <div className="font-medium">To:</div>
              <CustomerCombobox
                align="start"
                selected={customer}
                onSelect={onCustomerChange}
              >
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-base"
                >
                  {customer ? (
                    <div>
                      <span>{customer.name} </span>
                      {customer.default_billing_profile?.email && (
                        <span className="text-muted-foreground text-sm">
                          ({customer.default_billing_profile.email})
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-muted-foreground">
                      Select customer
                    </span>
                  )}
                </Button>
              </CustomerCombobox>
            </div>

            <div className="flex gap-1">
              <CurrencyCombobox
                align="start"
                selected={currency}
                onSelect={async (value) => {
                  if (!value) return;
                  form.setValue("currency", value as CurrencyEnum);
                }}
              >
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs"
                >
                  <CurrencyIcon className="size-3" />
                  {currency}
                </Button>
              </CurrencyCombobox>
              <NumberingSystemCombobox
                align="start"
                appliesTo={NumberingSystemsListAppliesTo.invoice}
                selected={numberingSystem}
                status={NumberingSystemsListStatus.active}
                onSelect={async (value) => {
                  form.setValue("numbering_system_id", value?.id || null);
                }}
              >
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className={cn(
                    "h-7 text-xs",
                    !numberingSystem && "text-muted-foreground",
                  )}
                >
                  <HashIcon className="size-3" />
                  {numberingSystem ? numberingSystem.description : "Numbering"}
                </Button>
              </NumberingSystemCombobox>
              <CouponCombobox
                align="start"
                currency={currency}
                selected={coupon}
                status={CouponsListStatus.active}
                onSelect={async (value) => {
                  form.setValue("coupon_id", value?.id || null);
                }}
              >
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className={cn(
                    "h-7 text-xs",
                    !coupon && "text-muted-foreground",
                  )}
                >
                  <TagIcon className="size-3" />
                  {coupon ? coupon.name : "Discount"}
                </Button>
              </CouponCombobox>
              <TaxRateCombobox
                align="start"
                selected={taxRate}
                status={TaxRatesListStatus.active}
                onSelect={async (value) => {
                  form.setValue("tax_rate_id", value?.id || null);
                }}
              >
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className={cn(
                    "h-7 text-xs",
                    !taxRate && "text-muted-foreground",
                  )}
                >
                  <PercentIcon className="size-3" />
                  {taxRate ? taxRate.name : "Tax"}
                </Button>
              </TaxRateCombobox>

              <Select
                value={netPaymentTerm.toString()}
                onValueChange={(value) => {
                  form.setValue("net_payment_term", Number(value));
                }}
              >
                <SelectTrigger
                  size="sm"
                  className="gap-1.5 px-2.5 py-0 text-xs font-medium data-[size=sm]:h-7"
                  showIcon={false}
                >
                  <CalendarIcon className="size-3" />
                  {formatDueDate(netPaymentTerm)}
                </SelectTrigger>
                <SelectContent className="min-w-52">
                  {[0, 1, 7, 14, 30, 60, 90].map((value) => (
                    <SelectItem key={value} value={value.toString()}>
                      {formatNetPaymentTerm(value)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter className="border-t p-3">
            <DialogClose asChild>
              <Button
                variant="ghost"
                size="sm"
                type="button"
                disabled={isPending}
              >
                Cancel
              </Button>
            </DialogClose>
            <Button type="submit" size="sm" disabled={isPending || !customer}>
              {isPending && <Spinner />}
              Create invoice
            </Button>
          </DialogFooter>
        </form>
      </Form>
    </DialogContent>
  );
}
