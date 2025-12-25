import type { Account, Authenticated } from "@/api/models";
import { ModalProvider } from "@/components/push-modals.tsx";
import { Toaster } from "@/components/ui/sonner";
import { TanStackDevtools } from "@tanstack/react-devtools";
import type { QueryClient } from "@tanstack/react-query";
import { ReactQueryDevtoolsPanel } from "@tanstack/react-query-devtools";
import { createRootRouteWithContext, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtoolsPanel } from "@tanstack/react-router-devtools";
import { NuqsAdapter } from "nuqs/adapters/tanstack-router";

interface RouterContext {
  queryClient: QueryClient;
  auth: Authenticated | undefined;
  account: Account | undefined;
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: () => (
    <>
      <NuqsAdapter>
        <Outlet />
        <ModalProvider />
      </NuqsAdapter>
      <Toaster />
      <TanStackDevtools
        config={{
          position: "bottom-left",
        }}
        plugins={[
          {
            name: "Tanstack Router",
            render: <TanStackRouterDevtoolsPanel />,
          },
          {
            name: "Tanstack Query",
            render: <ReactQueryDevtoolsPanel />,
          },
        ]}
      />
    </>
  ),
});
