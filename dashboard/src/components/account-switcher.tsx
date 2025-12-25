import {
  useAccountsList,
  useSwitchAccount,
} from "@/api/endpoints/accounts/accounts";
import type { Account } from "@/api/models";
import { pushModal } from "@/components/push-modals";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { usePlan } from "@/hooks/use-plan";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { BuildingIcon, CheckIcon, ChevronsUpDown, Plus } from "lucide-react";

export function AccountSwitcher({ activeAccount }: { activeAccount: Account }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isMobile, setOpenMobile } = useSidebar();
  const { data: accounts } = useAccountsList();
  const switchAccount = useSwitchAccount({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries();
        await navigate({ to: "/overview" });
      },
    },
  });

  const { currentPlan } = usePlan(activeAccount);

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <Avatar className="size-8 rounded-md">
                <AvatarImage src={activeAccount.logo_url || undefined} />
                <AvatarFallback className="rounded-md">
                  <BuildingIcon className="size-4" />
                </AvatarFallback>
              </Avatar>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">
                  {activeAccount.name}
                </span>
                <span className="truncate text-xs">{currentPlan?.title}</span>
              </div>
              <ChevronsUpDown className="ml-auto" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
            align="start"
            side={isMobile ? "bottom" : "right"}
            sideOffset={4}
          >
            <DropdownMenuLabel className="text-muted-foreground text-xs">
              Accounts
            </DropdownMenuLabel>
            {accounts?.results.map((account) => (
              <DropdownMenuItem
                key={account.id}
                onClick={async () => {
                  await switchAccount.mutateAsync({ id: account.id });
                  setOpenMobile(false);
                }}
                className="flex justify-between p-2"
              >
                <span>{account.name}</span>
                {account.id === activeAccount.id && <CheckIcon />}
              </DropdownMenuItem>
            ))}
            {currentPlan && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="gap-2"
                  onClick={() => pushModal("AccountCreateDialog")}
                >
                  <div className="flex size-6 items-center justify-center rounded-md border bg-transparent">
                    <Plus className="size-4" />
                  </div>
                  <div className="font-medium">Create account</div>
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
