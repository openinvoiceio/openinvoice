import { useCustomersList } from "@/api/endpoints/customers/customers";
import type { Customer } from "@/api/models";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { AppSidebar } from "@/components/app-sidebar";
import { columns } from "@/components/customer-table";
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
import { pushModal } from "@/components/push-modals";
import { SearchCommand } from "@/components/search-command.tsx";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty.tsx";
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
import { getSortingStateParser } from "@/lib/parsers";
import { createFileRoute } from "@tanstack/react-router";
import { addDays, formatISO } from "date-fns";
import { PlusIcon } from "lucide-react";
import {
  parseAsArrayOf,
  parseAsInteger,
  parseAsIsoDateTime,
  parseAsString,
  useQueryStates,
} from "nuqs";

export const Route = createFileRoute("/(dashboard)/customers/")({
  component: RouteComponent,
});

function RouteComponent() {
  const { auth, account } = Route.useRouteContext();
  const navigate = Route.useNavigate();
  const [{ page, perPage, sort, name, created_at }] = useQueryStates({
    page: parseAsInteger.withDefault(1),
    perPage: parseAsInteger.withDefault(20),
    sort: getSortingStateParser<Customer>().withDefault([
      { id: "created_at", desc: true },
    ]),
    name: parseAsString.withDefault(""),
    created_at: parseAsArrayOf(parseAsIsoDateTime).withDefault([]),
  });

  const { data } = useCustomersList({
    page,
    page_size: perPage,
    ordering: sort.map((s) => `${s.desc ? "-" : ""}${s.id}`).join(","),
    ...(name && { search: name }),
    ...(created_at.length == 2 && {
      created_at_gte: formatISO(new Date(created_at[0])),
      created_at_lte: formatISO(addDays(new Date(created_at[1]), 1)),
    }),
  });
  const { table } = useDataTable({
    data: data?.results || [],
    columns,
    pageCount: data?.count ? Math.ceil(data.count / perPage) : 0,
    initialState: {
      sorting: sort,
      pagination: { pageSize: perPage, pageIndex: page - 1 },
      columnFilters: [
        { id: "name", value: name },
        { id: "created_at", value: created_at },
      ],
      columnVisibility: {
        phone: false,
        net_payment_term: false,
        updated_at: false,
      },
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
              <NavBreadcrumb items={[{ type: "page", label: "Customers" }]} />
            </AppHeaderContent>
            <AppHeaderActions>
              <div className="flex items-center gap-2 text-sm">
                <SearchCommand />
                <Button
                  type="button"
                  size="sm"
                  onClick={() =>
                    pushModal("CustomerCreateSheet", {
                      onSuccess: (customer) =>
                        navigate({
                          to: "/customers/$id/edit",
                          params: { id: customer.id },
                        }),
                    })
                  }
                >
                  <PlusIcon />
                  Add customer
                </Button>
              </div>
            </AppHeaderActions>
          </AppHeader>
          <main className="w-full flex-1">
            <SectionGroup>
              <Section>
                <SectionHeader>
                  <SectionTitle>Customers</SectionTitle>
                  <SectionDescription>
                    Manage your customers.
                  </SectionDescription>
                </SectionHeader>
                <DataTableContainer>
                  <DataTableToolbar table={table}>
                    <DataTableFilterList table={table} />
                    <DataTableSortList table={table} />
                    <DataTableViewOptions table={table} />
                  </DataTableToolbar>
                  <DataTable table={table}>
                    <Empty>
                      <EmptyHeader>
                        <EmptyTitle>Add your first customer</EmptyTitle>
                        <EmptyDescription>
                          Customers are people or businesses you invoice.
                        </EmptyDescription>
                      </EmptyHeader>
                      <EmptyContent>
                        <Button
                          size="sm"
                          onClick={() =>
                            pushModal("CustomerCreateSheet", { name: "" })
                          }
                        >
                          <PlusIcon />
                          Add customer
                        </Button>
                      </EmptyContent>
                    </Empty>
                  </DataTable>
                  <DataTableFooter>
                    <DataTablePagination table={table} />
                  </DataTableFooter>
                </DataTableContainer>
              </Section>
            </SectionGroup>
          </main>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
