import { useNumberingSystemsList } from "@/api/endpoints/numbering-systems/numbering-systems";
import {
  NumberingSystemAppliesToEnum,
  type NumberingSystem,
} from "@/api/models";
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
import { useActiveAccount } from "@/hooks/use-active-account.ts";
import { useDebounce } from "@/hooks/use-debounce";
import { cn } from "@/lib/utils";
import { CheckIcon, PlusIcon } from "lucide-react";
import React, { useState } from "react";

export function NumberingSystemCombobox({
  appliesTo,
  selected,
  onSelect,
  className,
  children,
  ...props
}: Omit<React.ComponentProps<typeof PopoverContent>, "onSelect"> & {
  appliesTo: NumberingSystemAppliesToEnum;
  selected?: NumberingSystem | null;
  onSelect?: (numberingSystem: NumberingSystem | null) => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const { account } = useActiveAccount();
  const debounce = useDebounce(search, 400);
  const { data } = useNumberingSystemsList(
    {
      page_size: 3,
      ordering: "-created_at",
      applies_to: appliesTo,
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
            placeholder="Find numbering system"
            value={search}
            onValueChange={setSearch}
          />
          <CommandList>
            <CommandEmpty>No numbering system found</CommandEmpty>
            <CommandGroup>
              {data?.results.map((numberingSystem) => (
                <CommandItem
                  key={numberingSystem.id}
                  value={numberingSystem.id}
                  onSelect={async (value) => {
                    setOpen(false);
                    await onSelect?.(
                      selected?.id === value ? null : numberingSystem,
                    );
                  }}
                >
                  {numberingSystem.description || numberingSystem.id}
                  {numberingSystem.id === selected?.id && (
                    <CheckIcon className="ml-auto" />
                  )}
                </CommandItem>
              ))}
            </CommandGroup>
            {account.subscription && (
              <>
                <CommandSeparator alwaysRender={true} />
                <CommandGroup>
                  <CommandAction
                    onClick={() =>
                      pushModal("NumberingSystemCreateSheet", {
                        description: search,
                        appliesTo,
                        onSuccess: (numberingSystem) =>
                          onSelect?.(numberingSystem),
                      })
                    }
                  >
                    <PlusIcon />
                    Add {search ? search : "new numbering system"}
                  </CommandAction>
                </CommandGroup>
              </>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
