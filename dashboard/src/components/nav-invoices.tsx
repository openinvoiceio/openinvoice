import { useInvoicesList } from "@/api/endpoints/invoices/invoices";
import { InvoiceBadge } from "@/components/invoice-badge";
import { InvoiceDropdown } from "@/components/invoice-dropdown";
import { pushModal } from "@/components/push-modals.tsx";
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import { Link, useLocation } from "@tanstack/react-router";
import { MoreHorizontalIcon, PlusIcon } from "lucide-react";

export function NavInvoices() {
  const location = useLocation();
  const invoices = useInvoicesList();

  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden">
      <SidebarGroupLabel className="flex items-center justify-between pr-1">
        <span>Invoices</span>
        <div className="flex items-center gap-2">
          <SidebarMenuAction
            className="relative top-0 right-0 border"
            onClick={() =>
              pushModal("InvoiceCreateDialog", { defaultCustomer: undefined })
            }
          >
            <PlusIcon className="text-muted-foreground" />
          </SidebarMenuAction>
        </div>
      </SidebarGroupLabel>
      <SidebarMenu>
        {invoices?.data?.results.map((invoice) => {
          const href = `/invoices/${invoice.id}`;
          return (
            <SidebarMenuItem
              key={invoice.id}
              className="relative flex items-center"
            >
              <SidebarMenuButton isActive={location.pathname === href} asChild>
                <Link to={href} className="justify-between">
                  {invoice.number}
                </Link>
              </SidebarMenuButton>
              <div
                className={cn(
                  "absolute top-0.5 right-1 transition-all duration-200",
                  "group-focus-within/menu-item:right-7 group-hover/menu-action:right-6 group-hover/menu-item:right-7 [&:has(+[data-sidebar=menu-action][data-state=open])]:right-7",
                )}
              >
                <InvoiceBadge status={invoice.status} />
              </div>
              <InvoiceDropdown side="right" align="start" invoice={invoice}>
                <SidebarMenuAction className="outline-none" showOnHover>
                  <MoreHorizontalIcon />
                </SidebarMenuAction>
              </InvoiceDropdown>
            </SidebarMenuItem>
          );
        })}
      </SidebarMenu>
    </SidebarGroup>
  );
}
