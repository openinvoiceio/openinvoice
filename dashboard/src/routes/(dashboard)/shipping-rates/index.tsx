import { useShippingRatesList } from "@/api/endpoints/shipping-rates/shipping-rates.ts";
import type { ShippingRate } from "@/api/models";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
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
import { columns } from "@/components/shipping-rate-table";
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
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
import { SidebarTrigger } from "@/components/ui/sidebar.tsx";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDataTable } from "@/hooks/use-data-table";
import { getSortingStateParser } from "@/lib/parsers";
import { createFileRoute } from "@tanstack/react-router";
import { addDays, formatISO } from "date-fns";
import {
  BoxIcon,
  PercentIcon,
  PlusIcon,
  TagIcon,
  TruckIcon,
} from "lucide-react";
import {
  parseAsArrayOf,
  parseAsInteger,
  parseAsIsoDateTime,
  parseAsString,
  useQueryStates,
} from "nuqs";

export const Route = createFileRoute("/(dashboard)/shipping-rates/")({
  component: RouteComponent,
});

function RouteComponent() {
  const navigate = Route.useNavigate();
  const [{ page, perPage, sort, name, created_at }] = useQueryStates({
    page: parseAsInteger.withDefault(1),
    perPage: parseAsInteger.withDefault(20),
    sort: getSortingStateParser<ShippingRate>().withDefault([
      { id: "created_at", desc: true },
    ]),
    name: parseAsString.withDefault(""),
    created_at: parseAsArrayOf(parseAsIsoDateTime).withDefault([]),
  });

  const { data } = useShippingRatesList({
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
        updated_at: false,
      },
    },
  });

  return (
    <div>
      <AppHeader>
        <AppHeaderContent>
          <SidebarTrigger />
          <NavBreadcrumb items={[{ type: "page", label: "Shipping rates" }]} />
        </AppHeaderContent>
        <AppHeaderActions>
          <div className="flex items-center gap-2 text-sm">
            <SearchCommand />
            <Button
              type="button"
              size="sm"
              onClick={() => pushModal("ShippingRateCreateSheet", { name: "" })}
            >
              <PlusIcon />
              Add shipping rate
            </Button>
          </div>
        </AppHeaderActions>
      </AppHeader>
      <main className="w-full flex-1">
        <SectionGroup>
          <Section>
            <SectionHeader>
              <SectionTitle>Product catalogue</SectionTitle>
            </SectionHeader>
            <Tabs
              defaultValue="/shipping-rates"
              onValueChange={(value) => navigate({ to: value })}
            >
              <TabsList>
                <TabsTrigger value="/products">
                  <BoxIcon />
                  Products
                </TabsTrigger>
                <TabsTrigger value="/coupons">
                  <TagIcon />
                  Coupons
                </TabsTrigger>
                <TabsTrigger value="/tax-rates">
                  <PercentIcon />
                  Tax rates
                </TabsTrigger>
                <TabsTrigger value="/shipping-rates">
                  <TruckIcon />
                  Shipping rates
                </TabsTrigger>
              </TabsList>
              <TabsContent value="/shipping-rates">
                <DataTableContainer>
                  <DataTableToolbar table={table}>
                    <DataTableFilterList table={table} />
                    <DataTableSortList table={table} />
                    <DataTableViewOptions table={table} />
                  </DataTableToolbar>
                  <DataTable table={table}>
                    <Empty>
                      <EmptyHeader>
                        <EmptyHeader>
                          <EmptyTitle>Add your first shipping rate</EmptyTitle>
                          <EmptyDescription>
                            Shipping rates help you manage how much to charge
                            for shipping.
                          </EmptyDescription>
                        </EmptyHeader>
                        <EmptyContent>
                          <Button
                            size="sm"
                            onClick={() =>
                              pushModal("ShippingRateCreateSheet", { name: "" })
                            }
                          >
                            <PlusIcon />
                            Add shipping rate
                          </Button>
                        </EmptyContent>
                      </EmptyHeader>
                    </Empty>
                  </DataTable>
                  <DataTableFooter>
                    <DataTablePagination table={table} />
                  </DataTableFooter>
                </DataTableContainer>
              </TabsContent>
            </Tabs>
          </Section>
        </SectionGroup>
      </main>
    </div>
  );
}
