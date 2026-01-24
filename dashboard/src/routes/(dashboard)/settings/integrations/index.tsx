import {
  Section,
  SectionDescription,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section.tsx";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/(dashboard)/settings/integrations/")({
  component: RouteComponent,
});

// type Integration = {
//   name: string;
//   description: string;
//   type: PaymentProviderEnum;
//   url: string;
//   href: string;
//   group: string;
// };

// const integrationsConfig = [
//   {
//     name: "Stripe",
//     description: "Automatically collect payments from your customers",
//     type: PaymentProviderEnum.stripe,
//     url: "/stripe.svg",
//     href: "/settings/integrations/stripe",
//     group: "payments",
//   },
//   // Add more integrations as needed
// ] as Integration[];

function RouteComponent() {
  // const navigate = Route.useNavigate();
  // const { data: integrations } = useListIntegrations();
  // TODO: rework it

  return (
    <SectionGroup>
      <Section>
        <SectionHeader>
          <SectionTitle>Integrations</SectionTitle>
          <SectionDescription>
            Enhance your experience by connecting with third-party services.
          </SectionDescription>
        </SectionHeader>
      </Section>
      {/*{connectedIntegrations && connectedIntegrations?.length > 0 && (*/}
      {/*  <Section>*/}
      {/*    <SectionHeader>*/}
      {/*      <SectionTitle>Connected</SectionTitle>*/}
      {/*    </SectionHeader>*/}
      {/*    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">*/}
      {/*      {connectedIntegrations.map((integration) => (*/}
      {/*        <IntegrationCard*/}
      {/*          key={integration.name}*/}
      {/*          name={integration.name}*/}
      {/*          url={integration.url}*/}
      {/*          onClick={() => navigate({ to: integration.href })}*/}
      {/*          connected*/}
      {/*        />*/}
      {/*      ))}*/}
      {/*    </div>*/}
      {/*  </Section>*/}
      {/*)}*/}
      {/*{integrationsByGroup.map(({ group, integrations }) => (*/}
      {/*  <Section key={group}>*/}
      {/*    <SectionHeader>*/}
      {/*      <SectionTitle className="capitalize">{group}</SectionTitle>*/}
      {/*    </SectionHeader>*/}
      {/*    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">*/}
      {/*      {integrations.map((integration) => {*/}
      {/*        const isConnected = connectedIntegrations.some(*/}
      {/*          (ci) => ci.type === integration.type,*/}
      {/*        );*/}
      {/*        return (*/}
      {/*          <IntegrationCard*/}
      {/*            key={integration.name}*/}
      {/*            name={integration.name}*/}
      {/*            url={integration.url}*/}
      {/*            description={integration.description}*/}
      {/*            onClick={() => navigate({ to: integration.href })}*/}
      {/*            connected={isConnected}*/}
      {/*          />*/}
      {/*        );*/}
      {/*      })}*/}
      {/*    </div>*/}
      {/*  </Section>*/}
      {/*))}*/}
    </SectionGroup>
  );
}
