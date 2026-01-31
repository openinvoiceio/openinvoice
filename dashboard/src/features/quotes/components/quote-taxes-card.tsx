import {
  getPreviewQuoteQueryKey,
  getQuotesListQueryKey,
  getQuotesRetrieveQueryKey,
  useAddQuoteTax,
  useRemoveQuoteTax,
} from "@/api/endpoints/quotes/quotes";
import { TaxRatesListStatus, type Quote } from "@/api/models";
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
import { MAX_TAXES } from "@/config/quotes";
import { TaxRateCombobox } from "@/features/tax-rates/components/tax-rate-combobox.tsx";
import { getErrorSummary } from "@/lib/api/errors";
import { formatAmount, formatPercentage } from "@/lib/formatters.ts";
import { useQueryClient } from "@tanstack/react-query";
import { PlusIcon, XIcon } from "lucide-react";
import { toast } from "sonner";

export function QuoteTaxesCard({ quote }: { quote: Quote }) {
  const queryClient = useQueryClient();
  const limitReached = quote.taxes.length >= MAX_TAXES;

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

  const addQuoteTax = useAddQuoteTax({
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
  const removeQuoteTax = useRemoveQuoteTax({
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
        <FormCardTitle>Taxes</FormCardTitle>
        <FormCardDescription>
          Manage the taxes applied to this quote.
        </FormCardDescription>
      </FormCardHeader>
      <FormCardContent className="gap-2">
        {quote.taxes.map((tax) => (
          <div key={tax.id} className="flex gap-2 text-sm">
            <span className="flex flex-grow-1 items-center justify-between">
              <div className="flex gap-2">
                <span>{tax.name}</span>
                <span className="text-muted-foreground">
                  {formatPercentage(tax.rate)}
                </span>
              </div>
              <span>{formatAmount(tax.amount, quote.currency)}</span>
            </span>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="text-muted-foreground size-8"
              onClick={() =>
                removeQuoteTax.mutateAsync({
                  quoteId: quote.id,
                  quoteTaxId: tax.id,
                })
              }
            >
              <XIcon />
            </Button>
          </div>
        ))}
        {quote.taxes.length === 0 && (
          <Empty className="border border-dashed">
            <EmptyHeader>
              <EmptyTitle>No taxes added yet</EmptyTitle>
              <EmptyDescription>
                Add taxes to this quote to ensure compliance with tax
                regulations.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}
      </FormCardContent>
      <FormCardFooter>
        <Tooltip>
          <TooltipTrigger asChild>
            <span tabIndex={limitReached ? 0 : undefined}>
              <TaxRateCombobox
                align="start"
                status={TaxRatesListStatus.active}
                onSelect={async (selected) => {
                  if (!selected) return;
                  await addQuoteTax.mutateAsync({
                    quoteId: quote.id,
                    data: { tax_rate_id: selected.id },
                  });
                }}
              >
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={limitReached}
                >
                  {addQuoteTax.isPending ? (
                    <Spinner variant="outline" />
                  ) : (
                    <PlusIcon className="text-muted-foreground" />
                  )}
                  Add tax
                </Button>
              </TaxRateCombobox>
            </span>
          </TooltipTrigger>
          {limitReached && (
            <TooltipContent>Maximum {MAX_TAXES} taxes reached</TooltipContent>
          )}
        </Tooltip>
      </FormCardFooter>
    </FormCard>
  );
}
