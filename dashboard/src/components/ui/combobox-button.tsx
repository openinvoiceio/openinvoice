import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils.ts";
import { ChevronsUpDownIcon } from "lucide-react";
import React from "react";

function ComboboxButton({
  className,
  type,
  children,
  ...props
}: React.ComponentProps<typeof Button>) {
  return (
    <Button
      type={type || "button"}
      variant="outline"
      className={cn("font-normal", className)}
      {...props}
    >
      {children}
      <ChevronsUpDownIcon className="text-muted-foreground ml-auto" />
    </Button>
  );
}

function ComboboxButtonAvatar({
  src,
  className,
  children,
  ...props
}: React.ComponentProps<typeof Avatar> & {
  src?: string | null;
}) {
  return (
    <Avatar
      className={cn("size-5 rounded-sm bg-transparent", className)}
      {...props}
    >
      <AvatarImage src={src || undefined} />
      <AvatarFallback className="rounded-sm bg-transparent [&>svg]:size-4">
        {children}
      </AvatarFallback>
    </Avatar>
  );
}

export { ComboboxButton, ComboboxButtonAvatar };
