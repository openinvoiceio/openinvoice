import { Separator } from "@/components/ui/separator.tsx";
import { Sheet, SheetContent } from "@/components/ui/sheet.tsx";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs.tsx";
import { useMediaQuery } from "@/hooks/use-media-query";
import { cn } from "@/lib/utils";
import React from "react";
import { createPortal } from "react-dom";

type DataSidebarContext = {
  value: string;
  setValue: (value: string) => void;
  isSheet: boolean;
  sheetOpen: boolean;
  setSheetOpen: (open: boolean) => void;
  sheetContainer: HTMLDivElement | null;
};

const DataSidebarCtx = React.createContext<DataSidebarContext | null>(null);

type DataSidebarProps = Omit<
  React.ComponentProps<typeof Tabs>,
  "value" | "onValueChange" | "orientation"
>;

function DataSidebar({
  className,
  children,
  defaultValue,
  ...props
}: DataSidebarProps) {
  const isDesktop = useMediaQuery("(min-width: 1280px)");
  const isSheet = !isDesktop;
  const [desktopValue, setDesktopValue] = React.useState<string>(
    defaultValue ?? "",
  );
  const [mobileValue, setMobileValue] = React.useState<string>("");
  const [sheetOpenState, setSheetOpenState] = React.useState(false);
  const [sheetContainer, setSheetContainer] =
    React.useState<HTMLDivElement | null>(null);

  const value = isSheet ? mobileValue : desktopValue;
  const sheetOpen = isSheet && sheetOpenState;

  const handleValueChange = React.useCallback(
    (next: string) => {
      if (isSheet) {
        setMobileValue(next);
        return;
      }

      if (next === "" && defaultValue) {
        setDesktopValue(defaultValue);
        return;
      }

      setDesktopValue(next);
    },
    [defaultValue, isSheet],
  );

  const handleSheetOpenChange = React.useCallback(
    (open: boolean) => {
      if (!isSheet) {
        setSheetOpenState(false);
        return;
      }

      setSheetOpenState(open);
      if (!open) {
        setMobileValue("");
      }
    },
    [isSheet],
  );

  const contextValue = React.useMemo(
    () => ({
      value,
      setValue: handleValueChange,
      isSheet,
      sheetOpen,
      setSheetOpen: handleSheetOpenChange,
      sheetContainer,
    }),
    [
      handleSheetOpenChange,
      handleValueChange,
      isSheet,
      sheetOpen,
      sheetContainer,
      value,
    ],
  );

  return (
    <DataSidebarCtx.Provider value={contextValue}>
      <Tabs
        data-slot="data-sidebar"
        orientation="vertical"
        value={value}
        onValueChange={handleValueChange}
        className={cn(
          "bg-sidebar hidden md:sticky md:top-14 md:flex md:max-h-[calc(100svh_-_56px)] md:flex-row-reverse md:gap-0 md:overflow-hidden xl:h-[calc(100svh_-_56px)]",
          "md:w-auto xl:w-[320px] 2xl:w-[400px]",
          !isDesktop && "xl:w-auto 2xl:w-auto",
          className,
        )}
        {...props}
      >
        {children}
      </Tabs>
      {isSheet && (
        <Sheet open={sheetOpen} onOpenChange={handleSheetOpenChange}>
          <SheetContent
            side="right"
            className="bg-sidebar text-sidebar-foreground"
          >
            <div ref={setSheetContainer} className="flex h-full flex-col" />
          </SheetContent>
        </Sheet>
      )}
    </DataSidebarCtx.Provider>
  );
}

function DataSidebarList({
  className,
  ...props
}: React.ComponentProps<typeof TabsList>) {
  return (
    <TabsList
      data-slot="data-sidebar-list"
      className={cn(
        "bg-sidebar border-sidebar-border flex h-full flex-col justify-start gap-1 rounded-none border-l",
        className,
      )}
      {...props}
    />
  );
}

function DataSidebarTrigger({
  className,
  value,
  onPointerDown,
  onKeyDown,
  ...props
}: React.ComponentProps<typeof TabsTrigger>) {
  const ctx = React.useContext(DataSidebarCtx);

  return (
    <TabsTrigger
      data-slot="data-sidebar-trigger"
      className={cn("size-9 flex-none", className)}
      value={value}
      onPointerDown={(e) => {
        if (!ctx) return;
        if (ctx.isSheet) {
          e.preventDefault();
          if (ctx.value === value && ctx.sheetOpen) {
            ctx.setSheetOpen(false);
            return;
          }

          ctx.setValue(value);
          ctx.setSheetOpen(true);
          return;
        }

        if (ctx.value === value) {
          e.preventDefault();
          ctx.setValue("");
          return;
        }
        onPointerDown?.(e);
      }}
      // keyboard toggle (Space/Enter)
      onKeyDown={(e) => {
        if (!ctx) return;
        if (ctx.isSheet) {
          if (e.key === " " || e.key === "Enter") {
            e.preventDefault();
            if (ctx.value === value && ctx.sheetOpen) {
              ctx.setSheetOpen(false);
              return;
            }

            ctx.setValue(value);
            ctx.setSheetOpen(true);
          }
          return;
        }

        if ((e.key === " " || e.key === "Enter") && ctx.value === value) {
          e.preventDefault();
          ctx.setValue("");
          return;
        }
        onKeyDown?.(e);
      }}
      {...props}
    />
  );
}

function DataSidebarContent({
  className,
  value,
  children,
  ...props
}: React.ComponentProps<typeof TabsContent>) {
  const ctx = React.useContext(DataSidebarCtx);
  const portalTarget = ctx?.sheetContainer ?? null;
  const renderInSheet = Boolean(
    ctx?.isSheet && ctx.sheetOpen && ctx.value === value && portalTarget,
  );

  return (
    <>
      <TabsContent
        data-slot="data-sidebar-content"
        className={cn(
          "border-sidebar-border hidden h-[calc(100svh_-_56px)] flex-1 flex-col gap-2 overflow-y-auto border-l xl:flex",
          className,
        )}
        value={value}
        {...props}
      >
        {children}
      </TabsContent>
      {renderInSheet
        ? createPortal(
            <div
              data-slot="data-sidebar-content"
              className={cn(
                "flex h-full flex-col gap-2 overflow-y-auto",
                className,
              )}
            >
              {children}
            </div>,
            portalTarget!,
          )
        : null}
    </>
  );
}

function DataSidebarTitle({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="data-sidebar-title"
      className={cn("px-4 py-3 font-medium", className)}
      {...props}
    />
  );
}

function DataSidebarSeparator({
  className,
  ...props
}: React.ComponentProps<typeof Separator>) {
  return (
    <Separator
      data-slot="data-sidebar-separator"
      className={cn("bg-sidebar-border my-2", className)}
      {...props}
    />
  );
}

export {
  DataSidebar,
  DataSidebarList,
  DataSidebarTrigger,
  DataSidebarContent,
  DataSidebarTitle,
  DataSidebarSeparator,
};
