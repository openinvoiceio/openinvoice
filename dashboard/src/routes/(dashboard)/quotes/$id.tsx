import { useFilesRetrieve } from "@/api/endpoints/files/files";
import { useNumberingSystemsRetrieve } from "@/api/endpoints/numbering-systems/numbering-systems.ts";
import {
  getPreviewQuoteQueryKey,
  getQuotesListQueryKey,
  getQuotesRetrieveQueryKey,
  useAcceptQuote,
  useFinalizeQuote,
  useQuotesRetrieve,
  useUpdateQuote,
} from "@/api/endpoints/quotes/quotes";
import { QuoteStatusEnum } from "@/api/models";
import { AddressView } from "@/components/address-view";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { NumberingSystemView } from "@/components/numbering-system-view.tsx";
import { QuoteBadge } from "@/components/quote-badge";
import { QuoteDropdown } from "@/components/quote-dropdown";
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
} from "@/components/ui/empty";
import { Metadata } from "@/components/ui/metadata";
import {
  Section,
  SectionDescription,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Spinner } from "@/components/ui/spinner.tsx";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getErrorSummary } from "@/lib/api/errors";
import {
  formatAmount,
  formatDate,
  formatDatetime,
  formatEnum,
  formatPercentage,
} from "@/lib/formatters";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowRight,
  BracesIcon,
  CheckIcon,
  InfoIcon,
  MoreHorizontalIcon,
  UserIcon,
} from "lucide-react";
import { Fragment } from "react";
import { toast } from "sonner";

export const Route = createFileRoute("/(dashboard)/quotes/$id")({
  component: RouteComponent,
});

