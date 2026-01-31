import { useCustomersRetrieve } from "@/api/endpoints/customers/customers";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { AppSidebar } from "@/components/app-sidebar";
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { SearchCommand } from "@/components/search-command.tsx";
import {
  Section,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar.tsx";
import { CustomerBillingAddressCard } from "@/features/customers/components/customer-billing-address-card";
import { CustomerGeneralCard } from "@/features/customers/components/customer-general-card";
import { CustomerInvoicingCard } from "@/features/customers/components/customer-invoicing-card";
import { CustomerShippingCard } from "@/features/customers/components/customer-shipping-card";
import { CustomerTaxIdsCard } from "@/features/customers/components/customer-tax-ids-card";
import { CustomerTaxRatesCard } from "@/features/customers/components/customer-tax-rates-card";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/(dashboard)/customers/$id_/edit")({
  component: RouteComponent,
});

function RouteComponent() {
  const { auth, account } = Route.useRouteContext();
  const { id } = Route.useParams();
  const { data: customer } = useCustomersRetrieve(id);

  if (!customer) return;

  return (
    <SidebarProvider>
      <AppSidebar user={auth?.user} account={account} />
      <SidebarInset>
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
      </SidebarInset>
    </SidebarProvider>
  );
}
