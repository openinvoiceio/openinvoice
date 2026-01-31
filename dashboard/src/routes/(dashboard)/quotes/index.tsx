import {
  getQuotesListQueryKey,
  quotesList,
  useQuotesList,
} from "@/api/endpoints/quotes/quotes";
import { CurrencyEnum, QuoteStatusEnum, type Quote } from "@/api/models";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { AppSidebar } from "@/components/app-sidebar";
import {
  DataTable,
  DataTableContainer,
  DataTableFooter,
} from "@/components/data-table/data-table";
import { DataTablePagination } from "@/components/data-table/data-table-pagination";
import { DataTableSortList } from "@/components/data-table/data-table-sort-list";
import {
  DataTableFilterList,
  DataTableToolbar,
} from "@/components/data-table/data-table-toolbar";
import { DataTableViewOptions } from "@/components/data-table/data-table-view-options.tsx";
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { pushModal } from "@/components/push-modals.tsx";
import { columns } from "@/components/quote-table";
import { SearchCommand } from "@/components/search-command.tsx";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty.tsx";
import { Input } from "@/components/ui/input.tsx";
import {
  MetricCardButton,
  MetricCardGroup,
  MetricCardHeader,
  MetricCardTitle,
  MetricCardValue,
} from "@/components/ui/metric-card";
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
import { useDataTable } from "@/hooks/use-data-table";
import { useDebounce } from "@/hooks/use-debounce.ts";
import { getInitialColumnVisibility } from "@/lib/data-table.ts";
import { formatEnum } from "@/lib/formatters.ts";
import { getSortingStateParser } from "@/lib/parsers";
import { useQueries } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import type { ColumnSort } from "@tanstack/react-table";
import { addDays, formatISO } from "date-fns";
import { ListFilterIcon, PlusIcon } from "lucide-react";
import {
  parseAsArrayOf,
  parseAsFloat,
  parseAsInteger,
  parseAsIsoDateTime,
  parseAsString,
  parseAsStringEnum,
  useQueryStates,
} from "nuqs";

const searchParams = {
  page: parseAsInteger.withDefault(1),
  perPage: parseAsInteger.withDefault(20),
  sort: getSortingStateParser<Quote>().withDefault([
    { id: "created_at", desc: true },
  ]),
  search: parseAsString.withDefault(""),
  customer: parseAsString,
  issue_date: parseAsArrayOf(parseAsIsoDateTime).withDefault([]),
  status: parseAsArrayOf(
    parseAsStringEnum([...Object.values(QuoteStatusEnum), "all"]),
  ).withDefault(["all"]),
  currency: parseAsArrayOf(
    parseAsStringEnum([...Object.values(CurrencyEnum), "all"]),
  ).withDefault(["all"]),
  total_amount: parseAsArrayOf(parseAsFloat).withDefault([]),
  subtotal_amount: parseAsArrayOf(parseAsFloat).withDefault([]),
  created_at: parseAsArrayOf(parseAsIsoDateTime).withDefault([]),
  lines: parseAsString,
};

export const Route = createFileRoute("/(dashboard)/quotes/")({
  component: RouteComponent,
});

