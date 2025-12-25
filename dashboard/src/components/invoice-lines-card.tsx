import {
  useApplyInvoiceLineDiscount,
  useApplyInvoiceLineTax,
  useCreateInvoiceLine,
  useDeleteInvoiceLine,
  useDeleteInvoiceLineDiscount,
  useDeleteInvoiceLineTax,
  useUpdateInvoiceLine,
} from "@/api/endpoints/invoice-lines/invoice-lines";
import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
} from "@/api/endpoints/invoices/invoices";
import { usePricesRetrieve } from "@/api/endpoints/prices/prices";
import type { Invoice, InvoiceLine } from "@/api/models";
import { CouponCombobox } from "@/components/coupon-combobox.tsx";
import { PriceCombobox } from "@/components/price-combobox.tsx";
import { TaxRateCombobox } from "@/components/tax-rate-combobox.tsx";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ComboboxButton } from "@/components/ui/combobox-button.tsx";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty.tsx";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardFooter,
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Input, inputClassName } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { MAX_DISCOUNTS, MAX_TAXES } from "@/config/invoices";
import { useDebouncedCallback } from "@/hooks/use-debounced-callback";
import { getErrorSummary } from "@/lib/api/errors";
import { isZeroDecimalCurrency } from "@/lib/currency";
import { formatAmount, formatPercentage } from "@/lib/formatters";
import { formatPrice } from "@/lib/products.ts";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import Decimal from "decimal.js";
import { PlusIcon, XIcon } from "lucide-react";
import { useState } from "react";
import CurrencyInput from "react-currency-input-field";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import z from "zod";

