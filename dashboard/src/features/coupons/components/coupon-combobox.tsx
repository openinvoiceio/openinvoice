import { useCouponsList } from "@/api/endpoints/coupons/coupons";
import { CouponsListStatus, CurrencyEnum, type Coupon } from "@/api/models";
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
import { formatAmount, formatPercentage } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { CheckIcon, PlusIcon } from "lucide-react";
import React, { useState } from "react";

export function CouponCombobox({
  selected,
  onSelect,
  currency,
  status,
  className,
  children,
  ...props
}: Omit<React.ComponentProps<typeof PopoverContent>, "onSelect"> & {
  selected?: Coupon | null;
  onSelect?: (coupon: Coupon | null) => Promise<void>;
  currency?: CurrencyEnum;
  status?: CouponsListStatus;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const debounce = useDebounce(search, 400);
  const { data } = useCouponsList(
    {
      page_size: 3,
      ordering: "-created_at",
      ...(search ? { search: debounce } : {}),
      ...(currency ? { currency: [currency] } : {}),
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
            placeholder="Find coupon"
            value={search}
            onValueChange={setSearch}
          />
          <CommandList>
            <CommandEmpty>No coupon found</CommandEmpty>
            <CommandGroup>
              {data?.results.map((coupon) => (
                <CommandItem
                  key={coupon.id}
                  value={coupon.id}
                  onSelect={async (value) => {
                    setOpen(false);
                    await onSelect?.(selected?.id === value ? null : coupon);
                  }}
                >
                  <span className="max-w-32 truncate">{coupon.name}</span>
                  <span className="text-muted-foreground">
                    {!!coupon.amount
                      ? formatAmount(coupon.amount, coupon.currency)
                      : formatPercentage(coupon.percentage as string)}
                  </span>
                  {coupon.id === selected?.id && (
                    <CheckIcon className="ml-auto" />
                  )}
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator alwaysRender={true} />
            <CommandGroup>
              <CommandAction
                onClick={() =>
                  pushModal("CouponCreateSheet", {
                    name: search,
                    currency,
                    onSuccess: (coupon) => onSelect?.(coupon),
                  })
                }
              >
                <PlusIcon />
                Add {search ? search : "new coupon"}
              </CommandAction>
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
