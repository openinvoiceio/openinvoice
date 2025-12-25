import { usePricesList } from "@/api/endpoints/prices/prices";
import {
  getProductsListQueryKey,
  getProductsRetrieveQueryKey,
  useProductsRetrieve,
  useUpdateProduct,
} from "@/api/endpoints/products/products";
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
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { columns } from "@/components/price-table";
import { ProductBadge } from "@/components/product-badge";
import { ProductDropdown } from "@/components/product-dropdown";
import { pushModal } from "@/components/push-modals";
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
  DataSidebarTitle,
  DataSidebarTrigger,
} from "@/components/ui/data-sidebar";
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
import { SidebarTrigger } from "@/components/ui/sidebar.tsx";
import { useDataTable } from "@/hooks/use-data-table";
import { getErrorSummary } from "@/lib/api/errors.ts";
import { formatDatetime } from "@/lib/formatters";
import { formatPrices } from "@/lib/products.ts";
import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import {
  BoxIcon,
  BracesIcon,
  InfoIcon,
  MoreHorizontalIcon,
  PencilIcon,
  PlusIcon,
} from "lucide-react";
import { useMemo } from "react";
import { toast } from "sonner";

export const Route = createFileRoute("/(dashboard)/products/$id")({
  component: RouteComponent,
});

function RouteComponent() {
  const { id } = Route.useParams();
  const queryClient = useQueryClient();
  const { data: product } = useProductsRetrieve(id);
  const pageSize = 20;
  const { data: prices } = usePricesList({
    page_size: pageSize,
    ordering: "-created_at",
    product_id: id,
  });
  const { table } = useDataTable({
    data: prices?.results || [],
    columns,
    pageCount: prices?.count ? Math.ceil(prices.count / pageSize) : 0,
    initialState: {
      sorting: [{ id: "created_at", desc: true }],
      pagination: { pageSize, pageIndex: 0 },
      columnVisibility: {
        select: false,
        customer_name: false,
        due_date: false,
        updated_at: false,
      },
    },
    enableSorting: false,
    enableHiding: false,
  });
  const updateProduct = useUpdateProduct({
    mutation: {
      onSuccess: async (product) => {
        await queryClient.invalidateQueries({
          queryKey: getProductsListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getProductsRetrieveQueryKey(product.id),
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  const description = useMemo(() => formatPrices(product), [product]);

  if (!product) return;

  return (
    <div>
      <AppHeader>
        <AppHeaderContent>
          <SidebarTrigger />
          <NavBreadcrumb
            items={[
              {
                type: "link",
                label: "Products",
                href: "/products",
              },
              { type: "page", label: product.name },
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
              onClick={() => pushModal("ProductEditSheet", { product })}
            >
              <PencilIcon />
              Edit
            </Button>
            <ProductDropdown product={product} actions={{ edit: false }}>
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="data-[state=open]:bg-accent size-8"
              >
                <MoreHorizontalIcon />
              </Button>
            </ProductDropdown>
          </div>
        </AppHeaderActions>
      </AppHeader>
      <main className="flex min-h-[calc(100svh_-_56px)]">
        <SectionGroup>
          <Section>
            <SectionHeader className="flex flex-row items-center gap-2">
              <Avatar className="size-12 rounded-md">
                <AvatarImage src={product.image_url || undefined} />
                <AvatarFallback className="rounded-md">
                  <BoxIcon className="size-6" />
                </AvatarFallback>
              </Avatar>
              <div>
                <div className="flex items-center gap-2 self-start">
                  <SectionTitle>{product.name}</SectionTitle>
                  <ProductBadge isActive={product.is_active} />
                </div>
                <SectionDescription>{description}</SectionDescription>
              </div>
            </SectionHeader>
          </Section>
          <Section>
            <SectionHeader>
              <SectionTitle>Prices</SectionTitle>
            </SectionHeader>
            <DataTableContainer>
              <DataTable table={table}>
                <Empty>
                  <EmptyHeader>
                    <EmptyTitle>
                      Add your first price for {product.name}
                    </EmptyTitle>
                    <EmptyDescription>
                      Prices define how much and how you charge for your
                      products.
                    </EmptyDescription>
                  </EmptyHeader>
                  <EmptyContent>
                    <Button
                      size="sm"
                      onClick={() =>
                        pushModal("PriceCreateSheet", {
                          productId: product.id,
                        })
                      }
                    >
                      <PlusIcon />
                      Add price
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
                <DataListValue>{product.id}</DataListValue>
              </DataListItem>
              <DataListItem>
                <DataListLabel>Name</DataListLabel>
                <DataListValue>{product.name}</DataListValue>
              </DataListItem>
              <DataListItem>
                <DataListLabel>Description</DataListLabel>
                <DataListValue>{product.description || "-"}</DataListValue>
              </DataListItem>
              <DataListItem>
                <DataListLabel>Created</DataListLabel>
                <DataListValue>
                  {formatDatetime(product.created_at)}
                </DataListValue>
              </DataListItem>
              <DataListItem>
                <DataListLabel>Last updated</DataListLabel>
                <DataListValue>
                  {product.updated_at
                    ? formatDatetime(product.updated_at)
                    : "-"}
                </DataListValue>
              </DataListItem>
            </DataList>
          </DataSidebarContent>
          <DataSidebarContent value="metadata">
            <DataSidebarTitle>Metadata</DataSidebarTitle>
            <Metadata
              className="my-1 px-4"
              data={product.metadata as Record<string, string>}
              onSubmit={(metadata) => {
                void updateProduct.mutateAsync({
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
  );
}
