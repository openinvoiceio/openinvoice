import type { Quote, QuoteLine } from "@/api/models";
import { CurrencyEnum, QuoteStatusEnum } from "@/api/models";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { QuoteBadge } from "@/features/quotes/components/quote-badge";
import { QuoteDropdown } from "@/features/quotes/components/quote-dropdown";
import { formatAmount, formatDate, formatDatetime } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { Link } from "@tanstack/react-router";
import type { ColumnDef } from "@tanstack/react-table";
import {
  BoxIcon,
  CalendarIcon,
  ChevronRight,
  CurrencyIcon,
  HashIcon,
  MoreHorizontalIcon,
} from "lucide-react";

export const columns: Array<ColumnDef<Quote>> = [
  {
    id: "select",
    header: ({ table }) => (
      <Checkbox
        checked={
          table.getIsAllPageRowsSelected() ||
          (table.getIsSomePageRowsSelected() && "indeterminate")
        }
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
      />
    ),
    enableSorting: false,
    enableHiding: false,
    size: 40,
  },
  {
    id: "number",
    header: "Number",
    accessorKey: "number",
    cell: ({ row }) => (
      <Link
        to="/quotes/$id"
        params={{ id: row.original.id }}
        className={cn("group/link flex items-center gap-1")}
      >
        <div className="truncate font-medium">
          {row.getValue("number") || row.original.id}
        </div>
        <ChevronRight className="text-muted-foreground group-hover/link:text-foreground ml-auto size-3" />
      </Link>
    ),
    meta: {
      label: "Number",
    },
    enableHiding: false,
    enableSorting: false,
  },
  {
    id: "customer",
    header: "Customer",
    accessorKey: "customer",
    cell: ({ row }) => (
      <Link
        to="/customers/$id"
        params={{ id: row.original.customer.id }}
        className={cn("group/link flex items-center gap-1")}
      >
        <div className="truncate font-medium">{row.original.customer.name}</div>
        <ChevronRight className="text-muted-foreground group-hover/link:text-foreground ml-auto size-3" />
      </Link>
    ),
    meta: {
      label: "Customer",
      variant: "customer",
    },
    enableSorting: false,
    enableColumnFilter: true,
  },
  {
    id: "issue_date",
    header: "Issue date",
    accessorKey: "issue_date",
    cell: ({ row }) => {
      const value: string | undefined = row.getValue("issue_date");
      return (
        <div className={cn(!value && "text-muted-foreground")}>
          {value ? formatDate(value) : "-"}
        </div>
      );
    },
    meta: {
      label: "Issue date",
      variant: "dateRange",
      icon: CalendarIcon,
    },
    enableSorting: true,
    enableColumnFilter: true,
  },
  {
    id: "total_amount",
    header: "Total",
    accessorKey: "total_amount",
    cell: ({ row }) => {
      return (
        <div>
          {formatAmount(row.getValue("total_amount"), row.original.currency)}
        </div>
      );
    },
    meta: {
      label: "Total",
      variant: "range",
      icon: HashIcon,
      range: [0, 10000],
    },
    enableSorting: false,
    enableColumnFilter: true,
  },
  {
    id: "status",
    header: "Status",
    accessorKey: "status",
    cell: ({ row }) => <QuoteBadge status={row.getValue("status")} />,
    meta: {
      label: "Status",
      variant: "multiSelect",
      icon: CalendarIcon,
      options: Object.values(QuoteStatusEnum).map((status) => {
        return {
          label: status.charAt(0).toUpperCase() + status.slice(1),
          value: status,
        };
      }),
    },
    enableHiding: false,
    enableColumnFilter: true,
  },
  {
    id: "created_at",
    accessorKey: "created_at",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Created" />
    ),
    cell: ({ row }) => {
      return <div>{formatDatetime(row.getValue("created_at"))}</div>;
    },
    meta: {
      label: "Created",
      variant: "dateRange",
      icon: CalendarIcon,
    },
    enableSorting: true,
    enableColumnFilter: true,
  },
  {
    id: "updated_at",
    accessorKey: "updated_at",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Last updated" />
    ),
    cell: ({ row }) => {
      const value: string | null = row.getValue("updated_at");
      return (
        <div className={cn(!value && "text-muted-foreground")}>
          {value ? formatDatetime(value) : "-"}
        </div>
      );
    },
    meta: {
      label: "Last updated",
    },
    enableSorting: false,
  },
  {
    id: "currency",
    header: "Currency",
    accessorKey: "currency",
    cell: ({ row }) => {
      return <div>{row.getValue("currency")}</div>;
    },
    meta: {
      label: "Currency",
      variant: "multiSelect",
      icon: CurrencyIcon,
      options: Object.values(CurrencyEnum).map((currency) => {
        return { label: currency, value: currency };
      }),
    },
    enableSorting: false,
    enableColumnFilter: true,
  },
  {
    id: "subtotal_amount",
    header: "Subtotal",
    accessorKey: "subtotal_amount",
    cell: ({ row }) => {
      return (
        <div>
          {formatAmount(row.getValue("subtotal_amount"), row.original.currency)}
        </div>
      );
    },
    meta: {
      label: "Subtotal",
      variant: "range",
      icon: HashIcon,
      range: [0, 10000],
    },
    enableSorting: false,
    enableColumnFilter: true,
  },
  {
    id: "total_discount_amount",
    header: "Total discount",
    accessorKey: "total_discount_amount",
    cell: ({ row }) => {
      return (
        <div>
          {formatAmount(
            row.getValue("total_discount_amount"),
            row.original.currency,
          )}
        </div>
      );
    },
    meta: {
      label: "Total discount",
    },
    enableSorting: false,
  },
  {
    id: "total_amount_excluding_tax",
    header: "Total excluding tax",
    accessorKey: "total_amount_excluding_tax",
    cell: ({ row }) => {
      return (
        <div>
          {formatAmount(
            row.getValue("total_amount_excluding_tax"),
            row.original.currency,
          )}
        </div>
      );
    },
    meta: {
      label: "Total excluding tax",
    },
    enableSorting: false,
  },
  {
    id: "total_tax_amount",
    header: "Total tax",
    accessorKey: "total_tax_amount",
    cell: ({ row }) => {
      return (
        <div>
          {formatAmount(
            row.getValue("total_tax_amount"),
            row.original.currency,
          )}
        </div>
      );
    },
    meta: {
      label: "Total tax",
    },
    enableSorting: false,
  },
  {
    id: "lines",
    header: "Lines",
    accessorKey: "lines",
    cell: ({ row }) => {
      const value: Array<QuoteLine> = row.getValue("lines");
      return (
        <div
          className={cn(
            "max-w-96 truncate",
            value.length === 0 && "text-muted-foreground",
          )}
        >
          {value.length > 0
            ? value.map((line) => line.description).join(", ")
            : "-"}
        </div>
      );
    },
    meta: {
      label: "Lines",
      variant: "product",
      icon: BoxIcon,
    },
    enableSorting: false,
    enableColumnFilter: true,
  },
  {
    id: "actions",
    size: 40,
    enableHiding: false,
    cell: ({ row }) => (
      <QuoteDropdown quote={row.original}>
        <Button
          size="icon"
          variant="ghost"
          className="data-[state=open]:bg-accent size-7"
        >
          <MoreHorizontalIcon />
        </Button>
      </QuoteDropdown>
    ),
  },
];
