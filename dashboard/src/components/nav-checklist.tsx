import { useCustomersList } from "@/api/endpoints/customers/customers.ts";
import { useInvoicesList } from "@/api/endpoints/invoices/invoices.ts";
import { InvoiceStatusEnum } from "@/api/models";
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Link } from "@tanstack/react-router";
import { CircleCheck, CircleDashed, XIcon } from "lucide-react";
import { useState } from "react";

const KEY = "navChecklist.dismissed";

export function NavChecklist() {
  const [dismissed, setDismissed] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    try {
      return localStorage.getItem(KEY) === "1";
    } catch {
      return false;
    }
  });
  const handleClose = () => {
    try {
      localStorage.setItem(KEY, "1");
    } catch {}
    setDismissed(true);
  };
  if (dismissed) return null;
  return <NavChecklistGroup onClose={handleClose} />;
}

function NavChecklistGroup({ onClose }: { onClose?: () => void }) {
  const customers = useCustomersList();
  const invoices = useInvoicesList();

  const items = [
    {
      title: "Create Customer",
      checked: !!customers.data?.results.length,
    },
    {
      title: "Issue Invoice",
      checked: !!invoices.data?.results.length,
    },
    {
      title: "Finalize Invoice",
      checked: invoices.data?.results.some(
        (invoice) => invoice.status !== InvoiceStatusEnum.draft,
      ),
    },
  ];

  return (
    <SidebarGroup className="bg-background rounded-lg border group-data-[collapsible=icon]:hidden">
      <SidebarGroupLabel className="flex items-center justify-between pr-1">
        <span>Getting Started</span>
        <SidebarMenuAction className="relative top-0 right-0" onClick={onClose}>
          <XIcon className="text-muted-foreground size-4" />
        </SidebarMenuAction>
      </SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => (
          <SidebarMenuItem
            key={item.title}
            className="flex items-center gap-2 text-sm"
          >
            {item.checked ? (
              <>
                <CircleCheck className="size-3 text-emerald-500" />
                <span>{item.title}</span>
              </>
            ) : (
              <>
                <CircleDashed className="text-muted-foreground/50 size-3" />
                <Link to="/onboarding">{item.title}</Link>
              </>
            )}
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  );
}
