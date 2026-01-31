import { useCustomersList } from "@/api/endpoints/customers/customers";
import type { Customer } from "@/api/models";
import { pushModal } from "@/components/push-modals";
import {
  Command,
  CommandAction,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandItemAvatar,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useDebounce } from "@/hooks/use-debounce";
import { cn } from "@/lib/utils";
import { CheckIcon, PlusIcon, UserIcon } from "lucide-react";
import React, { useState } from "react";

export function CustomerCombobox({
  selected,
  onSelect,
  className,
  children,
  ...props
}: Omit<React.ComponentProps<typeof PopoverContent>, "onSelect"> & {
  selected?: Customer | null;
  onSelect?: (customer: Customer | null) => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const debounce = useDebounce(search, 400);
  const { data } = useCustomersList(
    {
      page_size: 3,
      ordering: "-created_at",
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
            placeholder="Find customer"
            value={search}
            onValueChange={setSearch}
          />
          <CommandList>
            <CommandEmpty>No customer found</CommandEmpty>
            <CommandGroup>
              {data?.results.map((customer) => (
                <CommandItem
                  key={customer.id}
                  value={customer.id}
                  onSelect={async (value) => {
                    setOpen(false);
                    await onSelect?.(selected?.id === value ? null : customer);
                  }}
                >
                  <CommandItemAvatar src={customer.logo_url}>
                    <UserIcon />
                  </CommandItemAvatar>
                  <span>{customer.name}</span>
                  {customer.id === selected?.id && (
                    <CheckIcon className="ml-auto" />
                  )}
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator alwaysRender={true} />
            <CommandGroup>
              <CommandAction
                onClick={() =>
                  pushModal("CustomerCreateSheet", {
                    name: search,
                    onSuccess: (customer) => onSelect?.(customer),
                  })
                }
              >
                <PlusIcon />
                Add {search ? search : "new customer"}
              </CommandAction>
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
