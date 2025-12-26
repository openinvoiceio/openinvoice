import type { User } from "@/api/models";
import { FeedbackPopover } from "@/components/feedback-popover";
import { pushModal } from "@/components/push-modals";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  Book,
  Braces,
  CalendarClock,
  HelpCircle,
  LifeBuoy,
  MessageSquareIcon,
} from "lucide-react";

export function NavSupport({ user }: { user: User }) {
  const { isMobile } = useSidebar();
  return (
    <SidebarGroup>
      <SidebarGroupContent>
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton tooltip="Get Help">
                  <HelpCircle />
                  <span>Get Help</span>
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
                side={isMobile ? "bottom" : "right"}
                align="end"
                sideOffset={4}
              >
                <DropdownMenuLabel className="text-muted-foreground text-xs">
                  Get Help
                </DropdownMenuLabel>
                <DropdownMenuItem onClick={() => pushModal("SupportDialog")}>
                  <LifeBuoy />
                  Support
                </DropdownMenuItem>
                <DropdownMenuItem asChild disabled>
                  <a href="https://openinvoice.io/docs">
                    <Book /> Docs
                  </a>
                </DropdownMenuItem>
                <DropdownMenuItem asChild disabled>
                  <a href="https://openinvoice.io/api-reference">
                    <Braces /> API Reference
                  </a>
                </DropdownMenuItem>
                <DropdownMenuItem asChild disabled>
                  <CalendarClock /> Book a Call
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <FeedbackPopover user={user}>
              <SidebarMenuButton tooltip="Feedback">
                <MessageSquareIcon />
                <span>Feedback</span>
              </SidebarMenuButton>
            </FeedbackPopover>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}
