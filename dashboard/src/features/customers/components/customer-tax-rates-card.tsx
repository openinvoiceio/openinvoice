import {
  getCustomersRetrieveQueryKey,
  useUpdateCustomer,
} from "@/api/endpoints/customers/customers";
import { TaxRatesListStatus, type Customer } from "@/api/models";
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
import { MAX_CUSTOMER_TAX_RATES } from "@/config/customers";
import { TaxRateCombobox } from "@/features/tax-rates/components/tax-rate-combobox.tsx";
import { getErrorSummary } from "@/lib/api/errors";
import { formatCountry, formatPercentage } from "@/lib/formatters";
import { useQueryClient } from "@tanstack/react-query";
import { XIcon } from "lucide-react";
import React from "react";
import { toast } from "sonner";

export function CustomerTaxRatesCard({
  customer,
  ...props
}: React.ComponentProps<typeof FormCard> & { customer: Customer }) {
  const queryClient = useQueryClient();
  const taxRates = customer.tax_rates ?? [];
  const limitReached = taxRates.length >= MAX_CUSTOMER_TAX_RATES;

  const updateCustomer = useUpdateCustomer({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getCustomersRetrieveQueryKey(customer.id),
        });
        toast.success("Customer updated");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });
  const isPending = updateCustomer.isPending;

  return (
    <FormCard {...props}>
      <FormCardHeader>
        <FormCardTitle>Tax rates</FormCardTitle>
        <FormCardDescription>
          Manage default tax rates applied to this customer.
        </FormCardDescription>
      </FormCardHeader>
      <FormCardContent>
        {taxRates.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Percentage</TableHead>
                <TableHead>Country</TableHead>
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
                  <TableCell>
                    {taxRate.country ? formatCountry(taxRate.country) : "-"}
                  </TableCell>
                  <TableCell className="flex justify-end">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() =>
                        updateCustomer.mutateAsync({
                          id: customer.id,
                          data: {
                            tax_rates: taxRates
                              .filter((rate) => rate.id !== taxRate.id)
                              .map((rate) => rate.id),
                          },
                        })
                      }
                      disabled={isPending}
                    >
                      <XIcon />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <Empty className="border border-dashed">
            <EmptyHeader>
              <EmptyTitle>No tax rates assigned</EmptyTitle>
              <EmptyDescription>
                Assigned tax rates will be applied to invoices by default
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}
      </FormCardContent>
      <FormCardFooter>
        <Tooltip>
          <TooltipTrigger asChild>
            <span>
              <TaxRateCombobox
                align="end"
                status={TaxRatesListStatus.active}
                onSelect={async (taxRate) => {
                  if (!taxRate) return;
                  await updateCustomer.mutateAsync({
                    id: customer.id,
                    data: {
                      tax_rates: [
                        ...taxRates.map((rate) => rate.id),
                        taxRate.id,
                      ],
                    },
                  });
                }}
              >
                <Button type="button" disabled={isPending || limitReached}>
                  Assign
                </Button>
              </TaxRateCombobox>
            </span>
          </TooltipTrigger>
          {limitReached && (
            <TooltipContent>
              You can assign at most {MAX_CUSTOMER_TAX_RATES} tax rates.
            </TooltipContent>
          )}
        </Tooltip>
      </FormCardFooter>
    </FormCard>
  );
}
