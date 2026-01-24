import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/(dashboard)/quotes/$id")({
  component: RouteComponent,
});

function RouteComponent() {
  return <div>Hello "/(dashboard)/quotes/$id"!</div>;
}
