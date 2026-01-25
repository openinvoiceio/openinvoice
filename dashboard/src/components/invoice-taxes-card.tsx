import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
  useUpdateInvoice,
} from "@/api/endpoints/invoices/invoices";
import { TaxRatesListStatus, type Invoice } from "@/api/models";
import { TaxRateCombobox } from "@/components/tax-rate-combobox.tsx";
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
import { MAX_TAXES } from "@/config/invoices";
import { getErrorSummary } from "@/lib/api/errors";
import { formatPercentage } from "@/lib/formatters.ts";
import { useQueryClient } from "@tanstack/react-query";
import { PlusIcon, XIcon } from "lucide-react";
import { toast } from "sonner";

export function InvoiceTaxesCard({ invoice }: { invoice: Invoice }) {
  const queryClient = useQueryClient();
  const limitReached = invoice.taxes.length >= MAX_TAXES;

  const updateInvoice = useUpdateInvoice({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getInvoicesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getInvoicesRetrieveQueryKey(invoice.id),
        });
        await queryClient.invalidateQueries({
          queryKey: getPreviewInvoiceQueryKey(invoice.id),
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return (
    <FormCard data-testid="invoice-taxes-card">
      <FormCardHeader>
        <FormCardTitle>Taxes</FormCardTitle>
        <FormCardDescription>
          Manage the taxes applied to this invoice.
        </FormCardDescription>
      </FormCardHeader>
      <FormCardContent className="gap-2">
        {invoice.tax_rates.map((tax_rate) => (
          <div key={tax_rate.id} className="flex gap-2 text-sm">
            <div className="flex flex-grow-1 items-center gap-2">
              <span>{tax_rate.name}</span>
              <span className="text-muted-foreground">
                {formatPercentage(tax_rate.percentage)}
              </span>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="text-muted-foreground size-8"
              aria-label={`Remove tax ${tax_rate.name}`}
              onClick={() =>
                updateInvoice.mutate({
                  id: invoice.id,
                  data: {
                    tax_rates: invoice.tax_rates
                      .filter((tr) => tr.id !== tax_rate.id)
                      .map((tr) => tr.id),
                  },
                })
              }
            >
              <XIcon />
            </Button>
          </div>
        ))}
        {invoice.tax_rates.length === 0 && (
          <Empty className="border border-dashed">
            <EmptyHeader>
              <EmptyTitle>No taxes added yet</EmptyTitle>
              <EmptyDescription>
                Add taxes to this invoice to ensure compliance with tax
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
                  await updateInvoice.mutateAsync({
                    id: invoice.id,
                    data: {
                      tax_rates: [
                        ...invoice.tax_rates.map((tr) => tr.id),
                        selected.id,
                      ],
                    },
                  });
                }}
              >
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={limitReached}
                >
                  {updateInvoice.isPending ? (
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
