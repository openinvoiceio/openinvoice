import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar.tsx";
import { FormCard } from "@/components/ui/form-card.tsx";
import {
  Section,
  SectionDescription,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/(dashboard)/settings/integrations/stripe",
)({
  component: RouteComponent,
});

function RouteComponent() {
  return (
    <SectionGroup>
      <Section>
        <SectionHeader className="flex-row items-center gap-3">
          <Avatar className="size-11 rounded-md">
            <AvatarImage src="/stripe.svg" />
            <AvatarFallback>Stripe</AvatarFallback>
          </Avatar>
          <div>
            <SectionTitle>Stripe</SectionTitle>
            <SectionDescription>
              Enhance your experience by connecting with third-party services.
            </SectionDescription>
          </div>
        </SectionHeader>
        <FormCard></FormCard>
      </Section>
    </SectionGroup>
  );
}
