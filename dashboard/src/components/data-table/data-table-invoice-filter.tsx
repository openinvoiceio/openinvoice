import { useInvoicesRetrieve } from "@/api/endpoints/invoices/invoices.ts";
import type { Invoice } from "@/api/models";
import { InvoiceCombobox } from "@/components/invoice-combobox.tsx";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import type { Column } from "@tanstack/react-table";
import { FileTextIcon, XCircle } from "lucide-react";
import * as React from "react";

function parseColumnFilterValue(value: unknown) {
  if (value === null || value === undefined) {
    return undefined;
  }
  if (Array.isArray(value)) return value.join("-");
  if (typeof value === "string") return value;
  return undefined;
}

interface DataTableInvoiceFilterProps<TData> {
  column: Column<TData, unknown>;
  title?: string;
}

export function DataTableInvoiceFilter<TData>({
  column,
  title,
}: DataTableInvoiceFilterProps<TData>) {
  const columnFilterValue = column.getFilterValue();

  const selectedInvoiceId = React.useMemo<string | undefined>(() => {
    if (!columnFilterValue) return undefined;
    return parseColumnFilterValue(columnFilterValue);
  }, [columnFilterValue]);

  const { data: invoice } = useInvoicesRetrieve(selectedInvoiceId || "", {
    query: { enabled: !!selectedInvoiceId },
  });

  const onSelect = React.useCallback(
    async (selected: Invoice | null) => {
      if (!selected) {
        column.setFilterValue(undefined);
        return;
      }
      column.setFilterValue(selected.id);
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
        {selectedInvoiceId && (
          <>
            <Separator
              orientation="vertical"
              className="mx-0.5 data-[orientation=vertical]:h-4"
            />
            <span>{invoice?.number}</span>
          </>
        )}
      </span>
    );
  }, [selectedInvoiceId, invoice?.number, title]);

  return (
    <InvoiceCombobox
      align="start"
      selected={selectedInvoiceId ? invoice : undefined}
      onSelect={onSelect}
    >
      <Button variant="outline" size="sm" className="border-dashed">
        {selectedInvoiceId ? (
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
          <FileTextIcon />
        )}
        {label}
      </Button>
    </InvoiceCombobox>
  );
}
