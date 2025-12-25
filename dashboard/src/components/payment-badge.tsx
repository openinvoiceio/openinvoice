import { PaymentStatusEnum } from "@/api/models";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { cva } from "class-variance-authority";
import React from "react";

const statusVariants = cva("capitalize border-transparent", {
  variants: {
    variant: {
      succeeded: "bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30",
      pending: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
      failed: "bg-destructive/20 text-destructive hover:bg-destructive/30",
      rejected: "bg-destructive/20 text-destructive hover:bg-destructive/30",
    },
  },
  defaultVariants: {
    variant: "pending",
  },
});

export function PaymentBadge({
  status,
  className,
  ...props
}: React.ComponentProps<typeof Badge> & { status: PaymentStatusEnum }) {
  return (
    <Badge
      className={cn(statusVariants({ variant: status }), className)}
      {...props}
    >
      {status}
    </Badge>
  );
}
