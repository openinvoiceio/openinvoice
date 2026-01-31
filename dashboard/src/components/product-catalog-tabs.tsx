import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BoxIcon, PercentIcon, TagIcon, TruckIcon } from "lucide-react";
import * as React from "react";

type ProductCatalogTabsProps = Pick<
  React.ComponentProps<typeof Tabs>,
  "defaultValue" | "onValueChange" | "children" | "className"
>;

function ProductCatalogTabs({
  defaultValue,
  onValueChange,
  children,
  className,
}: ProductCatalogTabsProps) {
  return (
    <Tabs
      defaultValue={defaultValue}
      onValueChange={onValueChange}
      className={className}
    >
      <TabsList>
        <TabsTrigger value="/products">
          <BoxIcon />
          Products
        </TabsTrigger>
        <TabsTrigger value="/coupons">
          <TagIcon />
          Coupons
        </TabsTrigger>
        <TabsTrigger value="/tax-rates">
          <PercentIcon />
          Tax rates
        </TabsTrigger>
        <TabsTrigger value="/shipping-rates">
          <TruckIcon />
          Shipping rates
        </TabsTrigger>
      </TabsList>
      {children}
    </Tabs>
  );
}

export { ProductCatalogTabs };
