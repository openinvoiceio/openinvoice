import { useCustomersRetrieve } from "@/api/endpoints/customers/customers";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { CustomerBillingAddressCard } from "@/components/customer-billing-address-card";
import { CustomerGeneralCard } from "@/components/customer-general-card";
import { CustomerInvoicingCard } from "@/components/customer-invoicing-card";
import { CustomerShippingCard } from "@/components/customer-shipping-card";
import { CustomerTaxIdsCard } from "@/components/customer-tax-ids-card";
import { CustomerTaxRatesCard } from "@/components/customer-tax-rates-card";
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { SearchCommand } from "@/components/search-command.tsx";
import {
  Section,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
import { SidebarTrigger } from "@/components/ui/sidebar.tsx";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/(dashboard)/customers/$id_/edit")({
  component: RouteComponent,
});

function RouteComponent() {
  const { id } = Route.useParams();
  const { data: customer } = useCustomersRetrieve(id);

  if (!customer) return;

  return (
    <div>
      <AppHeader>
        <AppHeaderContent>
          <SidebarTrigger />
          <NavBreadcrumb
            items={[
              {
                type: "link",
                label: "Customers",
                href: "/customers",
              },
              {
                type: "link",
                label: customer.name,
                href: `/customers/${customer.id}`,
              },
              {
                type: "page",
                label: "Edit",
              },
            ]}
          />
        </AppHeaderContent>
        <AppHeaderActions>
          <div className="flex items-center gap-2 text-sm">
            <SearchCommand />
          </div>
        </AppHeaderActions>
      </AppHeader>
      <main className="flex-1">
        <SectionGroup>
          <Section>
            <SectionHeader>
              <SectionTitle>Edit customer</SectionTitle>
            </SectionHeader>
            <CustomerGeneralCard customer={customer} />
            <CustomerInvoicingCard customer={customer} />
            <CustomerTaxRatesCard customer={customer} />
            <CustomerTaxIdsCard customer={customer} />
            <CustomerBillingAddressCard customer={customer} />
            <CustomerShippingCard customer={customer} />
          </Section>
        </SectionGroup>
      </main>
    </div>
  );
}
