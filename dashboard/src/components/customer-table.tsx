import type { Customer } from "@/api/models";
import { CustomerDropdown } from "@/components/customer-dropdown";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { formatDatetime } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { Link } from "@tanstack/react-router";
import type { ColumnDef } from "@tanstack/react-table";
import {
  CalendarIcon,
  ChevronRight,
  MoreHorizontalIcon,
  SearchIcon,
  UserIcon,
} from "lucide-react";

export const columns: ColumnDef<Customer>[] = [
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
        to="/customers/$id"
        params={{ id: row.original.id }}
        className={cn(
          "group/link flex w-full items-center justify-between gap-1",
        )}
      >
        <div className="flex flex-1 items-center gap-2 truncate">
          <Avatar className="size-8 rounded-md">
            <AvatarImage src={row.original.logo_url || undefined} alt="logo" />
            <AvatarFallback className="rounded-md">
              <UserIcon className="size-4" />
            </AvatarFallback>
          </Avatar>
          <div className="font-medium">{row.getValue("name")}</div>
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
    header: "Email",
    accessorKey: "email",
    cell: ({ row }) => {
      const email: string | undefined = row.getValue("email");
      return (
        <div className={cn(!email && "text-muted-foreground")}>
          {email || "-"}
        </div>
      );
    },
    meta: {
      label: "Email",
    },
    enableSorting: false,
  },
  {
    header: "Phone",
    accessorKey: "phone",
    cell: ({ row }) => {
      const phone: string | undefined = row.getValue("phone");
      return (
        <div className={cn(!phone && "text-muted-foreground")}>
          {phone || "-"}
        </div>
      );
    },
    meta: {
      label: "Phone",
    },
    enableSorting: false,
  },
  {
    header: "Currency",
    accessorKey: "currency",
    cell: ({ row }) => {
      const currency: string | undefined = row.getValue("currency");
      return (
        <div className={cn(!currency && "text-muted-foreground")}>
          {currency || "-"}
        </div>
      );
    },
    meta: {
      label: "Currency",
    },
    enableSorting: false,
  },
  {
    header: "Net Payment Term",
    accessorKey: "net_payment_term",
    cell: ({ row }) => {
      const value: string | undefined = row.getValue("net_payment_term");
      return (
        <div className={cn(!value && "text-muted-foreground")}>
          {value ? `${value} days` : "-"}
        </div>
      );
    },
    meta: {
      label: "Net Payment Term",
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
      <CustomerDropdown customer={row.original}>
        <Button
          size="icon"
          variant="ghost"
          className="data-[state=open]:bg-accent size-7"
        >
          <MoreHorizontalIcon />
        </Button>
      </CustomerDropdown>
    ),
  },
];