const schema = z.object({
  price_id: z.string().nullable(),
  unit_amount: z.string(),
  description: z.string(),
  quantity: z
    .union([z.string(), z.number()])
    .transform((v) => (typeof v === "string" ? Number(v) : v))
    .pipe(z.number().int().min(0, "Quantity cannot be negative")),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

function InvoiceLineForm({
  line,
  invoice,
}: {
  line: InvoiceLine;
  invoice: Invoice;
}) {
  const queryClient = useQueryClient();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      price_id: line.price_id,
      unit_amount: line.unit_amount,
      description: line.description || "",
      quantity: line.quantity,
    },
  });
  const { data: price } = usePricesRetrieve(line.price_id || "", {
    query: { enabled: !!line.price_id },
  });

  const discountsLimitReached = line.discounts.length >= MAX_DISCOUNTS;
  const taxesLimitReached = line.taxes.length >= MAX_TAXES;

  async function invalidate() {
    await queryClient.invalidateQueries({
      queryKey: getInvoicesListQueryKey(),
    });
    await queryClient.invalidateQueries({
      queryKey: getInvoicesRetrieveQueryKey(invoice.id),
    });
    await queryClient.invalidateQueries({
      queryKey: getPreviewInvoiceQueryKey(invoice.id),
    });
  }

  const updateInvoiceLine = useUpdateInvoiceLine({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });
  const applyInvoiceLineDiscount = useApplyInvoiceLineDiscount({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });
  const deleteInvoiceLineDiscount = useDeleteInvoiceLineDiscount({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });
  const applyInvoiceLineTax = useApplyInvoiceLineTax({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });
  const deleteInvoiceLineTax = useDeleteInvoiceLineTax({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  const isPending =
    updateInvoiceLine.isPending ||
    applyInvoiceLineDiscount.isPending ||
    deleteInvoiceLineDiscount.isPending ||
    applyInvoiceLineTax.isPending ||
    deleteInvoiceLineTax.isPending;

  async function onSubmit(values: FormValuesOutput) {
    if (isPending) return;
    await updateInvoiceLine.mutateAsync({
      id: line.id,
      data: {
        description: values.description,
        quantity: values.quantity,
        price_id: values.price_id || undefined,
        unit_amount: values.price_id ? undefined : values.unit_amount,
      },
    });
  }

  const submit = form.handleSubmit(onSubmit);
  const debouncedSubmit = useDebouncedCallback(() => submit(), 500);

  return (
    <Form {...form}>
      <form className="grid gap-4 py-2">
        <FormCardContent>
          <FormField
            control={form.control}
            name="description"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Description</FormLabel>
                <FormControl>
                  <Input
                    placeholder="Enter line description"
                    {...field}
                    onChange={(e) => {
                      field.onChange(e);
                      debouncedSubmit();
                    }}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </FormCardContent>
        <FormCardContent className="md:grid-cols-2">
          {!!line.price_id ? (
            <FormField
              control={form.control}
              name="price_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Price</FormLabel>
                  <FormControl>
                    <PriceCombobox
                      align="start"
                      selected={price}
                      onSelect={async (selected) => {
                        field.onChange(selected?.id);
                        form.setValue(
                          "description",
                          selected?.product.name || "",
                        );
                        await submit();
                      }}
                      currency={invoice.currency}
                    >
                      <ComboboxButton>
                        {price ? (
                          <>
                            <span>{formatPrice(price)}</span>
                            {price.code && (
                              <span className="text-muted-foreground">
                                {price.code}
                              </span>
                            )}
                          </>
                        ) : (
                          <span className="text-muted-foreground">
                            Select price
                          </span>
                        )}
                      </ComboboxButton>
                    </PriceCombobox>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          ) : (
            <FormField
              control={form.control}
              name="unit_amount"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Price</FormLabel>
                  <FormControl>
                    <CurrencyInput
                      placeholder="Enter price"
                      className={inputClassName}
                      value={field.value}
                      onValueChange={(value) => {
                        field.onChange(value);
                        debouncedSubmit();
                      }}
                      maxLength={8}
                      decimalsLimit={
                        isZeroDecimalCurrency(invoice.currency) ? 0 : 2
                      }
                      allowDecimals={!isZeroDecimalCurrency(invoice.currency)}
                      allowNegativeValue={false}
                      disableAbbreviations={true}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          )}
          <FormField
            control={form.control}
            name="quantity"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Quantity</FormLabel>
                <FormControl>
                  <CurrencyInput
                    placeholder="Enter quantity"
                    className={inputClassName}
                    value={field.value}
                    onValueChange={(value) => {
                      field.onChange(value || "0");
                      debouncedSubmit();
                    }}
                    maxLength={8}
                    allowDecimals={false}
                    allowNegativeValue={false}
                    disableAbbreviations={true}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </FormCardContent>
        {line.taxes.length > 0 && (
          <FormCardContent className="gap-2">
            <FormLabel>Line taxes</FormLabel>
            <div>
              {line.taxes.map((tax) => (
                <div key={tax.id} className="flex gap-2">
                  <span className="flex flex-grow-1 items-center justify-between">
                    <div className="flex gap-2">
                      <span>{tax.name}</span>
                      <span className="text-muted-foreground">
                        {formatPercentage(tax.rate)}
                      </span>
                    </div>
                    <span>{formatAmount(tax.amount, invoice.currency)}</span>
                  </span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground size-8"
                    onClick={() =>
                      deleteInvoiceLineTax.mutateAsync({
                        id: tax.id,
                        invoiceLineId: line.id,
                      })
                    }
                  >
                    <XIcon />
                  </Button>
                </div>
              ))}
            </div>
          </FormCardContent>
        )}
        {line.discounts.length > 0 && (
          <FormCardContent className="gap-2">
            <FormLabel>Line discounts</FormLabel>
            <div className="grid">
              {line.discounts.map((discount) => (
                <div key={discount.id} className="flex w-full gap-2">
                  <span className="flex flex-grow-1 items-center justify-between">
                    <div className="flex gap-2">
                      <span>{discount.coupon.name}</span>
                      <span className="text-muted-foreground">
                        {discount.coupon.amount
                          ? formatAmount(
                              discount.coupon.amount,
                              discount.coupon.currency,
                            )
                          : formatPercentage(
                              discount.coupon.percentage as string,
                            )}{" "}
                        off
                      </span>
                    </div>
                    <span>
                      -{formatAmount(discount.amount, invoice.currency)}
                    </span>
                  </span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground size-8"
                    onClick={() =>
                      deleteInvoiceLineDiscount.mutateAsync({
                        id: discount.id,
                        invoiceLineId: line.id,
                      })
                    }
                  >
                    <XIcon />
                  </Button>
                </div>
              ))}
            </div>
          </FormCardContent>
        )}
        <FormCardContent className="flex gap-1">
          <Tooltip>
            <TooltipTrigger asChild>
              <span tabIndex={discountsLimitReached ? 0 : undefined}>
                <CouponCombobox
                  align="start"
                  currency={invoice.currency}
                  onSelect={async (selected) => {
                    if (!selected) return;
                    await applyInvoiceLineDiscount.mutateAsync({
                      id: line.id,
                      data: { coupon_id: selected.id },
                    });
                  }}
                >
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    disabled={discountsLimitReached}
                  >
                    {applyInvoiceLineDiscount.isPending ? (
                      <Spinner variant="outline" />
                    ) : (
                      <PlusIcon className="text-muted-foreground" />
                    )}
                    Add discount
                  </Button>
                </CouponCombobox>
              </span>
            </TooltipTrigger>
            {discountsLimitReached && (
              <TooltipContent>
                Maximum {MAX_DISCOUNTS} discounts reached
              </TooltipContent>
            )}
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <span tabIndex={taxesLimitReached ? 0 : undefined}>
                <TaxRateCombobox
                  align="start"
                  onSelect={async (selected) => {
                    if (!selected) return;
                    await applyInvoiceLineTax.mutateAsync({
                      id: line.id,
                      data: { tax_rate_id: selected.id },
                    });
                  }}
                >
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    disabled={taxesLimitReached}
                  >
                    {applyInvoiceLineTax.isPending ? (
                      <Spinner variant="outline" />
                    ) : (
                      <PlusIcon className="text-muted-foreground" />
                    )}
                    Add tax
                  </Button>
                </TaxRateCombobox>
              </span>
            </TooltipTrigger>
            {taxesLimitReached && (
              <TooltipContent>Maximum {MAX_TAXES} taxes reached</TooltipContent>
            )}
          </Tooltip>
        </FormCardContent>
      </form>
    </Form>
  );
}

export function InvoiceLinesCard({ invoice }: { invoice: Invoice }) {
  const queryClient = useQueryClient();
  const [openItem, setOpenItem] = useState<string>();

  async function invalidate() {
    await queryClient.invalidateQueries({
      queryKey: getInvoicesListQueryKey(),
    });
    await queryClient.invalidateQueries({
      queryKey: getInvoicesRetrieveQueryKey(invoice.id),
    });
    await queryClient.invalidateQueries({
      queryKey: getPreviewInvoiceQueryKey(invoice.id),
    });
  }

  const createInvoiceLine = useCreateInvoiceLine({
    mutation: {
      onSuccess: async (line) => {
        await invalidate();
        setOpenItem(line.id);
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  const deleteInvoiceLine = useDeleteInvoiceLine({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  return (
    <FormCard className="gap-0">
      <FormCardHeader className="pb-4">
        <FormCardTitle>Lines</FormCardTitle>
        <FormCardDescription>Add items to your invoice</FormCardDescription>
      </FormCardHeader>
      <Accordion
        type="single"
        value={openItem}
        className="[&>:first-child]:border-t"
        onValueChange={setOpenItem}
        collapsible
      >
        {invoice.lines.map((line) => (
          <AccordionItem
            key={line.id}
            value={line.id}
            className="data-[state=open]:bg-accent/35 relative border-x-0 transition outline-none"
          >
            <div className="flex w-full items-center justify-between">
              <div className="w-full [&_h3]:w-full">
                <AccordionTrigger className="items-center justify-start px-4 py-3 leading-6 font-normal hover:no-underline focus-visible:ring-0 [&>svg]:-order-1">
                  {line.description} × {line.quantity}
                </AccordionTrigger>
              </div>
              <div className="flex items-center gap-2">
                {line.discounts.length > 0 && (
                  <Badge variant="secondary" className="text-muted-foreground">
                    {formatAmount(
                      line.discounts
                        .reduce(
                          (acc, discount) =>
                            acc.plus(new Decimal(discount.amount)),
                          new Decimal(0),
                        )
                        .toString(),
                      invoice.currency,
                    )}{" "}
                    off
                  </Badge>
                )}
                {line.taxes.length > 0 && (
                  <Badge variant="secondary" className="text-muted-foreground">
                    {formatPercentage(
                      line.taxes
                        .reduce(
                          (acc, tax) => acc.plus(new Decimal(tax.rate)),
                          new Decimal(0),
                        )
                        .toString(),
                    )}{" "}
                    tax
                  </Badge>
                )}
                {!line.price_id && <Badge variant="secondary">One-time</Badge>}
                <span className="text-sm">
                  {formatAmount(line.amount, invoice.currency)}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground mr-4 size-8"
                  onClick={async (e) => {
                    e.preventDefault();
                    await deleteInvoiceLine.mutateAsync({ id: line.id });
                  }}
                >
                  <XIcon />
                </Button>
              </div>
            </div>
            <AccordionContent>
              <InvoiceLineForm line={line} invoice={invoice} />
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
      {invoice.lines.length === 0 && (
        <Empty className="m-2 border border-dashed">
          <EmptyHeader>
            <EmptyTitle>No lines added yet</EmptyTitle>
            <EmptyDescription>
              Add lines by selecting a price or adding a one-time price.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      )}
      <FormCardFooter>
        <PriceCombobox
          align="start"
          onSelect={async (selected) => {
            if (!selected) return;
            await createInvoiceLine.mutateAsync({
              data: {
                invoice_id: invoice.id,
                price_id: selected.id,
                description: selected.product.name,
                quantity: 1,
              },
            });
          }}
          currency={invoice.currency}
          actions={[
            {
              name: "Add one-time price",
              onClick: async (value) => {
                await createInvoiceLine.mutateAsync({
                  data: {
                    invoice_id: invoice.id,
                    unit_amount: "0",
                    description: value,
                    quantity: 1,
                  },
                });
              },
            },
          ]}
        >
          <Button type="button" variant="outline" size="sm">
            {createInvoiceLine.isPending ? (
              <Spinner variant="outline" />
            ) : (
              <PlusIcon className="text-muted-foreground" />
            )}
            Add line
          </Button>
        </PriceCombobox>
      </FormCardFooter>
    </FormCard>
  );
}
