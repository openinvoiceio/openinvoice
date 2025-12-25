import { createFileRoute, Navigate, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/(public)")({
  component: RouteComponent,
});

function RouteComponent() {
  const { auth, account } = Route.useRouteContext();

  if (!auth?.user) return <Outlet />;
  if (!account) return <Navigate to="/setup" replace />;

  return <Navigate to="/overview" replace />;
}
