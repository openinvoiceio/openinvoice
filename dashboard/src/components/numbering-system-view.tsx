import type { NumberingSystem } from "@/api/models";
import { cn } from "@/lib/utils";
import { Repeat2Icon } from "lucide-react";
import React from "react";

export function NumberingSystemView({
  numberingSystem,
  className,
  ...props
}: React.ComponentProps<"div"> & {
  numberingSystem?: NumberingSystem;
}) {
  if (!numberingSystem) return <span>-</span>;

  return (
    <div className={cn("flex gap-2", className)} {...props}>
      <span>{numberingSystem.description}</span>
      <div className="text-muted-foreground flex items-center gap-0.5 capitalize">
        <Repeat2Icon className="size-4" />
        <span>{numberingSystem.reset_interval}</span>
      </div>
    </div>
  );
}
