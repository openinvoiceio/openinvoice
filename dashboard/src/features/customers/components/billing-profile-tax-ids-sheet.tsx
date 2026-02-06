import {
  getBillingProfilesListQueryKey,
  useBillingProfilesRetrieve,
  useDeleteBillingProfileTaxId,
} from "@/api/endpoints/billing-profiles/billing-profiles";
import { popModal, pushModal } from "@/components/push-modals";
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
import { MAX_TAX_IDS } from "@/config/tax-ids";
import { getErrorSummary } from "@/lib/api/errors";
import { formatCountry, formatTaxIdType } from "@/lib/formatters";
import { useQueryClient } from "@tanstack/react-query";
import { XIcon } from "lucide-react";
import { toast } from "sonner";

export function BillingProfileTaxIdsSheet({
  customerId,
  billingProfileId,
}: {
  customerId: string;
  billingProfileId: string;
}) {
  const queryClient = useQueryClient();
  const { data: profile } = useBillingProfilesRetrieve(billingProfileId);
  const taxIds = profile?.tax_ids ?? [];
  const limitReached = taxIds.length >= MAX_TAX_IDS;

  const { isPending, mutateAsync } = useDeleteBillingProfileTaxId({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getBillingProfilesListQueryKey(),
        });
        toast.success("Tax ID deleted");
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
          <FormSheetTitle>Tax IDs</FormSheetTitle>
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
        <FormSheetTitle>Tax IDs</FormSheetTitle>
        <FormSheetDescription>
          Manage tax IDs for {profile.legal_name || "this billing profile"}.
        </FormSheetDescription>
      </FormSheetHeader>
      {taxIds.length > 0 ? (
        <div className="overflow-hidden rounded-md border">
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
              {taxIds.map((taxId) => (
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
                        mutateAsync({
                          id: taxId.id,
                          billingProfileId: profile.id,
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
        </div>
      ) : (
        <Empty className="border border-dashed">
          <EmptyHeader>
            <EmptyTitle>No tax ids</EmptyTitle>
            <EmptyDescription>
              Add tax ids to appear on invoices and legal documents.
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
              <Button
                type="button"
                onClick={() =>
                  pushModal("BillingProfileTaxIdCreateSheet", {
                    customerId,
                    billingProfileId: profile.id,
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
              You can add at most {MAX_TAX_IDS} tax ids.
            </TooltipContent>
          )}
        </Tooltip>
      </FormSheetFooter>
    </FormSheetContent>
  );
}
