import { useShippingProfilesList } from "@/api/endpoints/shipping-profiles/shipping-profiles";
import type { ShippingProfile } from "@/api/models";
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
import { useDebounce } from "@/hooks/use-debounce";
import { cn } from "@/lib/utils";
import { CheckIcon } from "lucide-react";
import React, { useMemo, useState } from "react";

function getProfileLabel(profile: ShippingProfile) {
  return profile.name || "Untitled";
}

export function ShippingProfileCombobox({
  customerId,
  selected,
  onSelect,
  className,
  children,
  ...props
}: Omit<React.ComponentProps<typeof PopoverContent>, "onSelect"> & {
  customerId?: string;
  selected?: ShippingProfile | null;
  onSelect?: (profile: ShippingProfile | null) => Promise<void> | void;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const debounce = useDebounce(search, 400);
  const { data } = useShippingProfilesList(
    {
      customer_id: customerId,
      page_size: 8,
      ordering: "-created_at",
      ...(debounce ? { search: debounce } : {}),
    },
    { query: { enabled: open && !!customerId } },
  );
  const profiles = useMemo(() => data?.results ?? [], [data?.results]);

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
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Find shipping profile"
            value={search}
            onValueChange={setSearch}
          />
          <CommandList>
            <CommandEmpty>No shipping profile found</CommandEmpty>
            <CommandGroup>
              {profiles.map((profile) => (
                <CommandItem
                  key={profile.id}
                  value={profile.id}
                  onSelect={async () => {
                    setOpen(false);
                    await onSelect?.(profile);
                  }}
                >
                  <span>{getProfileLabel(profile)}</span>
                  {profile.phone && (
                    <span className="text-muted-foreground">
                      {profile.phone}
                    </span>
                  )}
                  {profile.id === selected?.id && (
                    <CheckIcon className="ml-auto" />
                  )}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
