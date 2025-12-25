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
import { countries } from "@/lib/country";
import { cn } from "@/lib/utils";
import { CheckIcon } from "lucide-react";
import React, { useState } from "react";

export function CountryCombobox({
  selected,
  onSelect,
  className,
  children,
  ...props
}: Omit<React.ComponentProps<typeof PopoverContent>, "onSelect"> & {
  selected?: string | null;
  onSelect?: (country: string | null) => Promise<void> | void;
}) {
  const [open, setOpen] = useState(false);

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
        <Command
          filter={(value, search, keywords) => {
            const raw = search.trim();
            const s = raw.toLowerCase();

            // Iso code match
            if (/^[A-Z]{2}$/.test(raw)) {
              // "value" is country name, "keywords" contains ["PL"]
              return keywords?.some((k) => k === raw) ? 1 : 0;
            }

            // Regular name-based search
            if (!s) return 1;

            const name = value.toLowerCase();

            // strong match: name starts with search
            if (name.startsWith(s)) return 1;

            // fallback match: name contains search
            if (name.includes(s)) return 0.8;

            // fallback: match by code substring (e.g. "p" matches "PL")
            if (keywords?.some((k) => k.toLowerCase().includes(s))) return 0.7;

            return 0;
          }}
        >
          <CommandInput placeholder="Find country" />
          <CommandList>
            <CommandEmpty>No country found</CommandEmpty>
            <CommandGroup>
              <ScrollArea className="h-52">
                {countries.map((country) => (
                  <CommandItem
                    key={country.code}
                    value={country.name}
                    keywords={[country.code]}
                    onSelect={async () => {
                      setOpen(false);
                      await onSelect?.(
                        selected === country.code ? null : country.code,
                      );
                    }}
                  >
                    <span>{country.name}</span>
                    {country.code === selected && (
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
