import { ProductCatalogStatusEnum, type TaxRate } from "@/api/models";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { TaxRateDropdown } from "@/features/tax-rates/components/tax-rate-dropdown";
import {
  formatCountry,
  formatDatetime,
  formatPercentage,
} from "@/lib/formatters";
import { cn } from "@/lib/utils";
import type { ColumnDef } from "@tanstack/react-table";
import { CalendarIcon, MoreHorizontalIcon, SearchIcon } from "lucide-react";

export const columns: ColumnDef<TaxRate>[] = [
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
          {row.original.status == ProductCatalogStatusEnum.archived && (
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
    header: "Percentage",
    accessorKey: "percentage",
    cell: ({ row }) => {
      const value: string = row.getValue("percentage");
      return <div>{formatPercentage(value)}</div>;
    },
    meta: {
      label: "Percentage",
    },
    enableSorting: false,
  },
  {
    header: "Country",
    accessorKey: "country",
    cell: ({ row }) => {
      const value: string | null = row.getValue("country");
      return <div>{value ? formatCountry(value) : "-"}</div>;
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
      <TaxRateDropdown taxRate={row.original}>
        <Button
          size="icon"
          variant="ghost"
          className="data-[state=open]:bg-accent size-7"
        >
          <MoreHorizontalIcon />
        </Button>
      </TaxRateDropdown>
    ),
  },
];
