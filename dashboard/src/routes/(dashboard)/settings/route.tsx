import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { SearchCommand } from "@/components/search-command.tsx";
import { SidebarTrigger } from "@/components/ui/sidebar.tsx";
import { usePlan } from "@/hooks/use-plan.tsx";
import { createFileRoute, Outlet } from "@tanstack/react-router";
import {
  BuildingIcon,
  CreditCardIcon,
  UnplugIcon,
  UserIcon,
} from "lucide-react";

export const Route = createFileRoute("/(dashboard)/settings")({
  component: RouteComponent,
});

function RouteComponent() {
  const { isBillingEnabled } = usePlan();

  return (
    <div>
      <AppHeader>
        <AppHeaderContent>
          <SidebarTrigger />
          <NavBreadcrumb
            items={[
              { type: "page", label: "Settings" },
              {
                type: "select",
                items: [
                  {
                    value: "/settings/account",
                    label: "Account",
                    icon: BuildingIcon,
                  },
                  {
                    value: "/settings/profile",
                    label: "Profile",
                    icon: UserIcon,
                  },
                  ...(isBillingEnabled
                    ? [
                        {
                          value: "/settings/billing",
                          label: "Billing",
                          icon: CreditCardIcon,
                        },
                      ]
                    : []),
                  {
                    value: "/settings/integrations",
                    label: "Integrations",
                    icon: UnplugIcon,
                  },
                ],
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
      <main className="w-full flex-1">
        <Outlet />
      </main>
    </div>
  );
}
