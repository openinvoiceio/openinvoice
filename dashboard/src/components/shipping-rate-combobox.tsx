import { useShippingRatesList } from "@/api/endpoints/shipping-rates/shipping-rates";
import { ShippingRatesListStatus, type ShippingRate } from "@/api/models";
import { pushModal } from "@/components/push-modals";
import {
  Command,
  CommandAction,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useDebounce } from "@/hooks/use-debounce";
import { formatAmount } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { CheckIcon, PlusIcon } from "lucide-react";
import React, { useState } from "react";

export function ShippingRateCombobox({
  selected,
  onSelect,
  className,
  children,
  ...props
}: Omit<React.ComponentProps<typeof PopoverContent>, "onSelect"> & {
  selected?: ShippingRate | null;
  onSelect?: (shippingRate: ShippingRate | null) => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const debounce = useDebounce(search, 400);
  const { data } = useShippingRatesList(
    {
      page_size: 3,
      ordering: "-created_at",
      status: ShippingRatesListStatus.active,
      ...(search ? { search: debounce } : {}),
    },
    { query: { enabled: open } },
  );

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
            placeholder="Find shipping rate"
            value={search}
            onValueChange={setSearch}
          />
          <CommandList>
            <CommandEmpty>No shipping rate found</CommandEmpty>
            <CommandGroup>
              {data?.results.map((rate) => (
                <CommandItem
                  key={rate.id}
                  value={rate.id}
                  onSelect={async (value) => {
                    setOpen(false);
                    await onSelect?.(selected?.id === value ? null : rate);
                  }}
                >
                  <div className="flex flex-1 items-center gap-2">
                    <span>{formatAmount(rate.amount, rate.currency)}</span>
                    <span className="text-muted-foreground">{rate.name}</span>
                    {rate.code && (
                      <span className="text-muted-foreground text-xs">
                        {rate.code}
                      </span>
                    )}
                  </div>
                  {rate.id === selected?.id && <CheckIcon className="ml-2" />}
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator alwaysRender={true} />
            <CommandGroup>
              <CommandAction
                onClick={() =>
                  pushModal("ShippingRateCreateSheet", {
                    name: search,
                    onSuccess: (rate: ShippingRate) => onSelect?.(rate),
                  })
                }
              >
                <PlusIcon />
                Add {search ? search : "new shipping rate"}
              </CommandAction>
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
