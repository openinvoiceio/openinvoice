import type { ShippingRate } from "@/api/models";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import { ShippingRateDropdown } from "@/components/shipping-rate-dropdown.tsx";
import { Badge } from "@/components/ui/badge.tsx";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { formatAmount, formatDatetime, formatEnum } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import type { ColumnDef } from "@tanstack/react-table";
import { CalendarIcon, MoreHorizontalIcon, SearchIcon } from "lucide-react";

export const columns: ColumnDef<ShippingRate>[] = [
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
    header: "Name",
    accessorKey: "name",
    cell: ({ row }) => {
      const value: string | undefined = row.getValue("name");
      return (
        <div className="flex min-w-40 gap-2 font-medium">
          {value || "-"}
          {!row.original.is_active && (
            <Badge variant="secondary">Archived</Badge>
          )}
        </div>
      );
    },
    meta: {
      label: "Name",
      placeholder: "Search...",
      variant: "text",
      icon: SearchIcon,
    },
    enableHiding: false,
    enableSorting: false,
    enableColumnFilter: true,
  },
  {
    header: "Amount",
    accessorKey: "amount",
    cell: ({ row }) => {
      const value: string = row.getValue("amount");
      return <div>{formatAmount(value, row.original.currency)}</div>;
    },
    meta: {
      label: "Amount",
    },
    enableSorting: false,
  },
  {
    header: "Tax policy",
    accessorKey: "tax_policy",
    cell: ({ row }) => {
      const value: string = row.getValue("tax_policy");
      return <div>{formatEnum(value)}</div>;
    },
    meta: { label: "Tax policy" },
    enableSorting: false,
  },
  {
    header: "Code",
    accessorKey: "code",
    cell: ({ row }) => {
      const value: string | null = row.getValue("code");
      return <div>{value || "-"}</div>;
    },
    meta: { label: "Country" },
    enableSorting: false,
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
    meta: { label: "Last updated" },
    enableSorting: false,
  },
  {
    id: "actions",
    size: 40,
    enableHiding: false,
    cell: ({ row }) => (
      <ShippingRateDropdown shippingRate={row.original}>
        <Button
          size="icon"
          variant="ghost"
          className="data-[state=open]:bg-accent size-7"
        >
          <MoreHorizontalIcon />
        </Button>
      </ShippingRateDropdown>
    ),
  },
];
