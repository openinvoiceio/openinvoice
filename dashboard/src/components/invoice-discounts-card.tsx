import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
  useApplyInvoiceDiscount,
  useDeleteInvoiceDiscount,
} from "@/api/endpoints/invoices/invoices";
import { type Invoice } from "@/api/models";
import { CouponCombobox } from "@/components/coupon-combobox.tsx";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty.tsx";
import {
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardFooter,
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Spinner } from "@/components/ui/spinner.tsx";
import { Tooltip } from "@/components/ui/tooltip";
import { TooltipContent, TooltipTrigger } from "@/components/ui/tooltip.tsx";
import { MAX_DISCOUNTS } from "@/config/invoices";
import { getErrorSummary } from "@/lib/api/errors";
import { formatAmount, formatPercentage } from "@/lib/formatters.ts";
import { useQueryClient } from "@tanstack/react-query";
import { PlusIcon, XIcon } from "lucide-react";
import { toast } from "sonner";

export function InvoiceDiscountsCard({ invoice }: { invoice: Invoice }) {
  const queryClient = useQueryClient();
  const limitReached = invoice.discounts.length >= MAX_DISCOUNTS;

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

  const applyInvoiceDiscount = useApplyInvoiceDiscount({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });
  const deleteInvoiceDiscount = useDeleteInvoiceDiscount({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return (
    <FormCard data-testid="invoice-discounts-card">
      <FormCardHeader>
        <FormCardTitle>Discounts</FormCardTitle>
        <FormCardDescription>
          Manage the discounts applied to this invoice.
        </FormCardDescription>
      </FormCardHeader>
      <FormCardContent className="gap-2">
        {invoice.discounts.map((discount) => (
          <div key={discount.id} className="flex gap-2 text-sm">
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
              <span>-{formatAmount(discount.amount, invoice.currency)}</span>
            </span>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="text-muted-foreground size-8"
              aria-label={`Remove discount ${discount.coupon.name}`}
              onClick={() =>
                deleteInvoiceDiscount.mutateAsync({
                  invoiceId: invoice.id,
                  id: discount.id,
                })
              }
            >
              <XIcon />
            </Button>
          </div>
        ))}
        {invoice.discounts.length === 0 && (
          <Empty className="border border-dashed">
            <EmptyHeader>
              <EmptyTitle>No discounts added yet</EmptyTitle>
              <EmptyDescription>
                Add discounts to this invoice to provide special offers or
                promotions to your customer.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}
      </FormCardContent>
      <FormCardFooter>
        <Tooltip>
          <TooltipTrigger asChild>
            <span tabIndex={limitReached ? 0 : undefined}>
              <CouponCombobox
                align="start"
                currency={invoice.currency}
                onSelect={async (selected) => {
                  if (!selected) return;
                  await applyInvoiceDiscount.mutateAsync({
                    id: invoice.id,
                    data: { coupon_id: selected.id },
                  });
                }}
              >
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={limitReached}
                >
                  {applyInvoiceDiscount.isPending ? (
                    <Spinner variant="outline" />
                  ) : (
                    <PlusIcon className="text-muted-foreground" />
                  )}
                  Add discount
                </Button>
              </CouponCombobox>
            </span>
          </TooltipTrigger>
          {limitReached && (
            <TooltipContent>
              Maximum {MAX_DISCOUNTS} discounts reached
            </TooltipContent>
          )}
        </Tooltip>
      </FormCardFooter>
    </FormCard>
  );
}
