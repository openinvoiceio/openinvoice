import { InvoiceStatusEnum } from "@/api/models";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { cva } from "class-variance-authority";
import React from "react";

const statusVariants = cva("capitalize border-transparent", {
  variants: {
    variant: {
      draft: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
      open: "bg-blue-500/20 text-blue-500 hover:bg-blue/30",
      paid: "bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30",
      voided: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    },
  },
  defaultVariants: {
    variant: "draft",
  },
});

export function InvoiceBadge({
  status,
  className,
  ...props
}: React.ComponentProps<typeof Badge> & {
  status: InvoiceStatusEnum;
}) {
  return (
    <Badge
      className={cn(statusVariants({ variant: status }), className)}
      {...props}
    >
      {status}
    </Badge>
  );
}
