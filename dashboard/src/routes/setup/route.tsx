import { createFileRoute, Navigate, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/setup")({
  component: RouteComponent,
});

function RouteComponent() {
  const { auth, account } = Route.useRouteContext();

  if (!auth?.user) return <Navigate to="/login" replace />;
  if (!account) return <Outlet />;

  return <Navigate to="/overview" replace />;
}
