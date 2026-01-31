import {
  getCreditNotesCommentsListQueryKey,
  getCreditNotesListQueryKey,
  getCreditNotesRetrieveQueryKey,
  useCreateCreditNoteComment,
  useCreditNotesCommentsList,
  useCreditNotesRetrieve,
  useDeleteCreditNoteComment,
  useIssueCreditNote,
  useUpdateCreditNote,
} from "@/api/endpoints/credit-notes/credit-notes";
import { useFilesRetrieve } from "@/api/endpoints/files/files.ts";
import { useInvoicesRetrieve } from "@/api/endpoints/invoices/invoices.ts";
import { useNumberingSystemsRetrieve } from "@/api/endpoints/numbering-systems/numbering-systems.ts";
import { CreditNoteStatusEnum } from "@/api/models";
import { AddressView } from "@/components/address-view.tsx";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { AppSidebar } from "@/components/app-sidebar";
import { CommentsForm } from "@/components/comments-form";
import { CommentsList } from "@/components/comments-list";
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { SearchCommand } from "@/components/search-command.tsx";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DataList,
  DataListItem,
  DataListLabel,
  DataListValue,
} from "@/components/ui/data-list";
import {
  DataSidebar,
  DataSidebarContent,
  DataSidebarList,
  DataSidebarSeparator,
  DataSidebarTitle,
  DataSidebarTrigger,
} from "@/components/ui/data-sidebar.tsx";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty.tsx";
import { Metadata } from "@/components/ui/metadata.tsx";
import {
  Section,
  SectionDescription,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { CreditNoteBadge } from "@/features/credit-notes/components/credit-note-badge";
import { CreditNoteDropdown } from "@/features/credit-notes/components/credit-note-dropdown.tsx";
import { NumberingSystemView } from "@/features/settings/components/numbering-system-view.tsx";
import { getErrorSummary } from "@/lib/api/errors";
import {
  formatAmount,
  formatDate,
  formatDatetime,
  formatEnum,
  formatPercentage,
} from "@/lib/formatters";
import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  BracesIcon,
  CheckIcon,
  InfoIcon,
  MoreHorizontalIcon,
  PencilIcon,
  UserIcon,
} from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/(dashboard)/credit-notes/$id")({
  component: RouteComponent,
});

