import { DataTableCustomerFilter } from "@/components/data-table/data-table-customer-filter.tsx";
import { DataTableDateFilter } from "@/components/data-table/data-table-date-filter";
import { DataTableFacetedFilter } from "@/components/data-table/data-table-faceted-filter";
import { DataTableInvoiceFilter } from "@/components/data-table/data-table-invoice-filter.tsx";
import { DataTableProductFilter } from "@/components/data-table/data-table-product-filter.tsx";
import { DataTableSliderFilter } from "@/components/data-table/data-table-slider-filter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { Column, Table } from "@tanstack/react-table";
import { X } from "lucide-react";
import * as React from "react";

interface DataTableToolbarProps<TData> extends React.ComponentProps<"div"> {
  table: Table<TData>;
}

export function DataTableToolbar<TData>({
  table,
  children,
  className,
  ...props
}: DataTableToolbarProps<TData>) {
  return (
    <div
      role="toolbar"
      aria-orientation="horizontal"
      className={cn("flex w-full items-start gap-2 py-1", className)}
      {...props}
    >
      {children}
    </div>
  );
}

export function DataTableFilterList<TData>({
  table,
  className,
  children,
  ...props
}: React.ComponentProps<"div"> & {
  table: Table<TData>;
}) {
  const isFiltered = table.getState().columnFilters.length > 0;

  const columns = React.useMemo(
    () => table.getAllColumns().filter((column) => column.getCanFilter()),
    [table],
  );

  const onReset = React.useCallback(() => {
    table.resetColumnFilters();
  }, [table]);

  return (
    <div
      className={cn("flex flex-1 flex-wrap items-center gap-2", className)}
      {...props}
    >
      {children}
      {columns.map((column) => (
        <DataTableToolbarFilter key={column.id} column={column} />
      ))}
      {isFiltered && (
        <Button
          aria-label="Reset filters"
          variant="outline"
          size="sm"
          className="border-dashed"
          onClick={onReset}
        >
          <X />
          Reset
        </Button>
      )}
    </div>
  );
}

interface DataTableToolbarFilterProps<TData> {
  column: Column<TData>;
}

function DataTableToolbarFilter<TData>({
  column,
}: DataTableToolbarFilterProps<TData>) {
  {
    const columnMeta = column.columnDef.meta;

    const onFilterRender = React.useCallback(() => {
      if (!columnMeta?.variant) return null;

      switch (columnMeta.variant) {
        case "text":
          return (
            <Input
              placeholder={columnMeta.placeholder ?? columnMeta.label}
              value={(column.getFilterValue() as string) ?? ""}
              onChange={(event) => column.setFilterValue(event.target.value)}
              className="h-8 w-40 lg:w-56"
            />
          );

        case "number":
          return (
            <div className="relative">
              <Input
                type="number"
                inputMode="numeric"
                placeholder={columnMeta.placeholder ?? columnMeta.label}
                value={(column.getFilterValue() as string) ?? ""}
                onChange={(event) => column.setFilterValue(event.target.value)}
                className={cn("h-8 w-[120px]", columnMeta.unit && "pr-8")}
              />
              {columnMeta.unit && (
                <span className="bg-accent text-muted-foreground absolute top-0 right-0 bottom-0 flex items-center rounded-r-md px-2 text-sm">
                  {columnMeta.unit}
                </span>
              )}
            </div>
          );

        case "range":
          return (
            <DataTableSliderFilter
              column={column}
              title={columnMeta.label ?? column.id}
            />
          );

        case "date":
        case "dateRange":
          return (
            <DataTableDateFilter
              column={column}
              title={columnMeta.label ?? column.id}
              multiple={columnMeta.variant === "dateRange"}
            />
          );

        case "select":
        case "multiSelect":
          return (
            <DataTableFacetedFilter
              column={column}
              title={columnMeta.label ?? column.id}
              options={columnMeta.options ?? []}
              multiple={columnMeta.variant === "multiSelect"}
            />
          );

        case "customer":
          return (
            <DataTableCustomerFilter
              column={column}
              title={columnMeta.label ?? column.id}
            />
          );

        case "invoice":
          return (
            <DataTableInvoiceFilter
              column={column}
              title={columnMeta.label ?? column.id}
            />
          );

        case "product":
          return (
            <DataTableProductFilter
              column={column}
              title={columnMeta.label ?? column.id}
            />
          );

        default:
          return null;
      }
    }, [column, columnMeta]);

    return onFilterRender();
  }
}
