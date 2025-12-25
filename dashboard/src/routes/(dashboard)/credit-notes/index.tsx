import {
  creditNotesList,
  getCreditNotesListQueryKey,
  getCreditNotesRetrieveQueryKey,
  useCreateCreditNote,
  useCreditNotesList,
} from "@/api/endpoints/credit-notes/credit-notes";
import {
  CreditNoteStatusEnum,
  InvoiceStatusEnum,
  type CreditNote,
  type Invoice,
} from "@/api/models";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { columns } from "@/components/credit-note-table";
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
import { DataTableViewOptions } from "@/components/data-table/data-table-view-options";
import { InvoiceCombobox } from "@/components/invoice-combobox.tsx";
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { SearchCommand } from "@/components/search-command.tsx";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { Input } from "@/components/ui/input";
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
import { SidebarTrigger } from "@/components/ui/sidebar";
import { useDataTable } from "@/hooks/use-data-table";
import { useDebounce } from "@/hooks/use-debounce";
import { getInitialColumnVisibility } from "@/lib/data-table.ts";
import { formatEnum } from "@/lib/formatters.ts";
import { getSortingStateParser } from "@/lib/parsers";
import { useQueries, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { addDays, formatISO } from "date-fns";
import { ListFilterIcon, PlusIcon } from "lucide-react";
import {
  parseAsArrayOf,
  parseAsInteger,
  parseAsIsoDateTime,
  parseAsString,
  parseAsStringEnum,
  useQueryStates,
} from "nuqs";
import { toast } from "sonner";

const searchParams = {
  page: parseAsInteger.withDefault(1),
  perPage: parseAsInteger.withDefault(20),
  sort: getSortingStateParser<CreditNote>().withDefault([
    { id: "created_at", desc: true },
  ]),
  search: parseAsString.withDefault(""),
  invoice: parseAsString,
  status: parseAsArrayOf(
    parseAsStringEnum([...Object.values(CreditNoteStatusEnum), "all"]),
  ).withDefault(["all"]),
  issue_date: parseAsArrayOf(parseAsIsoDateTime).withDefault([]),
  created_at: parseAsArrayOf(parseAsIsoDateTime).withDefault([]),
};

const metrics = [
  { value: "all" as const, label: "All" },
  ...Object.values(CreditNoteStatusEnum).map((value) => ({
    value,
    label: formatEnum(value),
  })),
] as const;

export const Route = createFileRoute("/(dashboard)/credit-notes/")({
  component: RouteComponent,
});

function RouteComponent() {
  const queryClient = useQueryClient();
  const navigate = Route.useNavigate();
  const [
    { page, perPage, sort, search, invoice, status, issue_date, created_at },
    setQueryState,
  ] = useQueryStates(searchParams);
  const debouncedSearch = useDebounce(search, 400);

  const effectiveStatus = status.join() !== "all" ? status : undefined;

  const { data } = useCreditNotesList({
    page,
    page_size: perPage,
    ordering: sort.map((item) => `${item.desc ? "-" : ""}${item.id}`).join(","),
    ...(debouncedSearch && { search: debouncedSearch }),
    ...(invoice && { invoice_id: invoice }),
    ...(effectiveStatus && { status: [effectiveStatus.join(",")] }),
    ...(issue_date.length === 2 && {
      issue_date_after: formatISO(new Date(issue_date[0])),
      issue_date_before: formatISO(addDays(new Date(issue_date[1]), 1)),
    }),
    ...(created_at.length === 2 && {
      created_at_after: formatISO(new Date(created_at[0])),
      created_at_before: formatISO(addDays(new Date(created_at[1]), 1)),
    }),
  });

  const counters = useQueries({
    queries: metrics.map(({ value }) => ({
      queryKey: getCreditNotesListQueryKey(
        value === "all" ? undefined : { status: [value] },
      ),
      queryFn: () =>
        creditNotesList(value === "all" ? undefined : { status: [value] }),
      staleTime: 30_000,
    })),
  });

  const { table } = useDataTable({
    data: data?.results ?? [],
    columns,
    pageCount: data?.count ? Math.ceil(data.count / perPage) : 0,
    initialState: {
      columnVisibility: getInitialColumnVisibility(columns, [
        "select",
        "number",
        "customer",
        "invoice",
        "total_amount",
        "status",
        "actions",
      ]),
    },
  });

  const hasFilters =
    Boolean(search?.trim()) ||
    Boolean(invoice?.trim()) ||
    (effectiveStatus && effectiveStatus.join()) ||
    issue_date.length === 2 ||
    created_at.length === 2;

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
        navigate({
          to: "/credit-notes/$id/edit",
          params: { id: creditNote.id },
        });
      },
    },
  });

  async function onInvoiceSelect(invoice: Invoice | null) {
    if (isPending || !invoice) return;
    await mutateAsync({
      data: {
        invoice_id: invoice.id,
      },
    });
  }

  return (
    <div className="flex min-h-full flex-col">
      <AppHeader>
        <SidebarTrigger className="mr-2" />
        <AppHeaderContent>
          <NavBreadcrumb items={[{ type: "page", label: "Credit notes" }]} />
        </AppHeaderContent>
        <AppHeaderActions>
          <div className="flex items-center gap-2 text-sm">
            <SearchCommand />
            <InvoiceCombobox
              align="end"
              onSelect={onInvoiceSelect}
              status={[InvoiceStatusEnum.open, InvoiceStatusEnum.paid]}
              minOutstandingAmount={0.01}
            >
              <Button type="button" size="sm">
                <PlusIcon />
                Add credit note
              </Button>
            </InvoiceCombobox>
          </div>
        </AppHeaderActions>
      </AppHeader>
      <main className="flex-1">
        <SectionGroup>
          <Section>
            <SectionHeader>
              <SectionTitle>Credit notes</SectionTitle>
              <SectionDescription>
                Track adjustments issued against finalized invoices.
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
                      onClick={() => {
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
                        {query.isLoading ? "…" : (query.data?.count ?? 0)}
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
                        setQueryState({ page: 1, search: event.target.value })
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
                        <EmptyTitle>Add your first credit note</EmptyTitle>
                        <EmptyDescription>
                          Credit notes are adjustments issued against finalized
                          invoices.
                        </EmptyDescription>
                      </EmptyHeader>
                      <EmptyContent>
                        <InvoiceCombobox
                          onSelect={onInvoiceSelect}
                          status={[
                            InvoiceStatusEnum.open,
                            InvoiceStatusEnum.paid,
                          ]}
                          minOutstandingAmount={0.01}
                        >
                          <Button size="sm">
                            <PlusIcon />
                            Add credit note
                          </Button>
                        </InvoiceCombobox>
                      </EmptyContent>
                    </Empty>
                  ) : (
                    <Empty>
                      <EmptyHeader>
                        <EmptyTitle>No results found</EmptyTitle>
                        <EmptyDescription>
                          Try adjusting your filters to find credit notes you're
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
  );
}
