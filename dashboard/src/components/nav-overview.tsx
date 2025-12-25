import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { Link, useLocation } from "@tanstack/react-router";
import { type LucideIcon } from "lucide-react";

export function NavOverview({
  items,
}: {
  items: {
    name: string;
    url: string;
    icon: LucideIcon;
    related?: string[];
  }[];
}) {
  const location = useLocation();
  const { setOpenMobile } = useSidebar();
  return (
    <SidebarGroup>
      <SidebarGroupLabel>Workspace</SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => (
          <SidebarMenuItem key={item.name}>
            <SidebarMenuButton
              isActive={
                location.pathname.includes(item.url) ||
                item.related?.some((r) => location.pathname.includes(r))
              }
              asChild
              tooltip={item.name}
            >
              <Link to={item.url} onClick={() => setOpenMobile(false)}>
                <item.icon />
                <span>{item.name}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  );
}
