import { useCustomersRetrieve } from "@/api/endpoints/customers/customers.ts";
import type { Customer } from "@/api/models";
import { CustomerCombobox } from "@/components/customer-combobox.tsx";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import type { Column } from "@tanstack/react-table";
import { UserIcon, XCircle } from "lucide-react";
import * as React from "react";

function parseColumnFilterValue(value: unknown) {
  if (value === null || value === undefined) {
    return undefined;
  }
  if (Array.isArray(value)) return value.join("-");
  if (typeof value === "string") return value;
  return undefined;
}

interface DataTableCustomerFilterProps<TData> {
  column: Column<TData, unknown>;
  title?: string;
}

export function DataTableCustomerFilter<TData>({
  column,
  title,
}: DataTableCustomerFilterProps<TData>) {
  const columnFilterValue = column.getFilterValue();

  const selectedCustomerId = React.useMemo<string | undefined>(() => {
    if (!columnFilterValue) return undefined;
    return parseColumnFilterValue(columnFilterValue);
  }, [columnFilterValue]);

  const { data: customer } = useCustomersRetrieve(selectedCustomerId || "", {
    query: { enabled: !!selectedCustomerId },
  });

  const onSelect = React.useCallback(
    async (customer: Customer | null) => {
      if (!customer) {
        column.setFilterValue(undefined);
        return;
      }
      column.setFilterValue(customer.id);
    },
    [column],
  );

  const onReset = React.useCallback(
    (event: React.MouseEvent) => {
      event.stopPropagation();
      column.setFilterValue(undefined);
    },
    [column],
  );

  const label = React.useMemo(() => {
    return (
      <span className="flex items-center gap-2">
        <span>{title}</span>
        {selectedCustomerId && (
          <>
            <Separator
              orientation="vertical"
              className="mx-0.5 data-[orientation=vertical]:h-4"
            />
            <span>{customer?.name}</span>
          </>
        )}
      </span>
    );
  }, [selectedCustomerId, customer, title]);

  return (
    <CustomerCombobox
      align="start"
      selected={selectedCustomerId ? customer : undefined}
      onSelect={onSelect}
    >
      <Button variant="outline" size="sm" className="border-dashed">
        {selectedCustomerId ? (
          <div
            role="button"
            aria-label={`Clear ${title} filter`}
            tabIndex={0}
            onClick={onReset}
            className="focus-visible:ring-ring rounded-sm opacity-70 transition-opacity hover:opacity-100 focus-visible:ring-1 focus-visible:outline-none"
          >
            <XCircle />
          </div>
        ) : (
          <UserIcon />
        )}
        {label}
      </Button>
    </CustomerCombobox>
  );
}
