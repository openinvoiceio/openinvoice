import {
  useGetGrossRevenue,
  useGetOverdueBalance,
} from "@/api/endpoints/analytics/analytics";
import { useInvoicesList } from "@/api/endpoints/invoices/invoices";
import { CurrencyEnum } from "@/api/models";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { AppSidebar } from "@/components/app-sidebar";
import { CurrencyCombobox } from "@/components/currency-combobox.tsx";
import { DataTable } from "@/components/data-table/data-table";
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { SearchCommand } from "@/components/search-command.tsx";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { ComboboxButton } from "@/components/ui/combobox-button.tsx";
import { Empty, EmptyHeader, EmptyTitle } from "@/components/ui/empty.tsx";
import {
  MetricCard,
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar.tsx";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { columns } from "@/features/invoices/tables/columns";
import { useDataTable } from "@/hooks/use-data-table";
import { getInitialColumnVisibility } from "@/lib/data-table.ts";
import { formatAmount, formatISODate } from "@/lib/formatters";
import { createFileRoute } from "@tanstack/react-router";
import { format, subDays } from "date-fns";
import Decimal from "decimal.js";
import { InfoIcon } from "lucide-react";
import { parseAsStringEnum, useQueryState } from "nuqs";
import { useMemo } from "react";
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts";

export const Route = createFileRoute("/(dashboard)/overview")({
  component: RouteComponent,
});

type DateRange = "30d" | "90d" | "180d" | "365d";

const chartConfig = {
  total_amount: {
    label: "Total amount",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

function RouteComponent() {
  const { auth, account } = Route.useRouteContext();
  const { data } = useInvoicesList({
    page_size: 20,
    ordering: "-created_at",
    status: ["paid"],
  });

  const { table } = useDataTable({
    data: data?.results || [],
    columns,
    pageCount: data?.count ? Math.ceil(data.count / 20) : 0,
    initialState: {
      pagination: { pageSize: 20, pageIndex: 0 },
      columnVisibility: getInitialColumnVisibility(columns, [
        "number",
        "customer",
        "total_amount",
        "paid_at",
        "status",
      ]),
    },
    enableSorting: false,
    enableHiding: false,
  });

  const [range, setRange] = useQueryState(
    "range",
    parseAsStringEnum<DateRange>(["30d", "90d", "180d", "365d"]).withDefault(
      "90d",
    ),
  );
  const [currency, setCurrency] = useQueryState(
    "currency",
    parseAsStringEnum(Object.values(CurrencyEnum)).withDefault(
      account?.default_currency || CurrencyEnum.EUR,
    ),
  );

  const params = useMemo(
    () => ({
      date_after: formatISODate(
        subDays(new Date(), parseInt(range.slice(0, -1))),
      ),
      date_before: formatISODate(new Date()),
      currency: currency,
    }),
    [range, currency],
  );

  const grossRevenue = useGetGrossRevenue(params);
  const overdueBalance = useGetOverdueBalance(params);

  const invoicesCreated = useMemo(
    () =>
      grossRevenue.data?.reduce((sum, item) => sum + item.invoice_count, 0) ??
      0,
    [grossRevenue.data],
  );
  const grossTotal = useMemo(
    () =>
      grossRevenue.data?.reduce(
        (sum, item) => sum.plus(new Decimal(item.total_amount)),
        new Decimal(0),
      ) ?? new Decimal(0),
    [grossRevenue.data],
  );
  const overdueTotal = useMemo(
    () =>
      overdueBalance.data?.reduce(
        (sum, item) => sum.plus(new Decimal(item.total_amount)),
        new Decimal(0),
      ) ?? new Decimal(0),
    [overdueBalance.data],
  );

  const metrics = useMemo(
    () => [
      { title: "Invoices Created", value: invoicesCreated },
      {
        title: "Gross Revenue",
        value: formatAmount(grossTotal.toString(), currency),
      },
      {
        title: "Overdue Amount",
        value: formatAmount(overdueTotal.toString(), currency),
      },
    ],
    [invoicesCreated, grossTotal, overdueTotal],
  );

  return (
    <SidebarProvider>
      <AppSidebar user={auth.user} account={account} />
      <SidebarInset>
        <div>
          <AppHeader>
            <AppHeaderContent>
              <SidebarTrigger />
              <NavBreadcrumb items={[{ type: "page", label: "Overview" }]} />
            </AppHeaderContent>
            <AppHeaderActions>
              <div className="flex items-center gap-2 text-sm">
                <SearchCommand />
              </div>
            </AppHeaderActions>
          </AppHeader>
          <main className="w-full flex-1">
            <SectionGroup>
              <Section>
                <SectionHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <SectionTitle>Overview</SectionTitle>
                    <SectionDescription>
                      Welcome to your dashboard
                    </SectionDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Select
                      value={range}
                      onValueChange={(value) => setRange(value as DateRange)}
                    >
                      <SelectTrigger className="hidden w-[140px] sm:ml-auto sm:flex">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="30d">Last month</SelectItem>
                        <SelectItem value="90d">Last 3 months</SelectItem>
                        <SelectItem value="180d">Last 6 months</SelectItem>
                        <SelectItem value="365d">Last year</SelectItem>
                      </SelectContent>
                    </Select>
                    <CurrencyCombobox
                      align="end"
                      selected={currency}
                      onSelect={async (c) => {
                        await setCurrency(c as CurrencyEnum);
                      }}
                    >
                      <ComboboxButton>{currency}</ComboboxButton>
                    </CurrencyCombobox>
                  </div>
                </SectionHeader>
                <MetricCardGroup>
                  {metrics.map((metric) => (
                    <MetricCard key={metric.title}>
                      <MetricCardHeader>
                        <MetricCardTitle>{metric.title}</MetricCardTitle>
                      </MetricCardHeader>
                      <MetricCardValue>{metric.value}</MetricCardValue>
                    </MetricCard>
                  ))}
                </MetricCardGroup>
              </Section>

              <Section className="flex gap-4 space-y-0">
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
                            Total revenue from paid invoices within the selected
                            date range.
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
                            Total amount from overdue invoices within the
                            selected date range.
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
              </Section>

              <Section>
                <SectionHeader>
                  <SectionTitle>Invoices</SectionTitle>
                  <SectionDescription>
                    Paid invoices over the last 30 days.
                  </SectionDescription>
                </SectionHeader>
                <DataTable table={table}>
                  <Empty>
                    <EmptyHeader>
                      <EmptyTitle>You have no invoices yet</EmptyTitle>
                    </EmptyHeader>
                  </Empty>
                </DataTable>
              </Section>
            </SectionGroup>
          </main>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
