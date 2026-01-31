import {
  useGetGrossRevenue,
  useGetOverdueBalance,
} from "@/api/endpoints/analytics/analytics";
import {
  getCustomersListQueryKey,
  getCustomersRetrieveQueryKey,
  useCustomersRetrieve,
  useUpdateCustomer,
} from "@/api/endpoints/customers/customers";
import {
  getInvoicesListQueryKey,
  useInvoicesList,
} from "@/api/endpoints/invoices/invoices";
import { useNumberingSystemsRetrieve } from "@/api/endpoints/numbering-systems/numbering-systems";
import { useCreatePortalSession } from "@/api/endpoints/portal/portal";
import { AddressView } from "@/components/address-view";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { AppSidebar } from "@/components/app-sidebar";
import { CustomerDropdown } from "@/components/customer-dropdown";
import { DataTable } from "@/components/data-table/data-table";
import { columns } from "@/components/invoice-table";
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { NumberingSystemView } from "@/components/numbering-system-view";
import { pushModal } from "@/components/push-modals.tsx";
import { SearchCommand } from "@/components/search-command.tsx";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
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
} from "@/components/ui/data-sidebar";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty.tsx";
import { Metadata } from "@/components/ui/metadata";
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
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useDataTable } from "@/hooks/use-data-table";
import { getErrorSummary } from "@/lib/api/errors";
import { getInitialColumnVisibility } from "@/lib/data-table.ts";
import {
  formatCountry,
  formatDatetime,
  formatPercentage,
  formatTaxIdType,
} from "@/lib/formatters";
import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { format } from "date-fns";
import {
  BracesIcon,
  ExternalLinkIcon,
  InfoIcon,
  MoreHorizontalIcon,
  PencilIcon,
  PlusIcon,
  UserIcon,
} from "lucide-react";
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts";
import { toast } from "sonner";

export const Route = createFileRoute("/(dashboard)/customers/$id")({
  component: RouteComponent,
});

