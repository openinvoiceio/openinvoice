import type { ProductCatalogStatusEnum } from "@/api/models";
import { Badge } from "@/components/ui/badge";
import { formatEnum } from "@/lib/formatters.ts";
import { cn } from "@/lib/utils";
import { cva } from "class-variance-authority";
import React from "react";

const statusVariants = cva("capitalize border-transparent", {
  variants: {
    variant: {
      active: "bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30",
      archived: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    },
  },
  defaultVariants: {
    variant: "active",
  },
});

export function ProductBadge({
  status,
  className,
  ...props
}: React.ComponentProps<typeof Badge> & {
  status: ProductCatalogStatusEnum;
}) {
  return (
    <Badge
      className={cn(statusVariants({ variant: status }), className)}
      {...props}
    >
      {formatEnum(status)}
    </Badge>
  );
}
