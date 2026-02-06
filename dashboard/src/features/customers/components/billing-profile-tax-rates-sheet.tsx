import {
  getBillingProfilesListQueryKey,
  useBillingProfilesRetrieve,
  useUpdateBillingProfile,
} from "@/api/endpoints/billing-profiles/billing-profiles";
import { popModal } from "@/components/push-modals";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty.tsx";
import {
  FormSheetContent,
  FormSheetDescription,
  FormSheetFooter,
  FormSheetHeader,
  FormSheetTitle,
} from "@/components/ui/form-sheet";
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { MAX_CUSTOMER_TAX_RATES } from "@/config/customers.ts";
import { TaxRateCombobox } from "@/features/tax-rates/components/tax-rate-combobox";
import { getErrorSummary } from "@/lib/api/errors";
import { formatPercentage } from "@/lib/formatters";
import { useQueryClient } from "@tanstack/react-query";
import { XIcon } from "lucide-react";
import { toast } from "sonner";

export function BillingProfileTaxRatesSheet({
  billingProfileId,
}: {
  billingProfileId: string;
}) {
  const queryClient = useQueryClient();
  const { data: profile } = useBillingProfilesRetrieve(billingProfileId);
  const taxRates = profile?.tax_rates ?? [];
  const limitReached = taxRates.length >= MAX_CUSTOMER_TAX_RATES;

  const updateBillingProfile = useUpdateBillingProfile({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getBillingProfilesListQueryKey(),
        });
        toast.success("Billing profile updated");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  if (!profile) {
    return (
      <FormSheetContent>
        <FormSheetHeader>
          <FormSheetTitle>Tax rates</FormSheetTitle>
          <FormSheetDescription>
            Loading billing profile details.
          </FormSheetDescription>
        </FormSheetHeader>
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      </FormSheetContent>
    );
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Tax rates</FormSheetTitle>
        <FormSheetDescription>
          Manage tax rates for {profile.legal_name || "this billing profile"}.
        </FormSheetDescription>
      </FormSheetHeader>
      {taxRates.length > 0 ? (
        <div className="overflow-hidden rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Percentage</TableHead>
                <TableHead>
                  <span className="sr-only">Remove</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {taxRates.map((taxRate) => (
                <TableRow key={taxRate.id}>
                  <TableCell className="font-medium">{taxRate.name}</TableCell>
                  <TableCell>{formatPercentage(taxRate.percentage)}</TableCell>
                  <TableCell className="flex justify-end">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() =>
                        updateBillingProfile.mutateAsync({
                          id: profile.id,
                          data: {
                            tax_rates: taxRates
                              .filter((rate) => rate.id !== taxRate.id)
                              .map((rate) => rate.id),
                          },
                        })
                      }
                      disabled={updateBillingProfile.isPending}
                    >
                      <XIcon />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <Empty className="border border-dashed">
          <EmptyHeader>
            <EmptyTitle>No tax rates assigned</EmptyTitle>
            <EmptyDescription>
              Assign tax rates to apply them by default to invoices.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      )}
      <FormSheetFooter className="justify-between">
        <Button type="button" variant="ghost" onClick={() => popModal()}>
          Close
        </Button>
        <Tooltip>
          <TooltipTrigger asChild>
            <span>
              <TaxRateCombobox
                align="end"
                onSelect={async (taxRate) => {
                  if (!taxRate) return;
                  await updateBillingProfile.mutateAsync({
                    id: profile.id,
                    data: {
                      tax_rates: [
                        ...taxRates.map((rate) => rate.id),
                        taxRate.id,
                      ],
                    },
                  });
                }}
              >
                <Button
                  type="button"
                  disabled={updateBillingProfile.isPending || limitReached}
                >
                  Assign
                </Button>
              </TaxRateCombobox>
            </span>
          </TooltipTrigger>
          {limitReached && (
            <TooltipContent>
              You can add at most {MAX_CUSTOMER_TAX_RATES} tax rates.
            </TooltipContent>
          )}
        </Tooltip>
      </FormSheetFooter>
    </FormSheetContent>
  );
}
