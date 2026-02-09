import { useAccountsAddressesList } from "@/api/endpoints/accounts/accounts";
import type { Account } from "@/api/models";
import { pushModal } from "@/components/push-modals";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
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
import { AccountAddressDropdown } from "@/features/settings/components/account-address-dropdown";
import { formatCountry } from "@/lib/formatters";
import { MoreHorizontalIcon } from "lucide-react";

export function AccountAddressesCard({ account }: { account: Account }) {
  const { data } = useAccountsAddressesList(account.id, { page_size: 50 });
  const addresses = data?.results ?? [];

  return (
    <FormCard>
      <FormCardHeader>
        <FormCardTitle>Addresses</FormCardTitle>
        <FormCardDescription>
          Manage the saved addresses for this account.
        </FormCardDescription>
      </FormCardHeader>
      <FormCardContent>
        {addresses.length > 0 ? (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Line 1</TableHead>
                  <TableHead>Locality</TableHead>
                  <TableHead>Country</TableHead>
                  <TableHead>
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {addresses.map((address) => (
                  <TableRow key={address.id}>
                    <TableCell className="font-medium">
                      {address.line1 || "-"}
                    </TableCell>
                    <TableCell>{address.locality || "-"}</TableCell>
                    <TableCell>
                      {address.country ? formatCountry(address.country) : "-"}
                    </TableCell>
                    <TableCell className="text-right">
                      <AccountAddressDropdown
                        address={address}
                        accountId={account.id}
                      >
                        <Button
                          size="icon"
                          variant="ghost"
                          className="data-[state=open]:bg-accent size-7"
                        >
                          <MoreHorizontalIcon />
                        </Button>
                      </AccountAddressDropdown>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          <Empty className="border border-dashed">
            <EmptyHeader>
              <EmptyTitle>No addresses</EmptyTitle>
              <EmptyDescription>
                Save addresses to reuse them across business profiles.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}
      </FormCardContent>
      <FormCardFooter>
        <Button
          type="button"
          onClick={() =>
            pushModal("AccountAddressCreateSheet", { accountId: account.id })
          }
        >
          Add
        </Button>
      </FormCardFooter>
    </FormCard>
  );
}
