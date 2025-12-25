import { useProductsList } from "@/api/endpoints/products/products";
import type { Product } from "@/api/models";
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
import { BoxIcon, CheckIcon, PlusIcon } from "lucide-react";
import React, { useState } from "react";

export function ProductCombobox({
  selected,
  onSelect,
  withoutPrice,
  className,
  children,
  ...props
}: Omit<React.ComponentProps<typeof PopoverContent>, "onSelect"> & {
  selected?: Product | null;
  onSelect?: (product: Product | null) => Promise<void>;
  withoutPrice?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const debounce = useDebounce(search, 400);
  const { data } = useProductsList(
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
            placeholder="Find product"
            value={search}
            onValueChange={setSearch}
          />
          <CommandList>
            <CommandEmpty>No product found</CommandEmpty>
            <CommandGroup>
              {data?.results.map((product) => (
                <CommandItem
                  key={product.id}
                  value={product.id}
                  onSelect={async (value) => {
                    setOpen(false);
                    await onSelect?.(selected?.id === value ? null : product);
                  }}
                >
                  <CommandItemAvatar src={product.image_url}>
                    <BoxIcon />
                  </CommandItemAvatar>
                  <span>{product.name}</span>
                  {product.id === selected?.id && (
                    <CheckIcon className="ml-auto" />
                  )}
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator alwaysRender={true} />
            <CommandGroup>
              <CommandAction
                onClick={() =>
                  pushModal("ProductCreateSheet", {
                    name: search,
                    onSuccess: (product) => onSelect?.(product),
                    withoutPrice,
                  })
                }
              >
                <PlusIcon />
                Add {search ? search : "new product"}
              </CommandAction>
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
