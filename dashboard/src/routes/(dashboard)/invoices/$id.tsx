import { useCreditNotesList } from "@/api/endpoints/credit-notes/credit-notes";
import { useFilesRetrieve } from "@/api/endpoints/files/files";
import {
  getInvoicesCommentsListQueryKey,
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
  useCreateInvoiceComment,
  useDeleteInvoiceComment,
  useFinalizeInvoice,
  useInvoicesCommentsList,
  useInvoicesRetrieve,
  useUpdateInvoice,
} from "@/api/endpoints/invoices/invoices";
import { useNumberingSystemsRetrieve } from "@/api/endpoints/numbering-systems/numbering-systems";
import { usePaymentsList } from "@/api/endpoints/payments/payments";
import { InvoiceStatusEnum } from "@/api/models";
import { AddressView } from "@/components/address-view";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { AppSidebar } from "@/components/app-sidebar";
import { CommentsForm } from "@/components/comments-form";
import { CommentsList } from "@/components/comments-list";
import {
  DataTable,
  DataTableContainer,
} from "@/components/data-table/data-table";
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { pushModal } from "@/components/push-modals";
import { SearchCommand } from "@/components/search-command.tsx";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
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
  EmptyContent,
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
} from "@/components/ui/sidebar.tsx";
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { columns } from "@/features/credit-notes/components/credit-note-table";
import { InvoiceBadge } from "@/features/invoices/components/invoice-badge";
import { InvoiceDropdown } from "@/features/invoices/components/invoice-dropdown";
import { InvoiceLineDropdown } from "@/features/invoices/components/invoice-line-dropdown";
import { PaymentBadge } from "@/features/invoices/components/payment-badge";
import { NumberingSystemView } from "@/features/settings/components/numbering-system-view";
import { useDataTable } from "@/hooks/use-data-table.ts";
import { useDownload } from "@/hooks/use-download";
import { getErrorSummary } from "@/lib/api/errors";
import { getInitialColumnVisibility } from "@/lib/data-table.ts";
import {
  formatAmount,
  formatDate,
  formatDatetime,
  formatEnum,
  formatLanguage,
  formatPercentage,
} from "@/lib/formatters";
import { cn } from "@/lib/utils.ts";
import { createFileRoute, Link } from "@tanstack/react-router";
import { addDays } from "date-fns";
import {
  BracesIcon,
  CheckIcon,
  CreditCardIcon,
  DownloadIcon,
  InfoIcon,
  MoreHorizontalIcon,
  PencilIcon,
  UserIcon,
} from "lucide-react";
import { Fragment } from "react";
import { toast } from "sonner";

export const Route = createFileRoute("/(dashboard)/invoices/$id")({
  component: RouteComponent,
});

