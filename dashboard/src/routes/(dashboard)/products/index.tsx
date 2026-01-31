import {
  getProductsListQueryKey,
  productsList,
  useProductsList,
} from "@/api/endpoints/products/products";
import { ProductCatalogStatusEnum, type Product } from "@/api/models";
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
import { ProductCatalogTabs } from "@/components/product-catalog-tabs";
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
  MetricCardButton,
  MetricCardGroup,
  MetricCardHeader,
  MetricCardTitle,
  MetricCardValue,
} from "@/components/ui/metric-card";
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
} from "@/components/ui/sidebar.tsx";
import { TabsContent } from "@/components/ui/tabs";
import { columns } from "@/features/products/tables/product-columns";
import { useDataTable } from "@/hooks/use-data-table";
import { formatEnum } from "@/lib/formatters";
import { getSortingStateParser } from "@/lib/parsers";
import { useQueries } from "@tanstack/react-query";
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

const statusValues = Object.values(
  ProductCatalogStatusEnum,
) as ProductCatalogStatusEnum[];
const statusFilterValues: Array<ProductCatalogStatusEnum | "all"> = [
  ...statusValues,
  "all",
];
type StatusFilter = (typeof statusFilterValues)[number];

const searchParams = {
  page: parseAsInteger.withDefault(1),
  perPage: parseAsInteger.withDefault(20),
  sort: getSortingStateParser<Product>().withDefault([
    { id: "created_at", desc: true },
  ]),
  name: parseAsString.withDefault(""),
  status: parseAsStringEnum(statusFilterValues).withDefault("active"),
  created_at: parseAsArrayOf(parseAsIsoDateTime).withDefault([]),
};

export const Route = createFileRoute("/(dashboard)/products/")({
  component: RouteComponent,
});

function RouteComponent() {
  const { auth, account } = Route.useRouteContext();
  const navigate = Route.useNavigate();
  const [{ page, perPage, sort, name, status, created_at }, setQueryState] =
    useQueryStates(searchParams);
  const hasFilters =
    (name?.trim()?.length ?? 0) > 0 ||
    created_at.length === 2 ||
    status != "active";

  const { data } = useProductsList({
    page,
    page_size: perPage,
    ordering: sort.map((s) => `${s.desc ? "-" : ""}${s.id}`).join(","),
    ...(name && { search: name }),
    ...(status !== "all" && { status }),
    ...(created_at.length == 2 && {
      created_at_gte: formatISO(new Date(created_at[0])),
      created_at_lte: formatISO(addDays(new Date(created_at[1]), 1)),
    }),
  });

  const metrics: Array<{ value: StatusFilter; label: string }> = [
    { value: "all", label: "All" },
    ...statusValues.map((value) => ({
      value,
      label: formatEnum(value),
    })),
  ];

  const counters = useQueries({
    queries: metrics.map(({ value }) => ({
      queryKey: getProductsListQueryKey({
        ...(value === "all" ? {} : { status: value }),
      }),
      queryFn: () =>
        productsList({ ...(value === "all" ? {} : { status: value }) }),
      staleTime: 30_000,
    })),
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
    <SidebarProvider>
      <AppSidebar user={auth?.user} account={account} />
      <SidebarInset>
        <div>
          <AppHeader>
            <AppHeaderContent>
              <SidebarTrigger />
              <NavBreadcrumb items={[{ type: "page", label: "Products" }]} />
            </AppHeaderContent>
            <AppHeaderActions>
              <div className="flex items-center gap-2">
                <SearchCommand />
                <Button
                  type="button"
                  size="sm"
                  onClick={() => pushModal("ProductCreateSheet", { name: "" })}
                >
                  <PlusIcon />
                  Add product
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
                <ProductCatalogTabs
                  defaultValue="/products"
                  onValueChange={(value) => navigate({ to: value })}
                >
                  <TabsContent value="/products" className="my-2 grid gap-4">
                    <MetricCardGroup className="flex">
                      {metrics.map((item, index) => {
                        const query = counters[index];
                        return (
                          <MetricCardButton
                            key={item.value}
                            selected={status === item.value}
                            onClick={() =>
                              setQueryState({ status: item.value, page: 1 })
                            }
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
                        <DataTableFilterList table={table} />
                        <DataTableSortList table={table} />
                        <DataTableViewOptions table={table} />
                      </DataTableToolbar>
                      <DataTable table={table}>
                        <Empty>
                          <EmptyHeader>
                            <EmptyTitle>Add your first product</EmptyTitle>
                            <EmptyDescription>
                              Products are the core of your catalogue and define
                              what you sell.
                            </EmptyDescription>
                          </EmptyHeader>
                          {!hasFilters && (
                            <EmptyContent>
                              <Button
                                size="sm"
                                onClick={() =>
                                  pushModal("ProductCreateSheet", { name: "" })
                                }
                              >
                                <PlusIcon />
                                Add Product
                              </Button>
                            </EmptyContent>
                          )}
                        </Empty>
                      </DataTable>
                      <DataTableFooter>
                        <DataTablePagination table={table} />
                      </DataTableFooter>
                    </DataTableContainer>
                  </TabsContent>
                </ProductCatalogTabs>
              </Section>
            </SectionGroup>
          </main>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
