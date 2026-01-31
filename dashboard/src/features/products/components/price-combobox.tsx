import { usePricesList } from "@/api/endpoints/prices/prices";
import { PricesListStatus, type Price } from "@/api/models";
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
import { formatPrice } from "@/lib/products.ts";
import { cn } from "@/lib/utils";
import { CheckIcon, PlusIcon } from "lucide-react";
import React, { useState, type ReactNode } from "react";

export function PriceCombobox({
  selected,
  onSelect,
  currency,
  status,
  actions,
  className,
  children,
  ...props
}: Omit<React.ComponentProps<typeof PopoverContent>, "onSelect"> & {
  selected?: Price | null;
  onSelect?: (price: Price | null) => Promise<void>;
  currency?: string;
  status?: PricesListStatus;
  actions?: {
    name: string;
    onClick: (value: string) => Promise<void>;
  }[];
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const debounce = useDebounce(search, 400);
  const { data } = usePricesList(
    {
      page_size: 3,
      ordering: "product_id,-created_at",
      ...(search ? { search: debounce } : {}),
      ...(currency ? { currency } : {}),
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
            placeholder="Find price"
            value={search}
            onValueChange={setSearch}
          />
          <CommandList>
            <CommandEmpty>No price found</CommandEmpty>
            {data?.results.reduce<ReactNode[]>(
              (nodes, price, index, prices) => {
                const previousPrice = prices[index - 1];
                const isNewGroup =
                  !previousPrice ||
                  previousPrice.product.id !== price.product.id;

                if (isNewGroup) {
                  nodes.push(
                    <CommandGroup
                      key={price.product.id}
                      heading={price.product.name}
                      className="py-0 last:pb-1"
                    >
                      {prices
                        .filter((p) => p.product.id === price.product.id)
                        .map((p) => (
                          <CommandItem
                            key={p.id}
                            value={p.id}
                            onSelect={async (value) => {
                              setOpen(false);
                              await onSelect?.(
                                selected?.id === value ? null : p,
                              );
                            }}
                          >
                            <span>{formatPrice(p)}</span>
                            {p.code && (
                              <span className="text-muted-foreground">
                                {p.code}
                              </span>
                            )}
                            {p.id === selected?.id && (
                              <CheckIcon className="ml-auto" />
                            )}
                          </CommandItem>
                        ))}
                    </CommandGroup>,
                  );
                }

                return nodes;
              },
              [],
            )}
            <CommandSeparator alwaysRender={true} className="mt-1" />
            <CommandGroup>
              <CommandAction
                onClick={() =>
                  pushModal("PriceCreateSheet", {
                    name: search,
                    onSuccess: (price) => onSelect?.(price),
                  })
                }
              >
                <PlusIcon />
                Add new price
              </CommandAction>
              <CommandAction
                onClick={() =>
                  pushModal("ProductCreateSheet", {
                    name: search,
                    onSuccess: (product) =>
                      onSelect?.(product.default_price as Price), // TODO: refine this, maybe we should fetch the price again
                  })
                }
              >
                <PlusIcon />
                Add {search ? search : "new product with price"}
              </CommandAction>
              {actions?.map(({ name, onClick }) => (
                <CommandAction
                  key={name}
                  onClick={async () => {
                    setOpen(false);
                    await onClick(search);
                  }}
                >
                  <PlusIcon />
                  {name}
                </CommandAction>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
