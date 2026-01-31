import { LanguageEnum } from "@/api/models";
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
import { ScrollArea } from "@/components/ui/scroll-area.tsx";
import { formatLanguage } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { CheckIcon } from "lucide-react";
import React, { useMemo, useState } from "react";

export function LanguageCombobox({
  selected,
  onSelect,
  className,
  children,
  ...props
}: Omit<React.ComponentProps<typeof PopoverContent>, "onSelect"> & {
  selected?: string | null;
  onSelect?: (language: LanguageEnum | null) => Promise<void> | void;
}) {
  const [open, setOpen] = useState(false);
  const languages = useMemo(() => Object.values(LanguageEnum), []);

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
        <Command>
          <CommandInput placeholder="Find language" />
          <CommandList>
            <CommandEmpty>No language found</CommandEmpty>
            <CommandGroup>
              <ScrollArea className="h-52">
                {languages.map((language) => {
                  const label = formatLanguage(language);
                  return (
                    <CommandItem
                      key={language}
                      value={`${language} ${label}`}
                      onSelect={async () => {
                        setOpen(false);
                        await onSelect?.(
                          selected === language ? null : language,
                        );
                      }}
                    >
                      <span>{label}</span>
                      <span className="text-muted-foreground text-xs">
                        {language}
                      </span>
                      {language === selected && (
                        <CheckIcon className="ml-auto" />
                      )}
                    </CommandItem>
                  );
                })}
              </ScrollArea>
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
