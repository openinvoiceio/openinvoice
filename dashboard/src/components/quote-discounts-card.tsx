import {
  getPreviewQuoteQueryKey,
  getQuotesListQueryKey,
  getQuotesRetrieveQueryKey,
  useAddQuoteDiscount,
  useRemoveQuoteDiscount,
} from "@/api/endpoints/quotes/quotes";
import { type Quote } from "@/api/models";
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
import { MAX_DISCOUNTS } from "@/config/quotes";
import { getErrorSummary } from "@/lib/api/errors";
import { formatAmount, formatPercentage } from "@/lib/formatters.ts";
import { useQueryClient } from "@tanstack/react-query";
import { PlusIcon, XIcon } from "lucide-react";
import { toast } from "sonner";

export function QuoteDiscountsCard({ quote }: { quote: Quote }) {
  const queryClient = useQueryClient();
  const limitReached = quote.discounts.length >= MAX_DISCOUNTS;

  async function invalidate() {
    await queryClient.invalidateQueries({
      queryKey: getQuotesListQueryKey(),
    });
    await queryClient.invalidateQueries({
      queryKey: getQuotesRetrieveQueryKey(quote.id),
    });
    await queryClient.invalidateQueries({
      queryKey: getPreviewQuoteQueryKey(quote.id),
    });
  }

  const addQuoteDiscount = useAddQuoteDiscount({
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
  const removeQuoteDiscount = useRemoveQuoteDiscount({
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
    <FormCard>
      <FormCardHeader>
        <FormCardTitle>Discounts</FormCardTitle>
        <FormCardDescription>
          Manage the discounts applied to this quote.
        </FormCardDescription>
      </FormCardHeader>
      <FormCardContent className="gap-2">
        {quote.discounts.map((discount) => (
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
              <span>-{formatAmount(discount.amount, quote.currency)}</span>
            </span>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="text-muted-foreground size-8"
              onClick={() =>
                removeQuoteDiscount.mutateAsync({
                  quoteId: quote.id,
                  quoteDiscountId: discount.id,
                })
              }
            >
              <XIcon />
            </Button>
          </div>
        ))}
        {quote.discounts.length === 0 && (
          <Empty className="border border-dashed">
            <EmptyHeader>
              <EmptyTitle>No discounts added yet</EmptyTitle>
              <EmptyDescription>
                Add discounts to this quote to provide special offers or
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
                currency={quote.currency}
                onSelect={async (selected) => {
                  if (!selected) return;
                  await addQuoteDiscount.mutateAsync({
                    quoteId: quote.id,
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
                  {addQuoteDiscount.isPending ? (
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
