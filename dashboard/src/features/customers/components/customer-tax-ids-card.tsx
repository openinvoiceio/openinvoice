import {
  getCustomersListQueryKey,
  getCustomersRetrieveQueryKey,
  useDeleteCustomerTaxId,
} from "@/api/endpoints/customers/customers";
import type { Customer } from "@/api/models";
import { pushModal } from "@/components/push-modals";
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
import { MAX_TAX_IDS } from "@/config/tax-ids";
import { getErrorSummary } from "@/lib/api/errors";
import { formatCountry, formatTaxIdType } from "@/lib/formatters";
import { useQueryClient } from "@tanstack/react-query";
import { XIcon } from "lucide-react";
import { toast } from "sonner";

export function CustomerTaxIdsCard({ customer }: { customer: Customer }) {
  const queryClient = useQueryClient();
  const limitReached = customer.tax_ids.length >= MAX_TAX_IDS;

  const { isPending, mutateAsync } = useDeleteCustomerTaxId({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getCustomersListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getCustomersRetrieveQueryKey(customer.id),
        });
        toast.success("Tax ID deleted");
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
        <FormCardTitle>Tax IDs</FormCardTitle>
        <FormCardDescription>
          Manage tax ids associated with this customer.
        </FormCardDescription>
      </FormCardHeader>
      <FormCardContent>
        {customer.tax_ids.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Number</TableHead>
                <TableHead>Country</TableHead>
                <TableHead>
                  <span className="sr-only">Remove</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {customer.tax_ids.map((taxId) => (
                <TableRow key={taxId.id}>
                  <TableCell className="font-medium">
                    {formatTaxIdType(taxId.type)}
                  </TableCell>
                  <TableCell>{taxId.number}</TableCell>
                  <TableCell>
                    {taxId.country ? formatCountry(taxId.country) : "-"}
                  </TableCell>
                  <TableCell className="flex justify-end">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() =>
                        mutateAsync({ id: taxId.id, customerId: customer.id })
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
              <EmptyTitle>No tax ids configured</EmptyTitle>
              <EmptyDescription>
                Configured tax ids will be displayed on invoices
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}
      </FormCardContent>
      <FormCardFooter>
        <Tooltip>
          <TooltipTrigger asChild>
            <span>
              <Button
                type="button"
                onClick={() =>
                  pushModal("CustomerTaxIdCreateSheet", {
                    customerId: customer.id,
                  })
                }
                disabled={isPending || limitReached}
              >
                Add
              </Button>
            </span>
          </TooltipTrigger>
          {limitReached && (
            <TooltipContent>
              You can add at most {MAX_TAX_IDS} tax IDs.
            </TooltipContent>
          )}
        </Tooltip>
      </FormCardFooter>
    </FormCard>
  );
}
