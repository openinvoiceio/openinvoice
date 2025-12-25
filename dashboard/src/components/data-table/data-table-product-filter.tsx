import { useProductsRetrieve } from "@/api/endpoints/products/products.ts";
import type { Product } from "@/api/models";
import { ProductCombobox } from "@/components/product-combobox.tsx";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import type { Column } from "@tanstack/react-table";
import { BoxIcon, XCircle } from "lucide-react";
import * as React from "react";

function parseColumnFilterValue(value: unknown) {
  if (value === null || value === undefined) {
    return undefined;
  }
  if (Array.isArray(value)) return value.join("-");
  if (typeof value === "string") return value;
  return undefined;
}

interface DataTableProductFilterProps<TData> {
  column: Column<TData, unknown>;
  title?: string;
}

export function DataTableProductFilter<TData>({
  column,
  title,
}: DataTableProductFilterProps<TData>) {
  const columnFilterValue = column.getFilterValue();

  const selectedProductId = React.useMemo<string | undefined>(() => {
    if (!columnFilterValue) return undefined;
    return parseColumnFilterValue(columnFilterValue);
  }, [columnFilterValue]);

  const { data: product } = useProductsRetrieve(selectedProductId || "", {
    query: { enabled: !!selectedProductId },
  });

  const onSelect = React.useCallback(
    async (product: Product | null) => {
      if (!product) {
        column.setFilterValue(undefined);
        return;
      }
      column.setFilterValue(product.id);
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
        {selectedProductId && (
          <>
            <Separator
              orientation="vertical"
              className="mx-0.5 data-[orientation=vertical]:h-4"
            />
            <span>{product?.name}</span>
          </>
        )}
      </span>
    );
  }, [selectedProductId, product, title]);

  return (
    <ProductCombobox
      align="start"
      selected={selectedProductId ? product : undefined}
      onSelect={onSelect}
    >
      <Button variant="outline" size="sm" className="border-dashed">
        {selectedProductId ? (
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
          <BoxIcon />
        )}
        {label}
      </Button>
    </ProductCombobox>
  );
}