function RouteComponent() {
  const { auth, account } = Route.useRouteContext();
  const { id } = Route.useParams();
  const queryClient = useQueryClient();
  const { data: creditNote } = useCreditNotesRetrieve(id);
  const { data: invoice } = useInvoicesRetrieve(creditNote?.invoice_id || "", {
    query: { enabled: !!creditNote?.invoice_id },
  });
  const { data: numberingSystem } = useNumberingSystemsRetrieve(
    creditNote?.numbering_system_id || "",
    { query: { enabled: !!creditNote?.numbering_system_id } },
  );
  const { data: logo } = useFilesRetrieve(creditNote?.customer.logo_id || "", {
    query: { enabled: !!creditNote?.customer?.logo_id },
  });

  async function invalidate() {
    await queryClient.invalidateQueries({
      queryKey: getCreditNotesRetrieveQueryKey(id),
    });
    await queryClient.invalidateQueries({
      queryKey: getCreditNotesListQueryKey(),
    });
  }

  const comments = useCreditNotesCommentsList(id, undefined, {
    query: { enabled: !!id },
  });
  const createComment = useCreateCreditNoteComment({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getCreditNotesCommentsListQueryKey(id),
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });
  const deleteComment = useDeleteCreditNoteComment({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getCreditNotesCommentsListQueryKey(id),
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  const issueMutation = useIssueCreditNote({
    mutation: {
      onSuccess: async () => {
        await invalidate();
        toast.success("Credit note issued");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  const updateCreditNote = useUpdateCreditNote({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  if (!creditNote) return null;

  const isDraft = creditNote.status === CreditNoteStatusEnum.draft;
  const hasLineTaxes = creditNote.lines.some((line) => line.taxes.length > 0);
  const summaryColSpan = hasLineTaxes ? 4 : 3;

  return (
    <SidebarProvider>
      <AppSidebar user={auth.user} account={account} />
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
                  { type: "page", label: creditNote.number || "Credit note" },
                ]}
              />
            </AppHeaderContent>
            <AppHeaderActions>
              <div className="flex items-center gap-2 text-sm">
                <SearchCommand />
                {isDraft && (
                  <Button type="button" variant="outline" size="sm" asChild>
                    <Link to="/credit-notes/$id/edit" params={{ id }}>
                      <PencilIcon />
                      Edit
                    </Link>
                  </Button>
                )}
                {isDraft && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={async () => {
                      await issueMutation.mutateAsync({ id, data: {} });
                    }}
                    disabled={issueMutation.isPending}
                  >
                    <CheckIcon />
                    Finalize
                  </Button>
                )}
                <CreditNoteDropdown
                  creditNote={creditNote}
                  actions={{
                    finalize: false,
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
          <main className="flex min-h-[calc(100svh_-_56px)]">
            <SectionGroup>
              <Section>
                <SectionHeader>
                  <div className="flex items-center gap-2">
                    <SectionTitle>{creditNote.number}</SectionTitle>
                    <CreditNoteBadge status={creditNote.status} />
                  </div>
                  <SectionDescription>
                    <span>Credited to </span>
                    <Link
                      to="/customers/$id"
                      params={{ id: creditNote.customer.id }}
                    >
                      <span className="text-primary underline-offset-4 hover:underline">
                        {creditNote.customer.name}
                      </span>
                    </Link>
                    <span> - </span>
                    <span>
                      {formatAmount(
                        creditNote.total_amount,
                        creditNote.currency,
                      )}
                    </span>
                  </SectionDescription>
                </SectionHeader>
              </Section>

              <Section>
                <SectionHeader>
                  <SectionTitle>Summary</SectionTitle>
                </SectionHeader>
                <div className="grid grid-cols-2 gap-4">
                  <DataList orientation="vertical" size="sm" className="gap-4">
                    <DataListItem>
                      <DataListLabel>Credited to</DataListLabel>
                      <DataListValue className="flex items-center gap-2">
                        <Avatar className="size-8 rounded-md">
                          <AvatarImage src={logo?.url} />
                          <AvatarFallback className="rounded-md">
                            <UserIcon className="size-4" />
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex flex-col self-start">
                          <div className="w-fit underline-offset-4 hover:underline">
                            <Link
                              to="/customers/$id"
                              params={{ id: creditNote.customer.id }}
                            >
                              {creditNote.customer.name}
                            </Link>
                          </div>
                          {creditNote.customer.email && (
                            <span className="text-muted-foreground">
                              {creditNote.customer.email}
                            </span>
                          )}
                        </div>
                      </DataListValue>
                    </DataListItem>
                    <DataListItem>
                      <DataListLabel>Billing address</DataListLabel>
                      <DataListValue>
                        <AddressView address={creditNote.customer.address} />
                      </DataListValue>
                    </DataListItem>
                  </DataList>

                  <DataList orientation="vertical" size="sm" className="gap-4">
                    <DataListItem>
                      <DataListLabel>Number</DataListLabel>
                      <DataListValue>{creditNote.number || "-"}</DataListValue>
                    </DataListItem>
                    <DataListItem>
                      <DataListLabel>Currency</DataListLabel>
                      <DataListValue>{creditNote.currency}</DataListValue>
                    </DataListItem>
                    <DataListItem>
                      <DataListLabel>Invoice</DataListLabel>
                      <DataListValue>
                        <Link
                          className="text-primary underline-offset-4 hover:underline"
                          to="/invoices/$id"
                          params={{ id: creditNote.invoice_id }}
                        >
                          {invoice?.number || "-"}
                        </Link>
                      </DataListValue>
                    </DataListItem>
                    <DataListItem>
                      <DataListLabel>Invoice total</DataListLabel>
                      <DataListValue>
                        {invoice &&
                          formatAmount(invoice.total_amount, invoice.currency)}
                      </DataListValue>
                    </DataListItem>
                    <DataListItem>
                      <DataListLabel>Reason</DataListLabel>
                      <DataListValue>
                        {formatEnum(creditNote.reason)}
                      </DataListValue>
                    </DataListItem>
                  </DataList>
                </div>

                <Table className="mt-2">
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-full">Description</TableHead>
                      <TableHead className="text-right">Quantity</TableHead>
                      <TableHead className="min-w-40 text-right">
                        Price
                      </TableHead>
                      {hasLineTaxes && (
                        <TableHead className="min-w-40 text-right">
                          Tax
                        </TableHead>
                      )}
                      <TableHead className="min-w-40 text-right">
                        Amount
                      </TableHead>
                      <TableHead className="w-10">
                        <span className="sr-only">Actions</span>
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {creditNote.lines.map((line) => (
                      <TableRow key={line.id}>
                        <TableCell>{line.description}</TableCell>
                        <TableCell className="text-right">
                          {line.quantity || "-"}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatAmount(line.unit_amount, creditNote.currency)}
                        </TableCell>
                        {hasLineTaxes &&
                          (line.taxes.length > 0 ? (
                            <TableCell className="text-right">
                              {/* TODO: fix this*/}
                              {/*{formatPercentage(line?.total_tax_rate || 0)}*/}
                              {formatPercentage("0")}
                            </TableCell>
                          ) : (
                            <TableCell />
                          ))}
                        <TableCell className="text-right text-emerald-400">
                          -{formatAmount(line.amount, creditNote.currency)}
                        </TableCell>
                        <TableCell>
                          <div className="flex justify-end">
                            {/*<InvoiceLineDropdown invoice={invoice} line={line}>*/}
                            {/*  <Button*/}
                            {/*      size="icon"*/}
                            {/*      variant="ghost"*/}
                            {/*      className="data-[state=open]:bg-accent size-7"*/}
                            {/*  >*/}
                            {/*    <MoreHorizontalIcon />*/}
                            {/*  </Button>*/}
                            {/*</InvoiceLineDropdown>*/}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                    {creditNote.lines.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5 + (hasLineTaxes ? 1 : 0)}>
                          <Empty>
                            <EmptyHeader>
                              <EmptyTitle>
                                {creditNote.status ===
                                CreditNoteStatusEnum.draft
                                  ? "No lines added yet"
                                  : "No lines"}
                              </EmptyTitle>
                              <EmptyDescription>
                                {creditNote.status ===
                                CreditNoteStatusEnum.draft
                                  ? "Choose lines to credit from the invoice."
                                  : "This credit note has no lines."}
                              </EmptyDescription>
                            </EmptyHeader>
                          </Empty>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                  <TableFooter className="[&_tr]:border-0">
                    <TableRow>
                      <TableCell
                        colSpan={summaryColSpan}
                        className="text-right font-medium"
                      >
                        Subtotal
                      </TableCell>
                      <TableCell className="text-right font-medium text-emerald-400">
                        -
                        {formatAmount(
                          creditNote.subtotal_amount,
                          creditNote.currency,
                        )}
                      </TableCell>
                      <TableCell className="p-0" />
                    </TableRow>
                    <TableRow>
                      <TableCell
                        colSpan={summaryColSpan}
                        className="text-right font-medium"
                      >
                        Total excluding tax
                      </TableCell>
                      <TableCell
                        className="font-medium text-emerald-400"
                        align="right"
                      >
                        -
                        {formatAmount(
                          creditNote.total_amount_excluding_tax,
                          creditNote.currency,
                        )}
                      </TableCell>
                      <TableCell className="p-0" />
                    </TableRow>
                    {creditNote.tax_breakdown.map((item) => (
                      <TableRow key={item.name}>
                        <TableCell
                          colSpan={summaryColSpan}
                          className="text-right font-medium"
                        >
                          {item.name} {formatPercentage(item.rate)}
                        </TableCell>
                        <TableCell
                          className="font-medium text-emerald-400"
                          align="right"
                        >
                          -{formatAmount(item.amount, creditNote.currency)}
                        </TableCell>
                        <TableCell className="p-0" />
                      </TableRow>
                    ))}
                    <TableRow>
                      <TableCell
                        colSpan={summaryColSpan}
                        className="text-right font-medium"
                      >
                        Total credited
                      </TableCell>
                      <TableCell
                        className="font-medium text-emerald-400"
                        align="right"
                      >
                        -
                        {formatAmount(
                          creditNote.total_amount,
                          creditNote.currency,
                        )}
                      </TableCell>
                      <TableCell className="p-0" />
                    </TableRow>
                  </TableFooter>
                </Table>
              </Section>

              <Section>
                <SectionHeader>
                  <SectionTitle>Comments</SectionTitle>
                </SectionHeader>
                <div className="space-y-4">
                  <CommentsList
                    comments={comments.data?.results ?? []}
                    isLoading={comments.isLoading}
                    onDelete={(commentId) =>
                      deleteComment.mutateAsync({
                        creditNoteId: creditNote.id,
                        id: commentId,
                      })
                    }
                  />
                  <CommentsForm
                    isCreating={createComment.isPending}
                    onCreate={(data) =>
                      createComment.mutateAsync({
                        creditNoteId: creditNote.id,
                        data,
                      })
                    }
                  />
                </div>
              </Section>
            </SectionGroup>
            <DataSidebar defaultValue="overview">
              <DataSidebarList>
                <DataSidebarTrigger value="overview">
                  <InfoIcon />
                </DataSidebarTrigger>
                <DataSidebarTrigger value="metadata">
                  <BracesIcon />
                </DataSidebarTrigger>
              </DataSidebarList>
              <DataSidebarContent value="overview">
                <DataSidebarTitle>Overview</DataSidebarTitle>
                <DataList
                  orientation="vertical"
                  className="gap-3 px-4"
                  size="sm"
                >
                  <DataListItem>
                    <DataListLabel>ID</DataListLabel>
                    <DataListValue>{creditNote.id}</DataListValue>
                  </DataListItem>
                  {creditNote.issue_date && (
                    <DataListItem>
                      <DataListLabel>Issue date</DataListLabel>
                      <DataListValue>
                        {formatDate(creditNote.issue_date)}
                      </DataListValue>
                    </DataListItem>
                  )}
                  <DataListItem>
                    <DataListLabel>Created</DataListLabel>
                    <DataListValue>
                      {formatDatetime(creditNote.created_at)}
                    </DataListValue>
                  </DataListItem>
                  {creditNote.issued_at && (
                    <DataListItem>
                      <DataListLabel>Issued</DataListLabel>
                      <DataListValue>
                        {formatDatetime(creditNote.issued_at)}
                      </DataListValue>
                    </DataListItem>
                  )}
                  {creditNote.voided_at && (
                    <DataListItem>
                      <DataListLabel>Voided</DataListLabel>
                      <DataListValue>
                        {formatDatetime(creditNote.voided_at)}
                      </DataListValue>
                    </DataListItem>
                  )}
                  <DataListItem>
                    <DataListLabel>Last updated</DataListLabel>
                    <DataListValue>
                      {creditNote.updated_at
                        ? formatDatetime(creditNote.updated_at)
                        : "-"}
                    </DataListValue>
                  </DataListItem>
                  {creditNote.payment_provider && (
                    <DataListItem>
                      <DataListLabel>Payment provider</DataListLabel>
                      <DataListValue>
                        {creditNote.payment_provider}
                      </DataListValue>
                    </DataListItem>
                  )}
                </DataList>
                <DataSidebarSeparator />
                <DataList
                  orientation="vertical"
                  className="gap-3 px-4"
                  size="sm"
                >
                  <DataListItem>
                    <DataListLabel>Invoice</DataListLabel>
                    <DataListValue>
                      <Link
                        className="text-primary underline-offset-4 hover:underline"
                        to="/invoices/$id"
                        params={{ id: creditNote.invoice_id }}
                      >
                        {invoice?.number || "-"}
                      </Link>
                    </DataListValue>
                  </DataListItem>
                  <DataListItem>
                    <DataListLabel>Reason</DataListLabel>
                    <DataListValue>
                      {formatEnum(creditNote.reason)}
                    </DataListValue>
                  </DataListItem>
                </DataList>
                {numberingSystem && (
                  <>
                    <DataSidebarSeparator />
                    <DataList
                      orientation="vertical"
                      className="gap-3 px-4"
                      size="sm"
                    >
                      <DataListItem>
                        <DataListLabel>Numbering system</DataListLabel>
                        <DataListValue>
                          <NumberingSystemView
                            numberingSystem={numberingSystem}
                          />
                        </DataListValue>
                      </DataListItem>
                    </DataList>
                  </>
                )}
                <DataSidebarSeparator />
                <DataList
                  orientation="vertical"
                  className="gap-3 px-4"
                  size="sm"
                >
                  <DataListItem>
                    <DataListLabel>Delivery method</DataListLabel>
                    <DataListValue>
                      {formatEnum(creditNote.delivery_method)}
                    </DataListValue>
                  </DataListItem>
                  <DataListItem>
                    <DataListLabel>Recipients</DataListLabel>
                    <DataListValue>
                      {creditNote.recipients.length > 0 ? (
                        <ul className="space-y-0.5">
                          {creditNote.recipients.map((recipient) => (
                            <li key={recipient} className="truncate">
                              {recipient}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <span>No recipients</span>
                      )}
                    </DataListValue>
                  </DataListItem>
                </DataList>
              </DataSidebarContent>
              <DataSidebarContent value="metadata">
                <DataSidebarTitle>Metadata</DataSidebarTitle>
                <Metadata
                  className="my-1 px-4"
                  data={creditNote.metadata as Record<string, string>}
                  onSubmit={(metadata) => {
                    void updateCreditNote.mutateAsync({
                      id: id,
                      data: { metadata },
                    });
                  }}
                  submitOnChange
                />
              </DataSidebarContent>
            </DataSidebar>
          </main>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
