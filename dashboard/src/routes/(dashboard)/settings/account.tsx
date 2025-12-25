import { AccountAddressCard } from "@/components/account-address-card";
import { AccountGeneralCard } from "@/components/account-general-card";
import { AccountInvoicingCard } from "@/components/account-invoicing-card";
import { AccountMembersCard } from "@/components/account-members-card";
import { AccountNumberingSystemsCard } from "@/components/account-numbering-systems-card";
import { AccountTaxIdsCard } from "@/components/account-tax-ids-card";
import { FormCardGroup } from "@/components/ui/form-card";
import {
  Section,
  SectionDescription,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
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
          <AccountAddressCard account={account} />
          <AccountInvoicingCard account={account} />
          <AccountNumberingSystemsCard account={account} />
          <AccountTaxIdsCard account={account} />
          <AccountMembersCard isLocked={!account.subscription} />
        </FormCardGroup>
      </Section>
    </SectionGroup>
  );
}