function RouteComponent() {
  const { auth, account } = Route.useRouteContext();
  const [
    {
      page,
      perPage,
      sort,
      search,
      customer,
      issue_date,
      status,
      currency,
      total_amount,
      subtotal_amount,
      created_at,
      lines: product_id,
    },
    setQueryState,
  ] = useQueryStates(searchParams);

  const debouncedSearch = useDebounce(search, 400);
  const hasFilters =
    (search?.trim()?.length ?? 0) > 0 ||
    (customer?.trim()?.length ?? 0) > 0 ||
    created_at.length === 2 ||
    status.join() !== "all" ||
    currency.join() !== "all" ||
    total_amount.length === 2 ||
    subtotal_amount.length === 2 ||
    issue_date.length === 2 ||
    (product_id?.trim()?.length ?? 0) > 0;

  const { data } = useQuotesList({
    page,
    page_size: perPage,
    ordering: sort
      .map((s: ColumnSort) => `${s.desc ? "-" : ""}${s.id}`)
      .join(","),
    ...(search && { search: debouncedSearch }),
    ...(customer && { customer_id: customer }),
    ...(issue_date.length == 2 && {
      issue_date_after: formatISO(new Date(issue_date[0])),
      issue_date_before: formatISO(addDays(new Date(issue_date[1]), 1)),
    }),
    ...(status.join() !== "all" && { status: [status.join(",")] }),
    ...(currency.join() !== "all" && { currency: [currency.join(",")] }),
    ...(total_amount.length == 2 && {
      total_amount_min: total_amount[0],
      total_amount_max: total_amount[1],
    }),
    ...(subtotal_amount.length == 2 && {
      subtotal_amount_min: subtotal_amount[0],
      subtotal_amount_max: subtotal_amount[1],
    }),
    ...(created_at.length == 2 && {
      created_at_after: formatISO(new Date(created_at[0])),
      created_at_before: formatISO(addDays(new Date(created_at[1]), 1)),
    }),
    ...(product_id && { product_id }),
  });

  const metrics = [
    { value: "all" as const, label: "All" },
    ...Object.values(QuoteStatusEnum).map((value) => ({
      value,
      label: formatEnum(value),
    })),
  ] as const;

  const counters = useQueries({
    queries: metrics.map(({ value }) => ({
      queryKey: getQuotesListQueryKey({
        ...(value === "all" ? {} : { status: [value] }),
      }),
      queryFn: () =>
        quotesList({
          ...(value === "all" ? {} : { status: [value] }),
        }),
      staleTime: 30_000,
    })),
  });

  const { table } = useDataTable({
    data: data?.results || [],
    columns,
    pageCount: data?.count ? Math.ceil(data.count / perPage) : 0,
    initialState: {
      columnVisibility: getInitialColumnVisibility(columns, [
        "select",
        "number",
        "customer",
        "issue_date",
        "total_amount",
        "status",
        "actions",
      ]),
    },
  });

  return (
    <SidebarProvider>
      <AppSidebar user={auth.user} account={account} />
      <SidebarInset>
        <div>
          <AppHeader>
            <AppHeaderContent>
              <SidebarTrigger />
              <NavBreadcrumb items={[{ type: "page", label: "Quotes" }]} />
            </AppHeaderContent>
            <AppHeaderActions>
              <div className="flex items-center gap-2 text-sm">
                <SearchCommand />
                <Button
                  type="button"
                  size="sm"
                  onClick={() =>
                    pushModal("QuoteCreateDialog", {
                      defaultCustomer: undefined,
                    })
                  }
                >
                  <PlusIcon />
                  Add quote
                </Button>
              </div>
            </AppHeaderActions>
          </AppHeader>
          <main className="w-full flex-1">
            <SectionGroup>
              <Section>
                <SectionHeader>
                  <SectionTitle>Quotes</SectionTitle>
                  <SectionDescription>
                    Manage and review your quotes.
                  </SectionDescription>
                </SectionHeader>
                <div className="grid gap-4">
                  <MetricCardGroup className="flex">
                    {metrics.map((item, index) => {
                      const query = counters[index];
                      return (
                        <MetricCardButton
                          key={item.value}
                          selected={status.includes(item.value)}
                          onClick={async () => {
                            const column = table.getColumn("status");
                            if (!column) return;
                            column.setFilterValue(
                              item.value === "all" ? undefined : [item.value],
                            );
                          }}
                        >
                          <MetricCardHeader className="flex items-center justify-between">
                            <MetricCardTitle>{item.label}</MetricCardTitle>
                            <ListFilterIcon className="size-4" />
                          </MetricCardHeader>
                          <MetricCardValue>
                            {query.isLoading ? "…" : query.data?.count}
                          </MetricCardValue>
                        </MetricCardButton>
                      );
                    })}
                  </MetricCardGroup>
                  <DataTableContainer>
                    <DataTableToolbar table={table}>
                      <DataTableFilterList table={table}>
                        <Input
                          placeholder="Search..."
                          value={search}
                          onChange={(event) =>
                            setQueryState({ search: event.target.value })
                          }
                          className="h-8 w-40 lg:w-56"
                        />
                      </DataTableFilterList>
                      <DataTableSortList table={table} />
                      <DataTableViewOptions table={table} />
                    </DataTableToolbar>
                    <DataTable table={table}>
                      {!hasFilters ? (
                        <Empty>
                          <EmptyHeader>
                            <EmptyTitle>Add your first quote</EmptyTitle>
                            <EmptyDescription>
                              Quotes help you provide customers with pricing
                              breakdowns before invoicing.
                            </EmptyDescription>
                          </EmptyHeader>
                          <EmptyContent>
                            <Button
                              size="sm"
                              onClick={() =>
                                pushModal("QuoteCreateDialog", {
                                  defaultCustomer: undefined,
                                })
                              }
                            >
                              <PlusIcon />
                              Add quote
                            </Button>
                          </EmptyContent>
                        </Empty>
                      ) : (
                        <Empty>
                          <EmptyHeader>
                            <EmptyTitle>No results found</EmptyTitle>
                            <EmptyDescription>
                              Try adjusting your filters to find quotes you're
                              looking for.
                            </EmptyDescription>
                          </EmptyHeader>
                        </Empty>
                      )}
                    </DataTable>
                    <DataTableFooter>
                      <DataTablePagination table={table} />
                    </DataTableFooter>
                  </DataTableContainer>
                </div>
              </Section>
            </SectionGroup>
          </main>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
