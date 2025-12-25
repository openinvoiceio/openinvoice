import {
  getCreditNotesListQueryKey,
  getCreditNotesRetrieveQueryKey,
  useCreateCreditNote,
  useCreditNotesList,
} from "@/api/endpoints/credit-notes/credit-notes";
import { InvoiceStatusEnum } from "@/api/models";
import { CreditNoteBadge } from "@/components/credit-note-badge";
import { CreditNoteDropdown } from "@/components/credit-note-dropdown";
import { InvoiceCombobox } from "@/components/invoice-combobox.tsx";
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import { useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useNavigate } from "@tanstack/react-router";
import { MoreHorizontalIcon, PlusIcon } from "lucide-react";
import { toast } from "sonner";

export function NavCreditNotes() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const creditNotes = useCreditNotesList({ page_size: 10 });
  const { mutateAsync, isPending } = useCreateCreditNote({
    mutation: {
      onSuccess: async (creditNote) => {
        await queryClient.invalidateQueries({
          queryKey: getCreditNotesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getCreditNotesRetrieveQueryKey(creditNote.id),
        });
        toast.success("Credit note created");
        await navigate({
          to: "/credit-notes/$id/edit",
          params: { id: creditNote.id },
        });
      },
    },
  });

  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden">
      <SidebarGroupLabel className="flex items-center justify-between pr-1">
        <span>Credit notes</span>
        <div className="flex items-center gap-2">
          <InvoiceCombobox
            side="right"
            align="start"
            onSelect={async (invoice) => {
              if (isPending || !invoice) return;
              await mutateAsync({ data: { invoice_id: invoice.id } });
            }}
            status={[InvoiceStatusEnum.open, InvoiceStatusEnum.paid]}
            minOutstandingAmount={0.01}
          >
            <SidebarMenuAction className="relative top-0 right-0 border">
              <PlusIcon className="text-muted-foreground" />
            </SidebarMenuAction>
          </InvoiceCombobox>
        </div>
      </SidebarGroupLabel>
      <SidebarMenu>
        {creditNotes.data?.results.map((creditNote) => {
          const href = `/credit-notes/${creditNote.id}`;
          return (
            <SidebarMenuItem
              key={creditNote.id}
              className="relative flex items-center"
            >
              <SidebarMenuButton isActive={location.pathname === href} asChild>
                <Link to={href} className="justify-between">
                  {creditNote.number}
                </Link>
              </SidebarMenuButton>
              <div
                className={cn(
                  "absolute top-0.5 right-1 transition-all duration-200",
                  "group-focus-within/menu-item:right-7 group-hover/menu-action:right-6 group-hover/menu-item:right-7 [&:has(+[data-sidebar=menu-action][data-state=open])]:right-7",
                )}
              >
                <CreditNoteBadge status={creditNote.status} />
              </div>
              <CreditNoteDropdown
                side="right"
                align="start"
                creditNote={creditNote}
              >
                <SidebarMenuAction className="outline-none" showOnHover>
                  <MoreHorizontalIcon />
                </SidebarMenuAction>
              </CreditNoteDropdown>
            </SidebarMenuItem>
          );
        })}
      </SidebarMenu>
    </SidebarGroup>
  );
}
