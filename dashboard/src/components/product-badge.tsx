import { Badge } from "@/components/ui/badge";
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
  isActive,
  className,
  ...props
}: React.ComponentProps<typeof Badge> & {
  isActive: boolean;
}) {
  return (
    <Badge
      className={cn(
        statusVariants({ variant: isActive ? "active" : "archived" }),
        className,
      )}
      {...props}
    >
      {isActive ? "Active" : "Archived"}
    </Badge>
  );
}
