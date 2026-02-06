import { getAccountsRetrieveQueryKey } from "@/api/endpoints/accounts/accounts";
import {
  getBusinessProfilesListQueryKey,
  useDeleteBusinessProfileTaxId,
} from "@/api/endpoints/business-profiles/business-profiles";
import type { Account } from "@/api/models";
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

export function AccountTaxIdsCard({ account }: { account: Account }) {
  const queryClient = useQueryClient();
  const defaultBusinessProfile = account.default_business_profile;
  const taxIds = defaultBusinessProfile?.tax_ids ?? [];
  const limitReached = taxIds.length >= MAX_TAX_IDS;

  const { isPending, mutateAsync } = useDeleteBusinessProfileTaxId({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getBusinessProfilesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getAccountsRetrieveQueryKey(account.id),
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
          Manage the tax ids associated with this account.
        </FormCardDescription>
      </FormCardHeader>
      <FormCardContent>
        {!defaultBusinessProfile && (
          <Empty className="border border-dashed">
            <EmptyHeader>
              <EmptyTitle>No default business profile</EmptyTitle>
              <EmptyDescription>
                Set a default business profile to manage tax IDs.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}
        {defaultBusinessProfile && taxIds.length === 0 ? (
          <Empty className="border border-dashed">
            <EmptyHeader>
              <EmptyTitle>No tax ids</EmptyTitle>
              <EmptyDescription>
                You have not added any tax ids to this account yet.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        ) : defaultBusinessProfile ? (
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
                        defaultBusinessProfile &&
                        mutateAsync({
                          id: taxId.id,
                          businessProfileId: defaultBusinessProfile.id,
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
        ) : null}
      </FormCardContent>
      <FormCardFooter>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              onClick={() =>
                defaultBusinessProfile &&
                pushModal("AccountTaxIdCreateSheet", {
                  accountId: account.id,
                  businessProfileId: defaultBusinessProfile.id,
                })
              }
              disabled={isPending || limitReached || !defaultBusinessProfile}
            >
              Add
            </Button>
          </TooltipTrigger>
          {limitReached && (
            <TooltipContent>
              You can add at most {MAX_TAX_IDS} tax ids.
            </TooltipContent>
          )}
        </Tooltip>
      </FormCardFooter>
    </FormCard>
  );
}
