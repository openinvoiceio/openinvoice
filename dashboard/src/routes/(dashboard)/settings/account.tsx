import { FormCardGroup } from "@/components/ui/form-card";
import {
  Section,
  SectionDescription,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
import { AccountBusinessProfilesCard } from "@/features/settings/components/account-business-profiles-card";
import { AccountGeneralCard } from "@/features/settings/components/account-general-card";
import { AccountInvoicingCard } from "@/features/settings/components/account-invoicing-card";
import { AccountMembersCard } from "@/features/settings/components/account-members-card";
import { AccountNumberingSystemsCard } from "@/features/settings/components/account-numbering-systems-card";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/(dashboard)/settings/account")({
  component: RouteComponent,
});

function RouteComponent() {
  const { account } = Route.useRouteContext();
  if (!account) return null;

  return (
    <SectionGroup>
      <Section>
        <SectionHeader>
          <SectionTitle>Account</SectionTitle>
          <SectionDescription>Manage your account settings.</SectionDescription>
        </SectionHeader>
        <FormCardGroup>
          <AccountGeneralCard account={account} />
          <AccountInvoicingCard account={account} />
          <AccountBusinessProfilesCard account={account} />
          <AccountNumberingSystemsCard account={account} />
          <AccountMembersCard isLocked={!account.subscription} />
        </FormCardGroup>
      </Section>
    </SectionGroup>
  );
}
