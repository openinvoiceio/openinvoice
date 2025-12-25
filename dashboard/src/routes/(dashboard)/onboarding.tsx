import { useCustomersList } from "@/api/endpoints/customers/customers.ts";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header.tsx";
import { CustomerOnboardingCard } from "@/components/customer-onboarding-card.tsx";
import { InvoiceOnboardingCard } from "@/components/invoice-onboarding-card.tsx";
import { NavBreadcrumb } from "@/components/nav-breadcrumb.tsx";
import { SearchCommand } from "@/components/search-command.tsx";
import {
  ActionCard,
  ActionCardDescription,
  ActionCardGroup,
  ActionCardHeader,
  ActionCardTitle,
} from "@/components/ui/action-card.tsx";
import {
  Section,
  SectionDescription,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
import { SidebarTrigger } from "@/components/ui/sidebar.tsx";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowUpRightIcon } from "lucide-react";

export const Route = createFileRoute("/(dashboard)/onboarding")({
  component: RouteComponent,
});

const moreActions = [
  {
    title: "Setup product catalogue",
    description: "Add products, prices, coupons and tax rates",
    href: "/products",
  },
  {
    title: "Configure account",
    description: "Update your account settings and preferences",
    href: "/settings/account",
  },
  {
    title: "Manage customers",
    description: "Create even more customers to bill",
    href: "/customers",
  },
  {
    title: "Schedule a call",
    description: "Book a meeting with us to get you started with OpenInvoice.",
    href: "#",
  },
  {
    title: "Documentation",
    description: "Read our documentation to get started with OpenInvoice.",
    href: "https://docs.openinvoice.io",
  },
];

function RouteComponent() {
  const { account } = Route.useRouteContext();
  const customers = useCustomersList({ ordering: "created_at" });
  const firstCustomer = customers.data?.results?.[0];

  return (
    <div>
      <AppHeader>
        <AppHeaderContent>
          <SidebarTrigger />
          <NavBreadcrumb items={[{ type: "page", label: "Onboarding" }]} />
        </AppHeaderContent>
        <AppHeaderActions>
          <div className="flex items-center gap-2 text-sm">
            <SearchCommand />
          </div>
        </AppHeaderActions>
      </AppHeader>
      <main className="w-full flex-1">
        <SectionGroup>
          <Section>
            <SectionHeader>
              <SectionTitle>Getting Started</SectionTitle>
              <SectionDescription>
                Welcome to Invoicence. Let&apos;s issue your first invoice.
              </SectionDescription>
            </SectionHeader>
          </Section>
          <Section>
            <SectionHeader>
              <SectionDescription className="tabular-nums">
                Step <span className="text-foreground font-medium">1</span> of{" "}
                <span className="text-foreground font-medium">2</span>
              </SectionDescription>
            </SectionHeader>
            <CustomerOnboardingCard />
          </Section>
          <Section>
            <SectionHeader>
              <SectionDescription className="tabular-nums">
                Step <span className="text-foreground font-medium">2</span> of{" "}
                <span className="text-foreground font-medium">2</span>
              </SectionDescription>
            </SectionHeader>
            {!customers.isLoading && (
              <InvoiceOnboardingCard
                firstCustomer={firstCustomer}
                currency={account?.default_currency}
              />
            )}
          </Section>
          <Section>
            <SectionHeader>
              <SectionDescription className="tabular-nums">
                What&apos;s next?
              </SectionDescription>
            </SectionHeader>
            <ActionCardGroup className="sm:grid-cols-2">
              {moreActions.map((action) => {
                const isExternal = action.href.startsWith("http");
                return (
                  <Link to={action.href} key={action.title}>
                    <ActionCard className="h-full w-full">
                      <ActionCardHeader>
                        <ActionCardTitle className="flex items-center justify-between gap-2">
                          {action.title}
                          {isExternal && (
                            <ArrowUpRightIcon className="group-hover/action-card:text-foreground text-muted-foreground size-4 shrink-0" />
                          )}
                        </ActionCardTitle>
                        <ActionCardDescription>
                          {action.description}
                        </ActionCardDescription>
                      </ActionCardHeader>
                    </ActionCard>
                  </Link>
                );
              })}
            </ActionCardGroup>
          </Section>
        </SectionGroup>
      </main>
    </div>
  );
}
