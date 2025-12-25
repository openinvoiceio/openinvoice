import { cn } from "@/lib/utils";
import { cva, type VariantProps } from "class-variance-authority";
import { LoaderCircleIcon } from "lucide-react";
import React from "react";

const spinnerVariants = cva("animate-spin text-primary-foreground", {
  variants: {
    variant: {
      default: "",
      destructive: "text-destructive-foreground",
      outline: "text-muted-foreground",
      secondary: "text-secondary-foreground",
      ghost: "",
      link: "text-primary",
      background: "text-primary",
      glow: "text-primary",
    },
    size: {
      xsmall: "size-4",
      small: "size-6",
      medium: "size-8",
      large: "size-12",
    },
  },
  defaultVariants: {
    variant: "default",
    size: "xsmall",
  },
});

interface SpinnerContentProps extends VariantProps<typeof spinnerVariants> {
  className?: string;
  children?: React.ReactNode;
}

export function Spinner({
  size,
  variant,
  children,
  className,
}: SpinnerContentProps) {
  return (
    <span className="flex h-full flex-col items-center justify-center">
      <LoaderCircleIcon
        className={cn(spinnerVariants({ size, variant }), className)}
      />
      {children}
    </span>
  );
}
