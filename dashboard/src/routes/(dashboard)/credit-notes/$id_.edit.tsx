import { useCreditNotesRetrieve } from "@/api/endpoints/credit-notes/credit-notes";
import { CreditNoteStatusEnum } from "@/api/models";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { AppSidebar } from "@/components/app-sidebar";
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { pushModal } from "@/components/push-modals";
import { SearchCommand } from "@/components/search-command.tsx";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
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
} from "@/components/ui/sidebar";
import { CreditNoteBadge } from "@/features/credit-notes/components/credit-note-badge";
import { CreditNoteDeliveryCard } from "@/features/credit-notes/components/credit-note-delivery-card";
import { CreditNoteDropdown } from "@/features/credit-notes/components/credit-note-dropdown.tsx";
import { CreditNoteInvoiceCard } from "@/features/credit-notes/components/credit-note-invoice-card.tsx";
import { CreditNoteLinesCard } from "@/features/credit-notes/components/credit-note-lines-card.tsx";
import { CreditNoteNumberingCard } from "@/features/credit-notes/components/credit-note-numbering-card";
import { CreditNotePreview } from "@/features/credit-notes/components/credit-note-preview";
import { createFileRoute, Navigate } from "@tanstack/react-router";
import { FileTextIcon, MoreHorizontalIcon } from "lucide-react";

export const Route = createFileRoute("/(dashboard)/credit-notes/$id_/edit")({
  component: RouteComponent,
});

function RouteComponent() {
  const { auth, account } = Route.useRouteContext();
  const { id } = Route.useParams();
  const { data: creditNote } = useCreditNotesRetrieve(id);

  if (!creditNote) return null;
  if (creditNote.status !== CreditNoteStatusEnum.draft) {
    return <Navigate to="/credit-notes/$id" params={{ id }} />;
  }

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
                    label: "Credit notes",
                    href: "/credit-notes",
                  },
                  {
                    type: "link",
                    label: creditNote.number || creditNote.id,
                    href: `/credit-notes/${creditNote.id}`,
                  },
                  { type: "page", label: "Edit" },
                ]}
              />
            </AppHeaderContent>
            <AppHeaderActions>
              <div className="flex items-center gap-2 text-sm">
                <SearchCommand />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="2xl:hidden"
                  onClick={() =>
                    pushModal("CreditNotePreviewDialog", { creditNote })
                  }
                >
                  <FileTextIcon />
                  Preview
                </Button>
                <CreditNoteDropdown
                  creditNote={creditNote}
                  actions={{
                    edit: false,
                  }}
                >
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    className="data-[state=open]:bg-accent size-8"
                  >
                    <MoreHorizontalIcon />
                  </Button>
                </CreditNoteDropdown>
              </div>
            </AppHeaderActions>
          </AppHeader>
          <main className="flex-1">
            <SectionGroup className="grid gap-2 2xl:max-w-7xl 2xl:grid-cols-2">
              <ScrollArea
                className="h-[calc(100svh_-_152px)] pr-3"
                type="scroll"
              >
                <Section>
                  <SectionHeader>
                    <div className="flex items-center gap-2">
                      <SectionTitle>Edit credit note</SectionTitle>
                      <CreditNoteBadge status={creditNote.status} />
                    </div>
                  </SectionHeader>
                  <CreditNoteInvoiceCard creditNote={creditNote} />
                  <CreditNoteNumberingCard creditNote={creditNote} />
                  <CreditNoteLinesCard creditNote={creditNote} />
                  <CreditNoteDeliveryCard creditNote={creditNote} />
                </Section>
              </ScrollArea>
              <Section className="hidden max-w-[600px] 2xl:block">
                <SectionHeader>
                  <SectionTitle>Preview</SectionTitle>
                </SectionHeader>
                <CreditNotePreview creditNote={creditNote} />
              </Section>
            </SectionGroup>
          </main>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
