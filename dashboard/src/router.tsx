import { routeTree } from "@/routeTree.gen.ts";
import { keepPreviousData, QueryClient } from "@tanstack/react-query";
import { createRouter } from "@tanstack/react-router";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      retry: false,
      placeholderData: keepPreviousData,
    },
  },
});

// Create a new router instance
export const router = createRouter({
  routeTree,
  context: {
    queryClient,
    auth: undefined,
    account: undefined,
  },
  defaultPreload: "intent",
  scrollRestoration: true,
  defaultStructuralSharing: true,
  defaultPreloadStaleTime: 0,
});

// Register the router instance for type safety
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