function RouteComponent() {
  const { id } = Route.useParams();
  const { queryClient } = Route.useRouteContext();
  const { data: quote } = useQuotesRetrieve(id);
  const { data: numberingSystem } = useNumberingSystemsRetrieve(
    quote?.numbering_system_id || "",
    { query: { enabled: !!quote?.numbering_system_id } },
  );
  const { data: logo } = useFilesRetrieve(quote?.customer.logo_id || "", {
    query: { enabled: !!quote?.customer.logo_id },
  });

  const updateQuote = useUpdateQuote({
    mutation: {
      onSuccess: async () => {
        await invalidateQuote();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  async function invalidateQuote() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: getQuotesListQueryKey() }),
      queryClient.invalidateQueries({
        queryKey: getQuotesRetrieveQueryKey(id),
      }),
      queryClient.invalidateQueries({ queryKey: getPreviewQuoteQueryKey(id) }),
    ]);
  }

  const finalizeQuote = useFinalizeQuote({
    mutation: {
      onSuccess: async () => {
        await invalidateQuote();
        toast.success("Quote finalized");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  const acceptQuote = useAcceptQuote({
    mutation: {
      onSuccess: async () => {
        await invalidateQuote();
        toast.success("Quote accepted");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  if (!quote) return null;

  const hasLineTaxes = quote.lines.some((line) => line.taxes.length > 0);
  const summaryColSpan = hasLineTaxes ? 4 : 3;

  const customFields = Object.entries(
    quote.custom_fields as Record<string, string>,
  );

  return (
    <div>
      <AppHeader>
        <AppHeaderContent>
          <SidebarTrigger />
          <NavBreadcrumb
            items={[
              { type: "link", label: "Quotes", href: "/quotes" },
              { type: "page", label: quote.number || quote.id },
            ]}
          />
        </AppHeaderContent>
        <AppHeaderActions>
          <div className="flex items-center gap-2 text-sm">
            <SearchCommand />
            {quote.status === QuoteStatusEnum.draft ? (
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={finalizeQuote.isPending}
                onClick={() => finalizeQuote.mutate({ quoteId: id })}
              >
                {finalizeQuote.isPending ? <Spinner /> : <CheckIcon />}
                Finalize
              </Button>
            ) : null}
            {quote.status === QuoteStatusEnum.open ? (
              <Button
                type="button"
                size="sm"
                onClick={() => acceptQuote.mutate({ quoteId: id })}
                disabled={acceptQuote.isPending}
              >
                {acceptQuote.isPending ? <Spinner /> : <ArrowRight />}
                Accept
              </Button>
            ) : null}
            <QuoteDropdown
              quote={quote}
              actions={{ finalize: false, accept: false }}
            >
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="data-[state=open]:bg-accent size-8"
              >
                <MoreHorizontalIcon />
              </Button>
            </QuoteDropdown>
          </div>
        </AppHeaderActions>
      </AppHeader>

      <main className="flex min-h-[calc(100svh_-_56px)]">
        <SectionGroup className="w-full flex-1">
          <Section>
            <SectionHeader>
              <div className="flex items-center gap-2">
                <SectionTitle>{quote.number || quote.id}</SectionTitle>
                <QuoteBadge status={quote.status} />
              </div>
              <SectionDescription>
                <span>Quoted to </span>
                <Link to="/customers/$id" params={{ id: quote.customer.id }}>
                  <span className="text-primary underline-offset-4 hover:underline">
                    {quote.customer.name}
                  </span>
                </Link>
                <span> - </span>
                <span>{formatAmount(quote.total_amount, quote.currency)}</span>
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
                  <DataListLabel>Quoted to</DataListLabel>
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
                          params={{ id: quote.customer.id }}
                        >
                          {quote.customer.name}
                        </Link>
                      </div>
                      {quote.customer.email && (
                        <span className="text-muted-foreground">
                          {quote.customer.email}
                        </span>
                      )}
                    </div>
                  </DataListValue>
                </DataListItem>

                <DataListItem>
                  <DataListLabel>Billing address</DataListLabel>
                  <DataListValue>
                    <AddressView address={quote.customer.billing_address} />
                  </DataListValue>
                </DataListItem>
              </DataList>
              <DataList orientation="vertical" size="sm" className="gap-4">
                <DataListItem>
                  <DataListLabel>Number</DataListLabel>
                  <DataListValue>{quote.number || "-"}</DataListValue>
                </DataListItem>
                <DataListItem>
                  <DataListLabel>Currency</DataListLabel>
                  <DataListValue>{quote.currency}</DataListValue>
                </DataListItem>
                <DataListItem>
                  {/*<DataListLabel>Due date</DataListLabel>*/}
                  {/*<DataListValue>*/}
                  {/*  {formatDate(*/}
                  {/*      invoice.due_date*/}
                  {/*          ? invoice.due_date*/}
                  {/*          : addDays(new Date(), invoice.net_payment_term),*/}
                  {/*  )}*/}
                  {/*</DataListValue>*/}
                </DataListItem>
              </DataList>
            </div>

            <Table className="mt-2">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-full">Description</TableHead>
                  <TableHead className="text-right">Quantity</TableHead>
                  <TableHead className="min-w-40 text-right">Price</TableHead>
                  {hasLineTaxes && (
                    <TableHead className="min-w-40 text-right">Tax</TableHead>
                  )}
                  <TableHead className="min-w-40 text-right">Amount</TableHead>
                  <TableHead className="w-10">
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {quote.lines.map((line) => (
                  <Fragment key={line.id}>
                    <TableRow>
                      <TableCell>{line.description}</TableCell>
                      <TableCell className="text-right">
                        {line.quantity}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatAmount(line.unit_amount, quote.currency)}
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
                        {formatAmount(line.amount, quote.currency)}
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
                    {line.discounts.map((discount) => (
                      <TableRow key={discount.id}>
                        <TableCell className="flex gap-2 pl-8">
                          <span>{discount.coupon.name}</span>
                          <span className="text-muted-foreground">
                            {discount.coupon.amount
                              ? formatAmount(
                                  discount.coupon.amount,
                                  discount.coupon.currency,
                                )
                              : formatPercentage(
                                  discount.coupon.percentage as string,
                                )}{" "}
                            off
                          </span>
                        </TableCell>
                        <TableCell />
                        {hasLineTaxes && <TableCell />}
                        <TableCell />
                        <TableCell className="text-right text-emerald-400">
                          -{formatAmount(discount.amount, quote.currency)}
                        </TableCell>
                        <TableCell />
                      </TableRow>
                    ))}
                  </Fragment>
                ))}
                {quote.lines.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5 + (hasLineTaxes ? 1 : 0)}>
                      <Empty>
                        <EmptyHeader>
                          <EmptyTitle>
                            {quote.status === QuoteStatusEnum.draft
                              ? "No lines added yet"
                              : "No lines"}
                          </EmptyTitle>
                          <EmptyDescription>
                            {quote.status === QuoteStatusEnum.draft
                              ? "Add lines to your quote to see them here."
                              : "This quote has no lines."}
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
                    {formatAmount(quote.subtotal_amount, quote.currency)}
                  </TableCell>
                  <TableCell className="p-0" />
                </TableRow>
                {/*{quote.discount_breakdown.map((item) => (*/}
                {/*    <TableRow key={item.coupon_id}>*/}
                {/*      <TableCell*/}
                {/*          colSpan={summaryColSpan}*/}
                {/*          className="text-right font-medium"*/}
                {/*      >*/}
                {/*        {item.name}*/}
                {/*      </TableCell>*/}
                {/*      <TableCell*/}
                {/*          className="font-medium text-emerald-400"*/}
                {/*          align="right"*/}
                {/*      >*/}
                {/*        -{formatAmount(item.amount, quote.currency)}*/}
                {/*      </TableCell>*/}
                {/*      <TableCell className="p-0" />*/}
                {/*    </TableRow>*/}
                {/*))}*/}
                <TableRow>
                  <TableCell
                    colSpan={summaryColSpan}
                    className="text-right font-medium"
                  >
                    Total excluding tax
                  </TableCell>
                  <TableCell className="font-medium" align="right">
                    {formatAmount(
                      quote.total_amount_excluding_tax,
                      quote.currency,
                    )}
                  </TableCell>
                  <TableCell className="p-0" />
                </TableRow>
                {/*{quote.tax_breakdown.map((item) => (*/}
                {/*    <TableRow key={item.name}>*/}
                {/*      <TableCell*/}
                {/*          colSpan={summaryColSpan}*/}
                {/*          className="text-right font-medium"*/}
                {/*      >*/}
                {/*        {item.name} {formatPercentage(item.rate)}*/}
                {/*      </TableCell>*/}
                {/*      <TableCell className="font-medium" align="right">*/}
                {/*        {formatAmount(item.amount, quote.currency)}*/}
                {/*      </TableCell>*/}
                {/*      <TableCell className="p-0" />*/}
                {/*    </TableRow>*/}
                {/*))}*/}
                <TableRow>
                  <TableCell
                    colSpan={summaryColSpan}
                    className="text-right font-medium"
                  >
                    Total
                  </TableCell>
                  <TableCell className="font-medium" align="right">
                    {formatAmount(quote.total_amount, quote.currency)}
                  </TableCell>
                  <TableCell className="p-0" />
                </TableRow>
              </TableFooter>
            </Table>
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
            <DataList orientation="vertical" className="gap-3 px-4" size="sm">
              <DataListItem>
                <DataListLabel>ID</DataListLabel>
                <DataListValue>{quote.id}</DataListValue>
              </DataListItem>
              {quote.issue_date && (
                <DataListItem>
                  <DataListLabel>Issue date</DataListLabel>
                  <DataListValue>{formatDate(quote.issue_date)}</DataListValue>
                </DataListItem>
              )}
              <DataListItem>
                <DataListLabel>Created</DataListLabel>
                <DataListValue>
                  {formatDatetime(quote.created_at)}
                </DataListValue>
              </DataListItem>
              {quote.opened_at && (
                <DataListItem>
                  <DataListLabel>Opened</DataListLabel>
                  <DataListValue>
                    {formatDatetime(quote.opened_at)}
                  </DataListValue>
                </DataListItem>
              )}
              {quote.accepted_at && (
                <DataListItem>
                  <DataListLabel>Accepted</DataListLabel>
                  <DataListValue>
                    {formatDatetime(quote.accepted_at)}
                  </DataListValue>
                </DataListItem>
              )}
              {quote.canceled_at && (
                <DataListItem>
                  <DataListLabel>Canceled</DataListLabel>
                  <DataListValue>
                    {formatDatetime(quote.canceled_at)}
                  </DataListValue>
                </DataListItem>
              )}
              <DataListItem>
                <DataListLabel>Last updated</DataListLabel>
                <DataListValue>
                  {quote.updated_at ? formatDatetime(quote.updated_at) : "-"}
                </DataListValue>
              </DataListItem>
              <DataListItem>
                <DataListLabel>Currency</DataListLabel>
                <DataListValue>{quote.currency}</DataListValue>
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
                      <NumberingSystemView numberingSystem={numberingSystem} />
                    </DataListValue>
                  </DataListItem>
                </DataList>
              </>
            )}
            <DataSidebarSeparator />
            <DataList orientation="vertical" className="gap-3 px-4" size="sm">
              <DataListItem>
                <DataListLabel>Delivery method</DataListLabel>
                <DataListValue>
                  {formatEnum(quote.delivery_method)}
                </DataListValue>
              </DataListItem>
              <DataListItem>
                <DataListLabel>Recipients</DataListLabel>
                <DataListValue>
                  {quote.recipients.length > 0 ? (
                    <ul className="space-y-0.5">
                      {quote.recipients.map((recipient) => (
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
            {customFields.length > 0 && (
              <>
                <DataSidebarSeparator />
                <DataList
                  orientation="vertical"
                  className="gap-3 px-4"
                  size="sm"
                >
                  {customFields.map(([label, value]) => (
                    <DataListItem key={label}>
                      <DataListLabel>{label}</DataListLabel>
                      <DataListValue>{value || "-"}</DataListValue>
                    </DataListItem>
                  ))}
                </DataList>
              </>
            )}
          </DataSidebarContent>
          <DataSidebarContent value="metadata">
            <DataSidebarTitle>Metadata</DataSidebarTitle>
            <Metadata
              className="my-1 px-4"
              data={quote.metadata as Record<string, string>}
              onSubmit={(metadata) => {
                void updateQuote.mutateAsync({ id, data: { metadata } });
              }}
              submitOnChange
            />
          </DataSidebarContent>
        </DataSidebar>
      </main>
    </div>
  );
}
