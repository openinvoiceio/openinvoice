import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area.tsx";
import { currencies } from "@/lib/currency";
import { cn } from "@/lib/utils";
import { CheckIcon } from "lucide-react";
import React, { useState } from "react";

export function CurrencyCombobox({
  selected,
  onSelect,
  className,
  children,
  ...props
}: Omit<React.ComponentProps<typeof PopoverContent>, "onSelect"> & {
  selected?: string | null;
  onSelect?: (currency: string | null) => Promise<void> | void;
}) {
  const [open, setOpen] = useState<boolean>(false);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>{children}</PopoverTrigger>
      <PopoverContent
        className={cn(
          "min-w-[var(--radix-popper-anchor-width)] p-0",
          className,
        )}
        {...props}
      >
        <Command>
          <CommandInput placeholder="Find currency" />
          <CommandList>
            <CommandEmpty>No currency found</CommandEmpty>
            <CommandGroup>
              <ScrollArea className="h-52">
                {currencies.map((currency) => (
                  <CommandItem
                    key={currency.code}
                    value={`${currency.code} ${currency.description}`}
                    onSelect={async () => {
                      setOpen(false);
                      await onSelect?.(
                        selected === currency.code ? null : currency.code,
                      );
                    }}
                  >
                    <span>{currency.code}</span>
                    <span className="text-muted-foreground">
                      {currency.description}
                    </span>
                    {currency.code === selected && (
                      <CheckIcon className="ml-auto" />
                    )}
                  </CommandItem>
                ))}
              </ScrollArea>
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
