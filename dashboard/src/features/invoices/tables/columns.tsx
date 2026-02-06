import {
  CurrencyEnum,
  InvoiceStatusEnum,
  type Invoice,
  type InvoiceLine,
} from "@/api/models";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { InvoiceBadge } from "@/features/invoices/components/invoice-badge";
import { InvoiceDropdown } from "@/features/invoices/components/invoice-dropdown";
import {
  formatAmount,
  formatDate,
  formatDatetime,
  formatEnum,
} from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { Link } from "@tanstack/react-router";
import type { ColumnDef } from "@tanstack/react-table";
import { addDays } from "date-fns";
import {
  BoxIcon,
  CalendarIcon,
  ChevronRight,
  CircleDashedIcon,
  CurrencyIcon,
  HashIcon,
  MoreHorizontalIcon,
} from "lucide-react";

export const columns: ColumnDef<Invoice>[] = [
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
        to="/invoices/$id"
        params={{ id: row.original.id }}
        className={cn("group/link flex items-center gap-1")}
      >
        <div className="truncate font-medium">{row.getValue("number")}</div>
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
    cell: ({ row }) => {
      const invoice = row.original as Invoice & { customer_id?: string };
      const customerId = invoice.customer_id;
      const billingProfile = invoice.billing_profile;
      const label =
        billingProfile.legal_name || billingProfile.email || "Unnamed customer";
      if (!customerId) {
        return <div className="text-muted-foreground">{label}</div>;
      }
      return (
        <Link
          to="/customers/$id"
          params={{ id: customerId }}
          className={cn("group/link flex items-center gap-1")}
        >
          <div className="truncate font-medium">{label}</div>
          <ChevronRight className="text-muted-foreground group-hover/link:text-foreground ml-auto size-3" />
        </Link>
      );
    },
    meta: {
      label: "Customer",
      variant: "customer",
    },
    enableSorting: false,
    enableColumnFilter: true,
  },
  {
    id: "due_date",
    header: "Due date",
    accessorKey: "due_date",
    cell: ({ row }) => {
      const value: string | undefined = row.getValue("due_date");
      return (
        <div>
          {formatDate(
            value ? value : addDays(new Date(), row.original.net_payment_term),
          )}
        </div>
      );
    },
    meta: {
      label: "Due date",
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
    cell: ({ row }) => <InvoiceBadge status={row.getValue("status")} />,
    meta: {
      label: "Status",
      variant: "multiSelect",
      icon: CircleDashedIcon,
      options: Object.values(InvoiceStatusEnum).map((status) => {
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
    id: "paid_at",
    accessorKey: "paid_at",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Paid at" />
    ),
    cell: ({ row }) => {
      const value: string | null = row.getValue("paid_at");
      return (
        <div className={cn(!value && "text-muted-foreground")}>
          {value ? formatDatetime(value) : "-"}
        </div>
      );
    },
    meta: {
      label: "Paid at",
    },
    enableSorting: false,
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
    id: "tax_behavior",
    header: "Tax behavior",
    accessorKey: "tax_behavior",
    cell: ({ row }) => {
      return <div>{formatEnum(row.getValue("tax_behavior"))}</div>;
    },
    meta: {
      label: "Tax behavior",
    },
    enableSorting: false,
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
    id: "shipping_amount",
    header: "Shipping",
    accessorKey: "shipping_amount",
    cell: ({ row }) => {
      return (
        <div>
          {formatAmount(row.getValue("shipping_amount"), row.original.currency)}
        </div>
      );
    },
    meta: {
      label: "Shipping",
      variant: "range",
      icon: HashIcon,
      range: [0, 10000],
    },
    enableSorting: false,
    enableColumnFilter: true,
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
    id: "total_paid_amount",
    header: "Paid",
    accessorKey: "total_paid_amount",
    cell: ({ row }) => {
      return (
        <div>
          {formatAmount(
            row.getValue("total_paid_amount"),
            row.original.currency,
          )}
        </div>
      );
    },
    meta: {
      label: "Paid",
      variant: "range",
      icon: HashIcon,
      range: [0, 10000],
    },
    enableSorting: false,
    enableColumnFilter: true,
  },
  {
    id: "outstanding_amount",
    header: "Outstanding",
    accessorKey: "outstanding_amount",
    cell: ({ row }) => {
      return (
        <div>
          {formatAmount(
            row.getValue("outstanding_amount"),
            row.original.currency,
          )}
        </div>
      );
    },
    meta: {
      label: "Outstanding",
      variant: "range",
      icon: HashIcon,
      range: [0, 10000],
    },
    enableSorting: false,
    enableColumnFilter: true,
  },
  {
    id: "opened_at",
    header: "Opened at",
    accessorKey: "opened_at",
    cell: ({ row }) => {
      const value: string | null = row.getValue("opened_at");
      return (
        <div className={cn(!value && "text-muted-foreground")}>
          {value ? formatDatetime(value) : "-"}
        </div>
      );
    },
    meta: {
      label: "Opened at",
    },
    enableSorting: false,
  },
  {
    id: "voided_at",
    header: "Voided at",
    accessorKey: "voided_at",
    cell: ({ row }) => {
      const value: string | null = row.getValue("voided_at");
      return (
        <div className={cn(!value && "text-muted-foreground")}>
          {value ? formatDatetime(value) : "-"}
        </div>
      );
    },
    meta: {
      label: "Voided at",
    },
    enableSorting: false,
  },
  {
    id: "customer_email",
    header: "Customer email",
    accessorFn: (row) => row.billing_profile.email,
    cell: ({ row }) => {
      const value: string | null = row.getValue("customer_email");
      return (
        <div className={cn(!value && "text-muted-foreground")}>
          {value || "-"}
        </div>
      );
    },
    meta: {
      label: "Customer email",
    },
    enableSorting: false,
  },
  {
    id: "lines",
    header: "Lines",
    accessorKey: "lines",
    cell: ({ row }) => {
      const value: InvoiceLine[] = row.getValue("lines");
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
      <InvoiceDropdown invoice={row.original}>
        <Button
          size="icon"
          variant="ghost"
          className="data-[state=open]:bg-accent size-7"
        >
          <MoreHorizontalIcon />
        </Button>
      </InvoiceDropdown>
    ),
  },
];
