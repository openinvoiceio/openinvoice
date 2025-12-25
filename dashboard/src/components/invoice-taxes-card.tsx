import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
  useApplyInvoiceTax,
  useDeleteInvoiceTax,
} from "@/api/endpoints/invoices/invoices";
import { type Invoice } from "@/api/models";
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
import { formatAmount, formatPercentage } from "@/lib/formatters.ts";
import { useQueryClient } from "@tanstack/react-query";
import { PlusIcon, XIcon } from "lucide-react";
import { toast } from "sonner";

export function InvoiceTaxesCard({ invoice }: { invoice: Invoice }) {
  const queryClient = useQueryClient();
  const limitReached = invoice.taxes.length >= MAX_TAXES;

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

  const applyInvoiceTax = useApplyInvoiceTax({
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
  const deleteInvoiceTax = useDeleteInvoiceTax({
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
          Manage the taxes applied to this invoice.
        </FormCardDescription>
      </FormCardHeader>
      <FormCardContent className="gap-2">
        {invoice.taxes.map((tax) => (
          <div key={tax.id} className="flex gap-2 text-sm">
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
                deleteInvoiceTax.mutateAsync({
                  invoiceId: invoice.id,
                  id: tax.id,
                })
              }
            >
              <XIcon />
            </Button>
          </div>
        ))}
        {invoice.taxes.length === 0 && (
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
                onSelect={async (selected) => {
                  if (!selected) return;
                  await applyInvoiceTax.mutateAsync({
                    id: invoice.id,
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
                  {applyInvoiceTax.isPending ? (
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
