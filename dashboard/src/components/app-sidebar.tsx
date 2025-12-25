import type { Account, User } from "@/api/models";
import { AccountSwitcher } from "@/components/account-switcher";
import { NavChecklist } from "@/components/nav-checklist.tsx";
import { NavCreditNotes } from "@/components/nav-credit-notes";
import { NavInvoices } from "@/components/nav-invoices";
import { NavOverview } from "@/components/nav-overview";
import { NavSupport } from "@/components/nav-support.tsx";
import { NavUser } from "@/components/nav-user";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar";
import {
  BoxIcon,
  CogIcon,
  FileMinusIcon,
  FilePenLineIcon,
  LayoutGridIcon,
  ReceiptTextIcon,
  UsersIcon,
} from "lucide-react";
import * as React from "react";

const data = [
  {
    name: "Overview",
    icon: LayoutGridIcon,
    url: "/overview",
  },
  {
    name: "Invoices",
    icon: ReceiptTextIcon,
    url: "/invoices",
  },
  {
    name: "Quotes",
    icon: FilePenLineIcon,
    url: "/quotes",
  },
  {
    name: "Credit notes",
    icon: FileMinusIcon,
    url: "/credit-notes",
  },
  {
    name: "Customers",
    icon: UsersIcon,
    url: "/customers",
  },
  {
    name: "Product catalogue",
    icon: BoxIcon,
    url: "/products",
    related: ["/coupons", "/tax-rates"],
  },
  {
    name: "Settings",
    icon: CogIcon,
    url: "/settings/account",
  },
];

interface AppSidebarProps extends React.ComponentProps<typeof Sidebar> {
  user: User;
  account: Account;
}

export function AppSidebar({ user, account, ...props }: AppSidebarProps) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader className="flex h-14 justify-center border-b py-1">
        <AccountSwitcher activeAccount={account} />
      </SidebarHeader>
      <SidebarContent>
        <NavOverview items={data} />
        <NavInvoices />
        <NavCreditNotes />
        <div className="mt-auto px-2">
          <NavChecklist />
        </div>
        <NavSupport user={user} />
      </SidebarContent>
      <SidebarFooter className="border-t">
        <NavUser user={user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
