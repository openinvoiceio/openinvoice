import { useTaxRatesList } from "@/api/endpoints/tax-rates/tax-rates";
import { TaxRatesListStatus, type TaxRate } from "@/api/models";
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
import { formatPercentage } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { CheckIcon, PlusIcon } from "lucide-react";
import React, { useState } from "react";

export function TaxRateCombobox({
  selected,
  onSelect,
  status,
  className,
  children,
  ...props
}: Omit<React.ComponentProps<typeof PopoverContent>, "onSelect"> & {
  selected?: TaxRate | null;
  onSelect?: (taxRate: TaxRate | null) => Promise<void>;
  status?: TaxRatesListStatus;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const debounce = useDebounce(search, 400);
  const { data } = useTaxRatesList(
    {
      page_size: 3,
      ordering: "-created_at",
      ...(search ? { search: debounce } : {}),
      ...(status ? { status } : {}),
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
            placeholder="Find tax rate"
            value={search}
            onValueChange={setSearch}
          />
          <CommandList>
            <CommandEmpty>No tax rate found</CommandEmpty>
            <CommandGroup>
              {data?.results.map((tax) => (
                <CommandItem
                  key={tax.id}
                  value={tax.id}
                  onSelect={async (value) => {
                    setOpen(false);
                    await onSelect?.(selected?.id === value ? null : tax);
                  }}
                >
                  <span>{tax.name}</span>
                  <span className="text-muted-foreground">
                    {formatPercentage(tax.percentage)}
                  </span>
                  {tax.id === selected?.id && <CheckIcon className="ml-auto" />}
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator alwaysRender={true} />
            <CommandGroup>
              <CommandAction
                onClick={() =>
                  pushModal("TaxRateCreateSheet", {
                    name: search,
                    onSuccess: (tax: TaxRate) => onSelect?.(tax),
                  })
                }
              >
                <PlusIcon />
                Add {search ? search : "new tax rate"}
              </CommandAction>
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
