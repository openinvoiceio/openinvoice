import { CreditNoteStatusEnum } from "@/api/models";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { cva } from "class-variance-authority";
import React from "react";

const statusVariants = cva("capitalize border-transparent", {
  variants: {
    variant: {
      [CreditNoteStatusEnum.draft]:
        "bg-secondary text-secondary-foreground hover:bg-secondary/80",
      [CreditNoteStatusEnum.issued]:
        "bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30",
      [CreditNoteStatusEnum.voided]:
        "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    },
  },
  defaultVariants: {
    variant: CreditNoteStatusEnum.draft,
  },
});

export function CreditNoteBadge({
  status,
  className,
  ...props
}: React.ComponentProps<typeof Badge> & {
  status: CreditNoteStatusEnum;
}) {
  return (
    <Badge
      className={cn(statusVariants({ variant: status }), className)}
      {...props}
    >
      {status.replace("_", " ")}
    </Badge>
  );
}
