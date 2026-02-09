import { useAccountsAddressesList } from "@/api/endpoints/accounts/accounts";
import type { AddressDetail } from "@/api/models";
import { Button } from "@/components/ui/button";
import {
  Command,
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
import { formatCountry } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { CheckIcon, ChevronsUpDownIcon, MapPinIcon } from "lucide-react";
import { useMemo, useState } from "react";

function getAddressLabel(address: AddressDetail) {
  const parts = [
    address.line1,
    address.line2,
    address.locality,
    address.state,
    address.postal_code,
    address.country ? formatCountry(address.country) : null,
  ].filter(Boolean);
  return parts.join(", ") || "Untitled address";
}

export function AccountAddressCombobox({
  accountId,
  value,
  onChange,
  placeholder = "Select address",
  disabled,
  allowClear = true,
  className,
}: {
  accountId: string;
  value: string | null;
  onChange: (value: string | null) => void;
  placeholder?: string;
  disabled?: boolean;
  allowClear?: boolean;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const { data } = useAccountsAddressesList(
    accountId,
    { page_size: 100 },
    { query: { enabled: open && !!accountId } },
  );
  const addresses = data?.results ?? [];
  const selected = useMemo(
    () => addresses.find((address) => address.id === value) ?? null,
    [addresses, value],
  );
  const selectedLabel = selected ? getAddressLabel(selected) : placeholder;

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
              !selected && "text-muted-foreground",
            )}
          >
            {selectedLabel}
          </span>
          <ChevronsUpDownIcon className="text-muted-foreground size-4 shrink-0" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="min-w-[var(--radix-popper-anchor-width)] p-0">
        <Command>
          <CommandInput placeholder="Search addresses" />
          <CommandList>
            <CommandEmpty>No addresses found.</CommandEmpty>
            <CommandGroup>
              {addresses.map((address) => {
                const isSelected = address.id === value;
                return (
                  <CommandItem
                    key={address.id}
                    value={getAddressLabel(address)}
                    onSelect={() => {
                      onChange(isSelected ? null : address.id);
                      setOpen(false);
                    }}
                  >
                    <span>{getAddressLabel(address)}</span>
                    {isSelected && <CheckIcon className="ml-auto" />}
                  </CommandItem>
                );
              })}
            </CommandGroup>
            {allowClear && addresses.length > 0 && <CommandSeparator />}
            <CommandGroup>
              {allowClear && (
                <CommandItem
                  value="none"
                  onSelect={() => {
                    onChange(null);
                    setOpen(false);
                  }}
                >
                  <MapPinIcon className="text-muted-foreground" />
                  <span>No address</span>
                  {!selected && <CheckIcon className="ml-auto" />}
                </CommandItem>
              )}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
