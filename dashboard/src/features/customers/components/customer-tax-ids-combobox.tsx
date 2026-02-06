import { useCustomersRetrieve } from "@/api/endpoints/customers/customers";
import type { TaxId } from "@/api/models";
import { Button } from "@/components/ui/button";
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
import { formatCountry, formatTaxIdType } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { CheckIcon, ChevronsUpDownIcon } from "lucide-react";
import { useMemo, useState } from "react";

function getTaxIdLabel(taxId: TaxId) {
  return `${formatTaxIdType(taxId.type)} ${taxId.number}`;
}

function getTaxIdHint(taxId: TaxId) {
  return taxId.country ? formatCountry(taxId.country) : "";
}

export function CustomerTaxIdsCombobox({
  customerId,
  value,
  onChange,
  placeholder = "Select tax ids",
  multiple = false,
  disabled,
  className,
}: {
  customerId: string;
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  multiple?: boolean;
  disabled?: boolean;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const { data: customer } = useCustomersRetrieve(customerId, {
    query: { enabled: !!customerId },
  });
  const taxIds = customer?.tax_ids ?? [];
  const selected = useMemo(
    () => taxIds.filter((taxId) => value.includes(taxId.id)),
    [taxIds, value],
  );
  const selectedLabel = useMemo(() => {
    if (selected.length === 0) return placeholder;
    return selected.map(getTaxIdLabel).join(", ");
  }, [placeholder, selected]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn("w-full justify-between gap-2", className)}
        >
          <span
            className={cn(
              "truncate text-left",
              selected.length === 0 && "text-muted-foreground",
            )}
          >
            {selectedLabel}
          </span>
          <ChevronsUpDownIcon className="text-muted-foreground size-4 shrink-0" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="min-w-[var(--radix-popper-anchor-width)] p-0">
        <Command>
          <CommandInput placeholder="Search tax ids" />
          <CommandList>
            <CommandEmpty>No tax ids found.</CommandEmpty>
            <CommandGroup>
              {taxIds.map((taxId) => {
                const isSelected = value.includes(taxId.id);
                return (
                  <CommandItem
                    key={taxId.id}
                    value={`${getTaxIdLabel(taxId)} ${getTaxIdHint(taxId)}`}
                    onSelect={() => {
                      if (multiple) {
                        const next = isSelected
                          ? value.filter((id) => id !== taxId.id)
                          : [...value, taxId.id];
                        onChange(next);
                        return;
                      }

                      onChange([taxId.id]);
                      setOpen(false);
                    }}
                  >
                    <span>{taxId.number}</span>
                    <span className="text-muted-foreground">
                      {formatTaxIdType(taxId.type)}
                    </span>
                    {isSelected && <CheckIcon className="ml-auto" />}
                  </CommandItem>
                );
              })}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