const chartConfig = {
  total_amount: {
    label: "Total amount",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

function RouteComponent() {
  const { auth, account } = Route.useRouteContext();
  const { id } = Route.useParams();
  const queryClient = useQueryClient();
  const { data: customer } = useCustomersRetrieve(id);
  const { data: numberingSystem } = useNumberingSystemsRetrieve(
    customer?.invoice_numbering_system_id || "",
    {
      query: {
        enabled: !!customer?.invoice_numbering_system_id,
      },
    },
  );
  const pageSize = 20;
  const { data: invoices } = useInvoicesList({
    page_size: pageSize,
    customer_id: id,
    ordering: "-created_at",
  });
  const { table } = useDataTable({
    data: invoices?.results || [],
    columns,
    pageCount: invoices?.count ? Math.ceil(invoices.count / pageSize) : 0,
    initialState: {
      sorting: [{ id: "created_at", desc: true }],
      pagination: { pageSize, pageIndex: 0 },
      columnVisibility: getInitialColumnVisibility(columns, [
        "number",
        "due_date",
        "total_amount",
        "status",
      ]),
    },
    enableSorting: false,
    enableHiding: false,
  });
  const grossRevenue = useGetGrossRevenue({
    currency: customer?.currency || undefined,
    customer_id: id,
  });
  const overdueBalance = useGetOverdueBalance({
    currency: customer?.currency || undefined,
    customer_id: id,
  });
  const updateCustomer = useUpdateCustomer({
    mutation: {
      onSuccess: async ({ id }) => {
        await queryClient.invalidateQueries({
          queryKey: getCustomersListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getCustomersRetrieveQueryKey(id),
        });
        await queryClient.invalidateQueries({
          queryKey: getInvoicesListQueryKey(),
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });
  const createPortalSession = useCreatePortalSession({
    mutation: {
      onSuccess: async ({ portal_url }) => {
        window.open(portal_url, "_blank");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  if (!customer) return;

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
                    label: "Customers",
                    href: "/customers",
                  },
                  { type: "page", label: customer.name },
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
                  onClick={() =>
                    createPortalSession.mutateAsync({
                      data: { customer_id: customer.id },
                    })
                  }
                  disabled={createPortalSession.isPending}
                >
                  {createPortalSession.isPending ? (
                    <Spinner />
                  ) : (
                    <ExternalLinkIcon />
                  )}
                  Customer portal
                </Button>
                <Button type="button" variant="outline" size="sm" asChild>
                  <Link to="/customers/$id/edit" params={{ id: customer.id }}>
                    <PencilIcon />
                    Edit
                  </Link>
                </Button>
                <CustomerDropdown customer={customer} actions={{ edit: false }}>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    className="data-[state=open]:bg-accent size-8"
                  >
                    <MoreHorizontalIcon />
                  </Button>
                </CustomerDropdown>
              </div>
            </AppHeaderActions>
          </AppHeader>
          <main className="flex">
            <SectionGroup>
              <Section>
                <SectionHeader className="flex flex-row items-center gap-2">
                  <Avatar className="size-12 rounded-md">
                    <AvatarImage src={customer.logo_url || undefined} />
                    <AvatarFallback className="rounded-md">
                      <UserIcon className="size-6" />
                    </AvatarFallback>
                  </Avatar>
                  <div className="self-start">
                    <SectionTitle>{customer.name}</SectionTitle>
                    <SectionDescription>{customer.email}</SectionDescription>
                  </div>
                </SectionHeader>
              </Section>
              <Section>
                <SectionHeader>
                  <SectionTitle>Insights</SectionTitle>
                  <SectionDescription></SectionDescription>
                </SectionHeader>
                <div className="flex gap-4 space-y-0">
                  <Card className="w-full">
                    <CardHeader>
                      <div className="flex items-center gap-2">
                        <CardTitle>Gross Revenue</CardTitle>
                        <TooltipProvider delayDuration={0}>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="size-4"
                              >
                                <InfoIcon className="size-3.5" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              Total revenue from paid invoices within 12 months.
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <ChartContainer
                        config={chartConfig}
                        className="aspect-auto h-32 w-full"
                      >
                        <AreaChart
                          data={
                            grossRevenue.data?.map((value) => {
                              return {
                                date: value.date,
                                total_amount: Number(value.total_amount),
                              };
                            }) || []
                          }
                        >
                          <CartesianGrid vertical={false} />
                          <XAxis
                            dataKey="date"
                            tickLine={false}
                            axisLine={false}
                            tickMargin={8}
                            minTickGap={32}
                            tickFormatter={(value) => format(value, "LLL")}
                            allowDataOverflow={false}
                          />
                          <ChartTooltip
                            cursor={false}
                            content={
                              <ChartTooltipContent
                                indicator="line"
                                labelFormatter={(value) =>
                                  format(value, "LLLL, yyyy")
                                }
                              />
                            }
                          />
                          <Area
                            dataKey="total_amount"
                            type="monotone"
                            fill="var(--color-total_amount)"
                            fillOpacity={0.4}
                            stroke="var(--color-total_amount)"
                          />
                        </AreaChart>
                      </ChartContainer>
                    </CardContent>
                  </Card>

                  <Card className="w-full">
                    <CardHeader>
                      <div className="flex items-center gap-2">
                        <CardTitle>Overdue balance</CardTitle>
                        <TooltipProvider delayDuration={0}>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="size-4"
                              >
                                <InfoIcon className="size-3.5" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              Total amount from overdue invoices within 12
                              months.
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <ChartContainer
                        config={chartConfig}
                        className="aspect-auto h-32 w-full"
                      >
                        <AreaChart
                          data={
                            overdueBalance.data?.map((value) => {
                              return {
                                date: value.date,
                                total_amount: Number(value.total_amount),
                              };
                            }) || []
                          }
                        >
                          <CartesianGrid vertical={false} />
                          <XAxis
                            dataKey="date"
                            tickLine={false}
                            axisLine={false}
                            tickMargin={8}
                            minTickGap={32}
                            tickFormatter={(value) => format(value, "LLL")}
                            allowDataOverflow={false}
                          />
                          <ChartTooltip
                            cursor={false}
                            content={
                              <ChartTooltipContent
                                indicator="line"
                                labelFormatter={(value) =>
                                  format(value, "LLLL, yyyy")
                                }
                              />
                            }
                          />
                          <Area
                            dataKey="total_amount"
                            type="monotone"
                            fill="var(--color-total_amount)"
                            fillOpacity={0.4}
                            stroke="var(--color-total_amount)"
                          />
                        </AreaChart>
                      </ChartContainer>
                    </CardContent>
                  </Card>
                </div>
              </Section>

              <Section>
                <SectionHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <SectionTitle>Invoices</SectionTitle>
                      <SectionDescription>
                        Invoices issued to {customer.name}
                      </SectionDescription>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-fit"
                      onClick={() =>
                        pushModal("InvoiceCreateDialog", {
                          defaultCustomer: customer,
                        })
                      }
                    >
                      <PlusIcon />
                      Add invoice
                    </Button>
                  </div>
                </SectionHeader>
                <DataTable table={table}>
                  <Empty>
                    <EmptyHeader>
                      <EmptyTitle>
                        Add your first invoice for {customer.name}
                      </EmptyTitle>
                      <EmptyDescription>
                        Bill for products or services by issuing invoice
                      </EmptyDescription>
                    </EmptyHeader>
                    <EmptyContent>
                      <Button
                        size="sm"
                        onClick={() =>
                          pushModal("InvoiceCreateDialog", {
                            defaultCustomer: customer,
                          })
                        }
                      >
                        <PlusIcon />
                        Add invoice
                      </Button>
                    </EmptyContent>
                  </Empty>
                </DataTable>
              </Section>
              <Section>
                <SectionHeader>
                  <SectionTitle>Tax rates</SectionTitle>
                </SectionHeader>
                {customer.tax_rates.length !== 0 ? (
                  <div className="overflow-hidden rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Name</TableHead>
                          <TableHead>Percentage</TableHead>
                          <TableHead>Country</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {customer.tax_rates.map((taxRate) => (
                          <TableRow key={taxRate.id}>
                            <TableCell className="font-medium">
                              {taxRate.name}
                            </TableCell>
                            <TableCell>
                              {formatPercentage(taxRate.percentage)}
                            </TableCell>
                            <TableCell>
                              {taxRate.country
                                ? formatCountry(taxRate.country)
                                : "-"}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <Empty className="border">
                    <EmptyHeader>
                      <EmptyTitle>No tax rates assigned</EmptyTitle>
                      <EmptyDescription>
                        Assigned tax rates will be applied to invoices by
                        default
                      </EmptyDescription>
                    </EmptyHeader>
                  </Empty>
                )}
              </Section>
              <Section>
                <SectionHeader>
                  <SectionTitle>Tax IDs</SectionTitle>
                </SectionHeader>
                {customer.tax_ids.length !== 0 ? (
                  <div className="overflow-hidden rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Type</TableHead>
                          <TableHead>Number</TableHead>
                          <TableHead>Country</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {customer.tax_ids.map((taxId) => (
                          <TableRow key={taxId.id}>
                            <TableCell className="font-medium">
                              {formatTaxIdType(taxId.type)}
                            </TableCell>
                            <TableCell>{taxId.number}</TableCell>
                            <TableCell>
                              {taxId.country
                                ? formatCountry(taxId.country)
                                : "-"}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <Empty className="border">
                    <EmptyHeader>
                      <EmptyTitle>No tax ids configured</EmptyTitle>
                      <EmptyDescription>
                        Configured tax ids will be displayed on invoices
                      </EmptyDescription>
                    </EmptyHeader>
                  </Empty>
                )}
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
                    <DataListValue>{customer.id}</DataListValue>
                  </DataListItem>
                  <DataListItem>
                    <DataListLabel>Name</DataListLabel>
                    <DataListValue>{customer.name}</DataListValue>
                  </DataListItem>
                  {customer.legal_name && (
                    <DataListItem>
                      <DataListLabel>Legal name</DataListLabel>
                      <DataListValue>{customer.legal_name}</DataListValue>
                    </DataListItem>
                  )}
                  {customer.legal_number && (
                    <DataListItem>
                      <DataListLabel>Legal number</DataListLabel>
                      <DataListValue>{customer.legal_number}</DataListValue>
                    </DataListItem>
                  )}
                  <DataListItem>
                    <DataListLabel>Email</DataListLabel>
                    <DataListValue>{customer.email || "-"}</DataListValue>
                  </DataListItem>
                  <DataListItem>
                    <DataListLabel>Phone</DataListLabel>
                    <DataListValue>{customer.phone || "-"}</DataListValue>
                  </DataListItem>
                  <DataListItem>
                    <DataListLabel>Billing address</DataListLabel>
                    <DataListValue>
                      <AddressView address={customer.address} />
                    </DataListValue>
                  </DataListItem>
                  <DataListItem>
                    <DataListLabel>Description</DataListLabel>
                    <DataListValue>{customer.description || "-"}</DataListValue>
                  </DataListItem>
                  <DataListItem>
                    <DataListLabel>Created</DataListLabel>
                    <DataListValue>
                      {formatDatetime(customer.created_at)}
                    </DataListValue>
                  </DataListItem>
                  <DataListItem>
                    <DataListLabel>Last updated</DataListLabel>
                    <DataListValue>
                      {customer.updated_at
                        ? formatDatetime(customer.updated_at)
                        : "-"}
                    </DataListValue>
                  </DataListItem>
                </DataList>
                <DataSidebarSeparator />
                <DataList
                  orientation="vertical"
                  className="gap-3 px-4"
                  size="sm"
                >
                  <DataListItem>
                    <DataListLabel>Currency</DataListLabel>
                    <DataListValue>{customer.currency || "-"}</DataListValue>
                  </DataListItem>
                  <DataListItem>
                    <DataListLabel>Net payment term</DataListLabel>
                    <DataListValue>
                      {customer.net_payment_term !== null
                        ? `${customer.net_payment_term} days`
                        : "-"}
                    </DataListValue>
                  </DataListItem>
                  <DataListItem>
                    <DataListLabel>Numbering system</DataListLabel>
                    <DataListValue>
                      <NumberingSystemView numberingSystem={numberingSystem} />
                    </DataListValue>
                  </DataListItem>
                </DataList>
                {customer.shipping && (
                  <>
                    <DataSidebarSeparator />
                    <DataList
                      orientation="vertical"
                      className="gap-3 px-4"
                      size="sm"
                    >
                      <DataListItem>
                        <DataListLabel>Shipping name</DataListLabel>
                        <DataListValue>
                          {customer.shipping.name || "-"}
                        </DataListValue>
                      </DataListItem>
                      <DataListItem>
                        <DataListLabel>Shipping phone</DataListLabel>
                        <DataListValue>
                          {customer.shipping.phone || "-"}
                        </DataListValue>
                      </DataListItem>
                      <DataListItem>
                        <DataListLabel>Shipping address</DataListLabel>
                        <DataListValue>
                          <AddressView
                            address={customer.shipping.address || undefined}
                          />
                        </DataListValue>
                      </DataListItem>
                    </DataList>
                  </>
                )}
              </DataSidebarContent>
              <DataSidebarContent value="metadata">
                <DataSidebarTitle>Metadata</DataSidebarTitle>
                <Metadata
                  className="my-1 px-4"
                  data={customer.metadata as Record<string, string>}
                  onSubmit={(metadata) => {
                    void updateCustomer.mutateAsync({
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
