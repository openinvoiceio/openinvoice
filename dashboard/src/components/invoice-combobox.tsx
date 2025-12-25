import { useInvoicesList } from "@/api/endpoints/invoices/invoices.ts";
import type { Invoice, InvoiceStatusEnum } from "@/api/models";
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
import { cn } from "@/lib/utils";
import { CheckIcon, PlusIcon } from "lucide-react";
import React, { useState } from "react";

export function InvoiceCombobox({
  selected,
  onSelect,
  status,
  minOutstandingAmount,
  className,
  children,
  ...props
}: Omit<React.ComponentProps<typeof PopoverContent>, "onSelect"> & {
  selected?: Invoice | null;
  onSelect?: (invoice: Invoice | null) => Promise<void>;
  status?: InvoiceStatusEnum[];
  minOutstandingAmount?: number;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const debounce = useDebounce(search, 400);
  const { data } = useInvoicesList(
    {
      page_size: 3,
      ordering: "-created_at",
      ...(search ? { search: debounce } : {}),
      ...(status && status.length > 0 ? { status: [status.join(",")] } : {}),
      ...(minOutstandingAmount
        ? { outstanding_amount_min: minOutstandingAmount }
        : {}),
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
            placeholder="Find invoice"
            value={search}
            onValueChange={setSearch}
          />
          <CommandList>
            <CommandEmpty>No invoice found</CommandEmpty>
            <CommandGroup>
              {data?.results.map((invoice) => (
                <CommandItem
                  key={invoice.id}
                  value={invoice.id}
                  onSelect={async (value) => {
                    setOpen(false);
                    await onSelect?.(selected?.id === value ? null : invoice);
                  }}
                >
                  <span>{invoice.number}</span>
                  {invoice.id === selected?.id && (
                    <CheckIcon className="ml-auto" />
                  )}
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator alwaysRender={true} />
            <CommandGroup>
              <CommandAction>
                <PlusIcon />
                Add {search ? search : "new invoice"}
              </CommandAction>
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