function RouteComponent() {
  const { id } = Route.useParams();
  const { auth, account, queryClient } = Route.useRouteContext();
  const { download, isDownloading } = useDownload();
  const { data: invoice } = useInvoicesRetrieve(id);
  const { data: numberingSystem } = useNumberingSystemsRetrieve(
    invoice?.numbering_system_id || "",
    { query: { enabled: !!invoice?.numbering_system_id } },
  );
  const { data: logo } = useFilesRetrieve(invoice?.customer.logo_id || "", {
    query: { enabled: !!invoice?.customer?.logo_id },
  });
  const payments = usePaymentsList({ invoice_id: id });
  const creditNotes = useCreditNotesList({ invoice_id: id });

  async function invalidate() {
    await queryClient.invalidateQueries({
      queryKey: getInvoicesListQueryKey(),
    });
    await queryClient.invalidateQueries({
      queryKey: getInvoicesRetrieveQueryKey(id),
    });
    await queryClient.invalidateQueries({
      queryKey: getPreviewInvoiceQueryKey(id),
    });
  }

  const updateInvoice = useUpdateInvoice({
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

  const comments = useInvoicesCommentsList(id, undefined, {
    query: { enabled: !!id },
  });
  const createComment = useCreateInvoiceComment({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getInvoicesCommentsListQueryKey(id),
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });
  const deleteComment = useDeleteInvoiceComment({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getInvoicesCommentsListQueryKey(id),
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  const finalizeInvoice = useFinalizeInvoice({
    mutation: {
      onSuccess: async () => {
        await invalidate();
        toast.success("Invoice finalized");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  const { table: creditNotesTable } = useDataTable({
    data: creditNotes.data?.results ?? [],
    columns,
    pageCount: creditNotes.data?.count
      ? Math.ceil(creditNotes.data.count / 20)
      : 0,
    initialState: {
      columnVisibility: getInitialColumnVisibility(columns, [
        "number",
        "total_amount",
        "issue_date",
        "status",
        "actions",
      ]),
    },
  });

  if (!invoice) return null;

  const hasLineTaxes = invoice.lines.some((line) => line.taxes.length > 0);
  const summaryColSpan = hasLineTaxes ? 4 : 3;
  const hasCredit = invoice.total_credit_amount !== "0.00";
  const hasPaid = invoice.total_paid_amount !== "0.00";
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
                    label: "Invoices",
                    href: "/invoices",
                  },
                  { type: "page", label: invoice.number || "" },
                ]}
              />
            </AppHeaderContent>
            <AppHeaderActions>
              <div className="flex items-center gap-2 text-sm">
                <SearchCommand />
                {invoice.status === "draft" && (
                  <Button type="button" variant="outline" size="sm" asChild>
                    <Link to="/invoices/$id/edit" params={{ id: invoice.id }}>
                      <PencilIcon />
                      Edit
                    </Link>
                  </Button>
                )}
                {invoice.status === "draft" && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      finalizeInvoice.mutateAsync({ id: invoice.id })
                    }
                    disabled={finalizeInvoice.isPending}
                  >
                    {finalizeInvoice.isPending ? <Spinner /> : <CheckIcon />}
                    <span>Finalize</span>
                  </Button>
                )}
                <InvoiceDropdown
                  invoice={invoice}
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
                </InvoiceDropdown>
              </div>
            </AppHeaderActions>
          </AppHeader>
          <main className="flex min-h-[calc(100svh_-_56px)]">
            <SectionGroup className="w-full flex-1">
              <Section>
                <SectionHeader>
                  <div className="flex items-center gap-2">
                    <SectionTitle>{invoice.number}</SectionTitle>
                    <InvoiceBadge status={invoice.status} />
                    {invoice.previous_revision_id && (
                      <Badge variant="secondary">Corrective</Badge>
                    )}
                  </div>
                  <SectionDescription>
                    <span>Billed to </span>
                    <Link
                      to="/customers/$id"
                      params={{ id: invoice.customer.id }}
                    >
                      <span className="text-primary underline-offset-4 hover:underline">
                        {invoice.customer.name}
                      </span>
                    </Link>
                    <span> - </span>
                    <span>
                      {formatAmount(invoice.total_amount, invoice.currency)}
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
                      <DataListLabel>Bill to</DataListLabel>
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
                              params={{ id: invoice.customer.id }}
                            >
                              {invoice.customer.name}
                            </Link>
                          </div>
                          {invoice.customer.email && (
                            <span className="text-muted-foreground">
                              {invoice.customer.email}
                            </span>
                          )}
                        </div>
                      </DataListValue>
                    </DataListItem>

                    <DataListItem>
                      <DataListLabel>Billing address</DataListLabel>
                      <DataListValue>
                        <AddressView address={invoice.customer.address} />
                      </DataListValue>
                    </DataListItem>
                    {invoice?.shipping && (
                      <DataListItem>
                        <DataListLabel>Ship to</DataListLabel>
                        <DataListValue>
                          <div className="flex flex-col gap-1">
                            {invoice.shipping?.name && (
                              <span>{invoice.shipping.name}</span>
                            )}
                            {invoice.shipping?.phone && (
                              <span>{invoice.shipping.phone}</span>
                            )}
                            <AddressView
                              address={invoice.shipping?.address || undefined}
                            />
                          </div>
                        </DataListValue>
                      </DataListItem>
                    )}
                  </DataList>
                  <DataList orientation="vertical" size="sm" className="gap-4">
                    <DataListItem>
                      <DataListLabel>Number</DataListLabel>
                      <DataListValue>{invoice.number || "-"}</DataListValue>
                    </DataListItem>
                    <DataListItem>
                      <DataListLabel>Currency</DataListLabel>
                      <DataListValue>{invoice.currency}</DataListValue>
                    </DataListItem>
                    <DataListItem>
                      <DataListLabel>Tax behavior</DataListLabel>
                      <DataListValue>
                        {formatEnum(invoice.tax_behavior)}
                      </DataListValue>
                    </DataListItem>
                    <DataListItem>
                      <DataListLabel>Due date</DataListLabel>
                      <DataListValue>
                        {formatDate(
                          invoice.due_date
                            ? invoice.due_date
                            : addDays(new Date(), invoice.net_payment_term),
                        )}
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
                    {invoice.lines.map((line) => (
                      <Fragment key={line.id}>
                        <TableRow>
                          <TableCell>{line.description}</TableCell>
                          <TableCell className="text-right">
                            {line.quantity}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatAmount(line.unit_amount, invoice.currency)}
                          </TableCell>
                          {hasLineTaxes &&
                            (line.taxes.length > 0 ? (
                              <TableCell className="text-right">
                                {formatPercentage(line.total_tax_rate)}
                              </TableCell>
                            ) : (
                              <TableCell />
                            ))}
                          <TableCell className="text-right">
                            {formatAmount(line.amount, invoice.currency)}
                          </TableCell>
                          <TableCell>
                            <div className="flex justify-end">
                              <InvoiceLineDropdown
                                invoice={invoice}
                                line={line}
                              >
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  className="data-[state=open]:bg-accent size-7"
                                >
                                  <MoreHorizontalIcon />
                                </Button>
                              </InvoiceLineDropdown>
                            </div>
                          </TableCell>
                        </TableRow>
                        {line.discounts.map((discount) => (
                          <TableRow key={discount.coupon_id}>
                            <TableCell className="pl-8">
                              {discount.name}
                            </TableCell>
                            <TableCell />
                            {hasLineTaxes && <TableCell />}
                            <TableCell />
                            <TableCell className="text-right text-emerald-400">
                              -{formatAmount(discount.amount, invoice.currency)}
                            </TableCell>
                            <TableCell />
                          </TableRow>
                        ))}
                      </Fragment>
                    ))}
                    {invoice.lines.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5 + (hasLineTaxes ? 1 : 0)}>
                          <Empty>
                            <EmptyHeader>
                              <EmptyTitle>
                                {invoice.status === "draft"
                                  ? "No lines added yet"
                                  : "No lines"}
                              </EmptyTitle>
                              <EmptyDescription>
                                {invoice.status === "draft"
                                  ? "Add lines to your invoice to see them here."
                                  : "This invoice has no lines."}
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
                      <TableCell className="text-right font-medium">
                        {formatAmount(
                          invoice.subtotal_amount,
                          invoice.currency,
                        )}
                      </TableCell>
                      <TableCell className="p-0" />
                    </TableRow>
                    {invoice.discounts.map((discount) => (
                      <TableRow key={discount.coupon_id}>
                        <TableCell
                          colSpan={summaryColSpan}
                          className="text-right font-medium"
                        >
                          {discount.name}
                        </TableCell>
                        <TableCell
                          className="font-medium text-emerald-400"
                          align="right"
                        >
                          -{formatAmount(discount.amount, invoice.currency)}
                        </TableCell>
                        <TableCell className="p-0" />
                      </TableRow>
                    ))}
                    {invoice?.shipping && (
                      <TableRow>
                        <TableCell
                          colSpan={summaryColSpan}
                          className="text-right font-medium"
                        >
                          <span>Shipping fee</span>
                        </TableCell>
                        <TableCell className="font-medium" align="right">
                          {formatAmount(
                            invoice.shipping_amount,
                            invoice.currency,
                          )}
                        </TableCell>
                        <TableCell className="p-0" />
                      </TableRow>
                    )}
                    <TableRow>
                      <TableCell
                        colSpan={summaryColSpan}
                        className="text-right font-medium"
                      >
                        Total excluding tax
                      </TableCell>
                      <TableCell className="font-medium" align="right">
                        {formatAmount(
                          invoice.total_excluding_tax_amount,
                          invoice.currency,
                        )}
                      </TableCell>
                      <TableCell className="p-0" />
                    </TableRow>
                    {invoice.total_taxes.map((tax) => (
                      <TableRow key={tax.tax_rate_id}>
                        <TableCell
                          colSpan={summaryColSpan}
                          className="text-right font-medium"
                        >
                          {tax.name} {formatPercentage(tax.percentage)}
                        </TableCell>
                        <TableCell className="font-medium" align="right">
                          {formatAmount(tax.amount, invoice.currency)}
                        </TableCell>
                        <TableCell className="p-0" />
                      </TableRow>
                    ))}
                    <TableRow>
                      <TableCell
                        colSpan={summaryColSpan}
                        className="text-right font-medium"
                      >
                        Total
                      </TableCell>
                      <TableCell className="font-medium" align="right">
                        {formatAmount(invoice.total_amount, invoice.currency)}
                      </TableCell>
                      <TableCell className="p-0" />
                    </TableRow>

                    {invoice.status !== InvoiceStatusEnum.draft && (
                      <>
                        <TableRow className="border-t!">
                          <TableCell
                            colSpan={summaryColSpan}
                            className="text-right font-medium"
                          >
                            Total paid
                          </TableCell>
                          <TableCell
                            className={cn(
                              "font-medium",
                              hasPaid && "text-emerald-400",
                            )}
                            align="right"
                          >
                            {hasPaid && "-"}
                            {formatAmount(
                              invoice.total_paid_amount,
                              invoice.currency,
                            )}
                          </TableCell>
                          <TableCell className="p-0" />
                        </TableRow>
                        {hasCredit && (
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
                                invoice.total_credit_amount,
                                invoice.currency,
                              )}
                            </TableCell>
                            <TableCell className="p-0" />
                          </TableRow>
                        )}
                        <TableRow>
                          <TableCell
                            colSpan={summaryColSpan}
                            className="text-right font-medium"
                          >
                            Outstanding
                          </TableCell>
                          <TableCell className="font-medium" align="right">
                            {formatAmount(
                              invoice.outstanding_amount,
                              invoice.currency,
                            )}
                          </TableCell>
                          <TableCell className="p-0" />
                        </TableRow>
                      </>
                    )}
                  </TableFooter>
                </Table>
              </Section>
              <Section>
                <SectionHeader>
                  <SectionTitle>Documents</SectionTitle>
                </SectionHeader>
                {invoice.documents.length > 0 ? (
                  <div className="overflow-hidden rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Language</TableHead>
                          <TableHead>Audience</TableHead>
                          <TableHead className="sr-only">Download</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {invoice.documents.map((document) => (
                          <TableRow key={document.id}>
                            <TableCell>
                              {formatLanguage(document.language)}
                            </TableCell>
                            <TableCell>
                              <div className="flex flex-wrap gap-2">
                                {document.audience.map((audience) => (
                                  <Badge key={audience} variant="secondary">
                                    {formatEnum(audience)}
                                  </Badge>
                                ))}
                              </div>
                            </TableCell>
                            <TableCell className="text-right">
                              <Button
                                variant="ghost"
                                size="icon"
                                disabled={!document.url || isDownloading}
                                onClick={() =>
                                  download(
                                    document.url,
                                    `${invoice.number}-${document.language}.pdf`,
                                  )
                                }
                              >
                                <DownloadIcon />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <Empty className="border">
                    <EmptyHeader>
                      <EmptyTitle>No documents available</EmptyTitle>
                      <EmptyDescription>
                        Documents will appear here once configured.
                      </EmptyDescription>
                    </EmptyHeader>
                  </Empty>
                )}
              </Section>
              <Section>
                <SectionHeader>
                  <SectionTitle>Payments</SectionTitle>
                </SectionHeader>
                {payments?.data && payments.data.count > 0 ? (
                  <div className="overflow-hidden rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Amount</TableHead>
                          <TableHead>Received at</TableHead>
                          <TableHead>Transaction ID</TableHead>
                          <TableHead>Description</TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {payments?.data?.results.map((payment) => (
                          <TableRow key={payment.id}>
                            <TableCell>
                              {formatAmount(payment.amount, payment.currency)}
                            </TableCell>
                            <TableCell>
                              {formatDatetime(payment.received_at)}
                            </TableCell>
                            <TableCell>
                              {payment.transaction_id || "-"}
                            </TableCell>
                            <TableCell>{payment.description || "-"}</TableCell>
                            <TableCell>
                              <PaymentBadge status={payment.status} />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <Empty className="border">
                    <EmptyHeader>
                      <EmptyTitle>No payments recorded</EmptyTitle>
                      <EmptyDescription>
                        Payment will appear here when recorded against this
                        invoice.
                      </EmptyDescription>
                    </EmptyHeader>
                    {invoice.status === InvoiceStatusEnum.open && (
                      <EmptyContent>
                        <Button
                          size="sm"
                          onClick={() =>
                            pushModal("PaymentRecordDialog", { invoice })
                          }
                        >
                          <CreditCardIcon />
                          Record payment
                        </Button>
                      </EmptyContent>
                    )}
                  </Empty>
                )}
              </Section>
              <Section>
                <SectionHeader>
                  <SectionTitle>Credit notes</SectionTitle>
                </SectionHeader>
                <DataTableContainer>
                  <DataTable table={creditNotesTable}>
                    <Empty>
                      <EmptyHeader>
                        <EmptyTitle>No credit notes issued</EmptyTitle>
                        <EmptyDescription>
                          Credit notes applied to this invoice will appear here.
                        </EmptyDescription>
                      </EmptyHeader>
                    </Empty>
                  </DataTable>
                </DataTableContainer>
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
                        invoiceId: invoice.id,
                        id: commentId,
                      })
                    }
                  />
                  <CommentsForm
                    isCreating={createComment.isPending}
                    onCreate={(data) =>
                      createComment.mutateAsync({ invoiceId: invoice.id, data })
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
                    <DataListValue>{invoice.id}</DataListValue>
                  </DataListItem>
                  {invoice.issue_date && (
                    <DataListItem>
                      <DataListLabel>Issue date</DataListLabel>
                      <DataListValue>
                        {formatDate(invoice.issue_date)}
                      </DataListValue>
                    </DataListItem>
                  )}
                  <DataListItem>
                    <DataListLabel>Created</DataListLabel>
                    <DataListValue>
                      {formatDatetime(invoice.created_at)}
                    </DataListValue>
                  </DataListItem>
                  {invoice.opened_at && (
                    <DataListItem>
                      <DataListLabel>Opened</DataListLabel>
                      <DataListValue>
                        {formatDatetime(invoice.opened_at)}
                      </DataListValue>
                    </DataListItem>
                  )}
                  {invoice.paid_at && (
                    <DataListItem>
                      <DataListLabel>Paid</DataListLabel>
                      <DataListValue>
                        {formatDatetime(invoice.paid_at)}
                      </DataListValue>
                    </DataListItem>
                  )}
                  {invoice.voided_at && (
                    <DataListItem>
                      <DataListLabel>Voided</DataListLabel>
                      <DataListValue>
                        {formatDatetime(invoice.voided_at)}
                      </DataListValue>
                    </DataListItem>
                  )}
                  <DataListItem>
                    <DataListLabel>Last updated</DataListLabel>
                    <DataListValue>
                      {invoice.updated_at
                        ? formatDatetime(invoice.updated_at)
                        : "-"}
                    </DataListValue>
                  </DataListItem>
                </DataList>
                {numberingSystem && (
                  <Fragment>
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
                  </Fragment>
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
                      {formatEnum(invoice.delivery_method)}
                    </DataListValue>
                  </DataListItem>
                  <DataListItem>
                    <DataListLabel>Recipients</DataListLabel>
                    <DataListValue>
                      {invoice.recipients.length > 0 ? (
                        <ul className="space-y-0.5">
                          {invoice.recipients.map((recipient) => (
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
                  data={invoice.metadata as Record<string, string>}
                  onSubmit={(metadata) => {
                    void updateInvoice.mutateAsync({
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
