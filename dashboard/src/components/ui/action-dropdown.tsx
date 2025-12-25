import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Spinner } from "@/components/ui/spinner";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  Fragment,
  useMemo,
  useState,
  type ComponentProps,
  type ComponentType,
  type ReactNode,
} from "react";
import { useHotkeys } from "react-hotkeys-hook";

export type DropdownAction<TData> = {
  key: string;
  label: string | ((data: TData) => string);
  icon?: ComponentType<{ className?: string }>;
  tooltip?: string | ((data: TData) => string | undefined);
  shortcut?: string | ReactNode;
  hotkey?: string;
  visible?: (data: TData) => boolean;
  disabled?: (data: TData) => boolean;
  onSelect?: (data: TData) => void | Promise<void>;
};

export type ActionSection<TData> = {
  key?: string;
  label?: string;
  danger?: boolean;
  items: DropdownAction<TData>[];
};

export type ActionDropdownProps<TData> = Omit<
  ComponentProps<typeof DropdownMenuContent>,
  "children"
> & {
  data: TData;
  sections: ActionSection<TData>[];
  children: ReactNode;
  className?: string;
  enableHotkeys?: boolean;
  actions?: string[] | Partial<Record<string, boolean>>;
};

function ActionHotkeyBinder({
  hotkey,
  enabled,
  onTrigger,
}: {
  hotkey: string;
  enabled: boolean;
  onTrigger: () => void;
}) {
  useHotkeys(
    hotkey,
    (e) => {
      if (!enabled) return;
      e.preventDefault();
      onTrigger();
    },
    { enableOnFormTags: false, enabled },
    [enabled, onTrigger],
  );
  return null;
}

function normalizeAllowlist(
  actions?: string[] | Partial<Record<string, boolean>>,
): {
  mode: "all" | "allowlist" | "denylist";
  set: Set<string>;
  orderIndex: Map<string, number>;
} {
  if (!actions) return { mode: "all", set: new Set(), orderIndex: new Map() };

  if (Array.isArray(actions)) {
    const set = new Set(actions);
    const orderIndex = new Map<string, number>();
    actions.forEach((k, i) => orderIndex.set(k, i));
    return { mode: "allowlist", set, orderIndex };
  }

  // map form: include everything except explicitly false
  const set = new Set<string>();
  for (const [k, v] of Object.entries(actions)) {
    if (v === false) set.add(k);
  }
  return { mode: "denylist", set, orderIndex: new Map() };
}

export function ActionDropdown<TData>({
  data,
  sections,
  children,
  align = "end",
  className,
  enableHotkeys = true,
  actions, // NEW
  ...contentProps
}: ActionDropdownProps<TData>) {
  const [pendingKey, setPendingKey] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  const allow = useMemo(() => normalizeAllowlist(actions), [actions]);

  const preparedSections = useMemo(() => {
    return sections
      .map((section) => {
        let items = section.items.filter((a) => {
          if (allow.mode === "all") return true;
          if (allow.mode === "allowlist") return allow.set.has(a.key);
          // denylist: drop keys present in set
          return !allow.set.has(a.key);
        });

        items = items.filter((a) => (a.visible ? a.visible(data) : true));

        if (allow.mode === "allowlist") {
          items.sort((a, b) => {
            const ia = allow.orderIndex.get(a.key) ?? Number.MAX_SAFE_INTEGER;
            const ib = allow.orderIndex.get(b.key) ?? Number.MAX_SAFE_INTEGER;
            return ia - ib;
          });
        }

        return { ...section, items };
      })
      .filter((s) => s.items.length > 0);
  }, [sections, data, allow]);

  const exec = async (a: DropdownAction<TData>) => {
    if (!a.onSelect) return;
    const maybe = a.onSelect(data);
    if (maybe && typeof (maybe as any).then === "function") {
      setPendingKey(a.key);
      try {
        await maybe;
      } finally {
        setPendingKey(null);
      }
    }
  };

  const renderItem = (a: DropdownAction<TData>, danger?: boolean) => {
    const disabled = a.disabled ? a.disabled(data) : false;
    const label = typeof a.label === "function" ? a.label(data) : a.label;
    const tip = typeof a.tooltip === "function" ? a.tooltip(data) : a.tooltip;
    const Icon = a.icon;
    const loading = pendingKey === a.key;

    const onTrigger = () => {
      if (!disabled) {
        void exec(a);
        setOpen(false);
      }
    };

    const base = (
      <DropdownMenuItem
        key={a.key}
        onClick={() => !disabled && exec(a)}
        disabled={disabled || loading}
        variant={danger ? "destructive" : "default"}
      >
        {loading ? <Spinner /> : Icon ? <Icon className="mr-2 size-4" /> : null}
        <span className="mr-auto">{label}</span>
        {a.shortcut ? (
          <DropdownMenuShortcut>{a.shortcut}</DropdownMenuShortcut>
        ) : null}
      </DropdownMenuItem>
    );

    const wrapped =
      tip && disabled ? (
        <TooltipProvider key={a.key}>
          <Tooltip>
            <TooltipTrigger asChild>{base}</TooltipTrigger>
            <TooltipContent>{tip}</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      ) : (
        base
      );

    return (
      <Fragment key={a.key}>
        {a.hotkey ? (
          <ActionHotkeyBinder
            hotkey={a.hotkey}
            enabled={enableHotkeys && open && !disabled}
            onTrigger={onTrigger}
          />
        ) : null}
        {wrapped}
      </Fragment>
    );
  };

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>{children}</DropdownMenuTrigger>
      <DropdownMenuContent
        align={align}
        className={cn("w-56", className)}
        {...contentProps}
      >
        {preparedSections.map((section, idx) => (
          <Fragment key={section.key ?? idx}>
            {idx > 0 && <DropdownMenuSeparator />}
            <DropdownMenuGroup>
              {section.label && (
                <DropdownMenuLabel className="text-xs">
                  {section.label}
                </DropdownMenuLabel>
              )}
              {section.items.map((a) => renderItem(a, section.danger))}
            </DropdownMenuGroup>
          </Fragment>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
