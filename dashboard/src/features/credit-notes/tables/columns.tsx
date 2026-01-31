import type { CreditNote } from "@/api/models";
import { CreditNoteStatusEnum } from "@/api/models";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox.tsx";
import { CreditNoteBadge } from "@/features/credit-notes/components/credit-note-badge";
import { CreditNoteDropdown } from "@/features/credit-notes/components/credit-note-dropdown";
import {
  formatAmount,
  formatDate,
  formatDatetime,
  formatEnum,
} from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { Link } from "@tanstack/react-router";
import type { ColumnDef } from "@tanstack/react-table";
import {
  CalendarIcon,
  ChevronRight,
  HashIcon,
  MoreHorizontalIcon,
} from "lucide-react";

export const columns: ColumnDef<CreditNote>[] = [
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
        to="/credit-notes/$id"
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
    accessorKey: "customer",
    header: "Customer",
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
    id: "invoice",
    accessorKey: "invoice_id",
    header: "Invoice",
    cell: ({ row }) => {
      const invoiceId = row.original.invoice_id;
      if (!invoiceId) return <span className="text-muted-foreground">—</span>;

      return (
        <Link
          to="/invoices/$id"
          params={{ id: invoiceId }}
          className={cn("group/link flex items-center gap-1")}
        >
          <div className="truncate font-medium">{invoiceId}</div>
          <ChevronRight className="text-muted-foreground group-hover/link:text-foreground ml-auto size-3" />
        </Link>
      );
    },
    meta: {
      label: "Invoice",
      variant: "invoice",
    },
    enableSorting: false,
    enableColumnFilter: true,
  },
  {
    id: "status",
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <CreditNoteBadge status={row.original.status} />,
    meta: {
      label: "Status",
      variant: "multiSelect",
      options: Object.values(CreditNoteStatusEnum).map((status) => ({
        label: formatEnum(status),
        value: status,
      })),
    },
    enableSorting: false,
    enableColumnFilter: true,
  },
  {
    id: "issue_date",
    header: "Issue date",
    accessorKey: "issue_date",
    cell: ({ row }) => {
      const value: string | null = row.getValue("issue_date");
      return (
        <div className={cn(!value && "text-muted-foreground")}>
          {value ? formatDate(value) : "-"}
        </div>
      );
    },
    meta: {
      label: "Issued",
      variant: "dateRange",
      icon: CalendarIcon,
    },
    enableSorting: true,
    enableColumnFilter: true,
  },
  {
    id: "created_at",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Created" />
    ),
    accessorKey: "created_at",
    cell: ({ row }) => <div>{formatDatetime(row.getValue("created_at"))}</div>,
    meta: {
      label: "Created",
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
    cell: ({ row }) => (
      <div>
        {formatAmount(row.getValue("total_amount"), row.original.currency)}
      </div>
    ),
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
    id: "actions",
    size: 40,
    enableHiding: false,
    cell: ({ row }) => (
      <CreditNoteDropdown creditNote={row.original}>
        <Button
          size="icon"
          variant="ghost"
          className="data-[state=open]:bg-accent size-7"
        >
          <MoreHorizontalIcon />
        </Button>
      </CreditNoteDropdown>
    ),
  },
];
