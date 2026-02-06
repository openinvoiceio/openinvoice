import { useBusinessProfilesList } from "@/api/endpoints/business-profiles/business-profiles";
import type { Account } from "@/api/models";
import { pushModal } from "@/components/push-modals";
import { Badge } from "@/components/ui/badge";
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
import { BusinessProfileDropdown } from "@/features/settings/components/business-profile-dropdown";
import { MoreHorizontalIcon } from "lucide-react";

export function AccountBusinessProfilesCard({ account }: { account: Account }) {
  const { data } = useBusinessProfilesList({
    ordering: "-created_at",
    page_size: 20,
  });
  const profiles = data?.results ?? [];
  const defaultProfileId = account.default_business_profile?.id ?? null;

  return (
    <FormCard>
      <FormCardHeader>
        <FormCardTitle>Business profiles</FormCardTitle>
        <FormCardDescription>
          Manage business profiles used on invoices.
        </FormCardDescription>
      </FormCardHeader>
      <FormCardContent>
        {profiles.length > 0 ? (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Phone</TableHead>
                  <TableHead>
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {profiles.map((profile) => (
                  <TableRow key={profile.id}>
                    <TableCell className="space-x-2 font-medium">
                      <span>{profile.legal_name || "Untitled"}</span>
                      {profile.id === defaultProfileId && (
                        <Badge>Default</Badge>
                      )}
                    </TableCell>
                    <TableCell>{profile.email || "-"}</TableCell>
                    <TableCell>{profile.phone || "-"}</TableCell>
                    <TableCell className="text-right">
                      <BusinessProfileDropdown
                        profile={profile}
                        accountId={account.id}
                        defaultProfileId={defaultProfileId}
                      >
                        <Button
                          size="icon"
                          variant="ghost"
                          className="data-[state=open]:bg-accent size-7"
                        >
                          <MoreHorizontalIcon />
                        </Button>
                      </BusinessProfileDropdown>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          <Empty className="border border-dashed">
            <EmptyHeader>
              <EmptyTitle>No business profiles</EmptyTitle>
              <EmptyDescription>
                Add a business profile to display your legal details on
                invoices.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}
      </FormCardContent>
      <FormCardFooter>
        <Button
          type="button"
          onClick={() => pushModal("BusinessProfileCreateSheet")}
        >
          Add
        </Button>
      </FormCardFooter>
    </FormCard>
  );
}
