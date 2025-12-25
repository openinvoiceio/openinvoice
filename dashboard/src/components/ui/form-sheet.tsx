import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import React from "react";

export function FormSheetContent({
  children,
  className,
  ...props
}: React.ComponentProps<typeof SheetContent>) {
  return (
    <SheetContent className={cn("max-h-screen gap-0", className)} {...props}>
      {children}
    </SheetContent>
  );
}

export function FormSheetHeader({
  children,
  className,
  ...props
}: React.ComponentProps<typeof SheetHeader>) {
  return (
    <SheetHeader
      className={cn("bg-background sticky top-0 border-b", className)}
      {...props}
    >
      {children}
    </SheetHeader>
  );
}

export function FormSheetFooter({
  children,
  className,
  ...props
}: React.ComponentProps<typeof SheetFooter>) {
  return (
    <SheetFooter
      className={cn("bg-background sticky bottom-0 border-t", className)}
      {...props}
    >
      {children}
    </SheetFooter>
  );
}

export function FormSheetFooterInfo({
  children,
  className,
  ...props
}: React.ComponentProps<"p">) {
  return (
    <p className={cn("text-muted-foreground/70 text-xs", className)} {...props}>
      {children}
    </p>
  );
}

function FormSheetGroup({
  children,
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div className={cn("grid gap-4 p-4", className)} {...props}>
      {children}
    </div>
  );
}

function FormSheetGroupTitle({
  children,
  className,
  ...props
}: React.ComponentProps<"h3">) {
  return (
    <h3 className={cn("pb-2 font-semibold", className)} {...props}>
      {children}
    </h3>
  );
}

export {
  SheetTitle as FormSheetTitle,
  SheetDescription as FormSheetDescription,
  SheetTrigger as FormSheetTrigger,
  Sheet as FormSheet,
  FormSheetGroup,
  FormSheetGroupTitle,
};
