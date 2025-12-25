import { type Price } from "@/api/models";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import { PriceDropdown } from "@/components/price-dropdown";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { formatDatetime, formatEnum } from "@/lib/formatters";
import { formatPrice } from "@/lib/products.ts";
import { cn } from "@/lib/utils";
import type { ColumnDef } from "@tanstack/react-table";
import { MoreHorizontalIcon } from "lucide-react";

export const columns: ColumnDef<Price>[] = [
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
    header: "Amount",
    accessorKey: "amount",
    cell: ({ row }) => {
      return (
        <div className="flex min-w-40 gap-2">
          {formatPrice(row.original)}
          {row.original.product.default_price_id === row.original.id && (
            <Badge>Default</Badge>
          )}
          {!row.original.is_active && (
            <Badge variant="secondary">Archived</Badge>
          )}
        </div>
      );
    },
    meta: {
      label: "Amount",
    },
    enableSorting: false,
  },
  {
    header: "Model",
    accessorKey: "model",
    cell: ({ row }) => {
      const value: string = row.getValue("model");
      return <div>{formatEnum(value)}</div>;
    },
  },
  {
    header: "Code",
    accessorKey: "code",
    cell: ({ row }) => {
      const value: string | undefined = row.getValue("code");
      return (
        <div
          className={cn("max-w-20 truncate", !value && "text-muted-foreground")}
        >
          {value || "-"}
        </div>
      );
    },
    meta: {
      label: "Code",
    },
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
    },
    enableSorting: true,
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
    id: "actions",
    size: 40,
    enableHiding: false,
    cell: ({ row }) => (
      <PriceDropdown price={row.original}>
        <Button
          size="icon"
          variant="ghost"
          className="data-[state=open]:bg-accent size-7"
        >
          <MoreHorizontalIcon />
        </Button>
      </PriceDropdown>
    ),
  },
];
