import { ProductCatalogStatusEnum, type Product } from "@/api/models";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { ProductDropdown } from "@/features/products/components/product-dropdown";
import { formatDatetime } from "@/lib/formatters";
import { formatPrices } from "@/lib/products.ts";
import { cn } from "@/lib/utils";
import { Link } from "@tanstack/react-router";
import type { ColumnDef } from "@tanstack/react-table";
import {
  BoxIcon,
  CalendarIcon,
  ChevronRight,
  MoreHorizontalIcon,
  SearchIcon,
} from "lucide-react";

export const columns: ColumnDef<Product>[] = [
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
    cell: ({ row }) => (
      <Link
        to="/products/$id"
        params={{ id: row.original.id }}
        className={cn(
          "group/link flex w-full items-center justify-between gap-1",
        )}
      >
        <div className="flex flex-1 items-center gap-2 truncate">
          <Avatar className="size-8 rounded-md">
            <AvatarImage
              src={row.original.image_url || undefined}
              alt="image"
            />
            <AvatarFallback className="rounded-md">
              <BoxIcon className="size-4" />
            </AvatarFallback>
          </Avatar>
          <div className="font-medium">{row.getValue("name")}</div>
          {row.original.status == ProductCatalogStatusEnum.archived && (
            <Badge variant="secondary">Archived</Badge>
          )}
        </div>
        <ChevronRight className="text-muted-foreground group-hover/link:text-foreground size-3 flex-shrink-0" />
      </Link>
    ),
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
    id: "default_price_id",
    header: "Prices",
    accessorFn: (row) => row.default_price?.id,
    cell: ({ row }) => {
      return (
        <div
          className={cn(!row.original.prices_count && "text-muted-foreground")}
        >
          {formatPrices(row.original)}
        </div>
      );
    },
    meta: {
      label: "Prices",
    },
    enableSorting: false,
  },
  {
    header: "Description",
    accessorKey: "description",
    cell: ({ row }) => {
      const value: string | undefined = row.getValue("description");
      return (
        <div
          className={cn("max-w-20 truncate", !value && "text-muted-foreground")}
        >
          {value || "-"}
        </div>
      );
    },
    meta: {
      label: "Description",
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
    id: "actions",
    size: 40,
    enableHiding: false,
    cell: ({ row }) => (
      <ProductDropdown product={row.original}>
        <Button
          size="icon"
          variant="ghost"
          className="data-[state=open]:bg-accent size-7"
        >
          <MoreHorizontalIcon />
        </Button>
      </ProductDropdown>
    ),
  },
];
