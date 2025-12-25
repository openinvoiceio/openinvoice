import { createFileRoute, Navigate } from "@tanstack/react-router";

export const Route = createFileRoute("/(dashboard)/settings/")({
  component: RouteComponent,
});

function RouteComponent() {
  return <Navigate to="/settings/account" />;
}
