import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Link from "next/link";


const marqueeItems = [
  "Northwind",
  "Lumen",
  "Orbit",
  "Monarch",
  "Sable",
  "Aster",
];

const compatibilityTabs = [
  {
    value: "api",
    label: "API",
    code: `// lib/openinvoice.ts\n\nimport { createClient } from "@openinvoice/sdk";\n\nexport const api = createClient({\n  baseUrl: process.env.NEXT_PUBLIC_API_URL,\n  apiKey: process.env.OPENINVOICE_API_KEY,\n});\n`,
  },
  {
    value: "webhooks",
    label: "Webhooks",
    code: `// webhooks/invoices.ts\n\nexport async function handler(event) {\n  if (event.type === "invoice.paid") {\n    await notifyFinance(event.data);\n  }\n}\n`,
  },
  {
    value: "integrations",
    label: "Integrations",
    code: `// integrations/stripe.ts\n\nexport const stripe = createStripe({\n  apiKey: process.env.STRIPE_KEY,\n});\n`,
  },
];

export default function HomePage() {
  return (
    <div className="overflow-hidden">
      <section>
        <div className="container">
          <div className="bordered-div-padding border-x text-center">
            <div className="mx-auto max-w-4xl space-y-6 md:space-y-8">
              <Badge variant="outline" className="rounded-sm border-none bg-card px-4 py-1.5 text-xs">
                OpenInvoice preview is live
              </Badge>
              <h1 className="font-weight-display text-2xl leading-snug tracking-tighter md:text-3xl lg:text-5xl">
                Open-source invoicing platform for modern teams.
              </h1>
              <p className="text-muted-foreground mx-auto max-w-[700px] text-sm leading-relaxed md:text-lg lg:text-xl">
                Create invoices, quotes, and credit notes with confidence. OpenInvoice keeps customers, products,
                taxes, and payments aligned from the first draft to final collection.
              </p>
            </div>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-4 md:gap-6">
              <Button className="font-weight-display h-10 rounded-full px-6 md:h-12 md:px-7" asChild>
                <Link href="/docs">Start Free Trial</Link>
              </Button>
              <Button
                variant="secondary"
                className="font-weight-display h-10 rounded-full px-6 md:h-12 md:px-7"
                asChild
              >
                <Link href="/docs">Community</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="container">
        <div className="grid grid-cols-1 border border-t-0 md:grid-cols-2">
          <div className="bordered-div-padding space-y-8 border-b md:border-e !pb-0">
            <div className="space-y-4">
              <h2 className="text-muted-foreground flex items-center gap-2 text-sm font-medium">
                <span className="inline-flex size-2 rounded-full bg-foreground/20" />
                Invoice Builder
              </h2>
              <h3 className="font-weight-display text-lg md:text-xl">Design invoices your way.</h3>
            </div>
            <p className="text-muted-foreground text-sm leading-relaxed md:text-base">
              Build line items, discounts, taxes, and shipping rates while keeping totals accurate and compliant.
            </p>
          </div>
          <div className="bordered-div-padding space-y-8 border-b md:border-b-0 !pb-0">
            <div className="space-y-4">
              <h2 className="text-muted-foreground flex items-center gap-2 text-sm font-medium">
                <span className="inline-flex size-2 rounded-full bg-foreground/20" />
                Collaboration
              </h2>
              <h3 className="font-weight-display text-lg md:text-xl">Built for finance teams.</h3>
            </div>
            <p className="text-muted-foreground text-sm leading-relaxed md:text-base">
              Draft, review, and publish invoices with role-based permissions and a shared customer portal.
            </p>
          </div>
          <div className="bordered-div-padding space-y-6">
            <div className="space-y-4">
              <h2 className="text-muted-foreground flex items-center gap-2 text-sm font-medium">
                <span className="inline-flex size-2 rounded-full bg-foreground/20" />
                Asset Management
              </h2>
              <h3 className="font-weight-display text-lg md:text-xl">Keep documents organized.</h3>
            </div>
            <p className="text-muted-foreground text-sm leading-relaxed md:text-base">
              Upload logos, documents, and attachments that follow every invoice and quote.
            </p>
          </div>
          <div className="bordered-div-padding space-y-6 border-t md:border-s">
            <div className="space-y-4">
              <h2 className="text-muted-foreground flex items-center gap-2 text-sm font-medium">
                <span className="inline-flex size-2 rounded-full bg-foreground/20" />
                Permissions
              </h2>
              <h3 className="font-weight-display text-lg md:text-xl">Control who does what.</h3>
            </div>
            <p className="text-muted-foreground text-sm leading-relaxed md:text-base">
              Create roles for administrators, finance teams, and guests with precision.
            </p>
          </div>
        </div>
      </section>

      <section className="container">
        <div className="bordered-div-padding border border-t-0">
          <div className="space-y-4">
            <h3 className="text-muted-foreground flex items-center gap-2 text-sm font-medium">
              <span className="inline-flex size-2 rounded-full bg-foreground/20" />
              Compatibility
            </h3>
            <h2 className="font-weight-display text-lg md:text-xl">Works out of the box with:</h2>
          </div>
          <Tabs defaultValue={compatibilityTabs[0].value} className="mt-6">
            <TabsList className="w-fit">
              {compatibilityTabs.map((tab) => (
                <TabsTrigger key={tab.value} value={tab.value}>
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>
            {compatibilityTabs.map((tab) => (
              <TabsContent key={tab.value} value={tab.value} className="mt-4">
                <Card className="rounded-sm">
                  <CardContent className="p-0">
                    <pre className="h-64 overflow-auto bg-transparent p-4 text-sm text-foreground">
                      <code>{tab.code}</code>
                    </pre>
                  </CardContent>
                </Card>
              </TabsContent>
            ))}
          </Tabs>
        </div>
      </section>

      <section className="container">
        <div className="bordered-div-padding border border-t-0">
          <h2 className="text-muted-foreground flex items-center gap-2 text-sm font-medium">
            <span className="inline-flex size-2 rounded-full bg-foreground/20" />
            Trusted by Fast-Moving Teams
          </h2>
          <div className="group mt-6 flex overflow-hidden p-2 [--duration:40s] [--gap:6rem]">
            <div className="animate-marquee flex shrink-0 items-center gap-[var(--gap)]">
              {marqueeItems.map((item) => (
                <span
                  key={item}
                  className="text-muted-foreground text-sm font-medium uppercase tracking-[0.2em]"
                >
                  {item}
                </span>
              ))}
            </div>
            <div className="animate-marquee flex shrink-0 items-center gap-[var(--gap)]">
              {marqueeItems.map((item) => (
                <span
                  key={`${item}-dup`}
                  className="text-muted-foreground text-sm font-medium uppercase tracking-[0.2em]"
                >
                  {item}
                </span>
              ))}
            </div>
          </div>
        </div>
        <blockquote className="bordered-div-padding flex flex-col gap-8 border border-t-0 md:flex-row">
          <p className="font-weight-display flex-1 text-2xl leading-snug tracking-tighter md:text-3xl">
            OpenInvoice changed how we track billing. Everything stays connected, visible, and simple.
          </p>
          <footer className="flex-1 self-end">
            <div className="flex items-center gap-4">
              <div className="size-10 rounded-full bg-muted" />
              <cite className="text-sm font-medium not-italic md:text-lg">
                Jamie Parker, Finance Lead at Ardent
              </cite>
            </div>
          </footer>
        </blockquote>
      </section>

      <section className="container">
        <div className="border-x bordered-div-padding">
          <h2 className="font-weight-display text-xl md:text-3xl lg:text-4xl">Start free. Scale confidently.</h2>
        </div>
        <div className="grid divide-y border md:grid-cols-2 md:divide-x md:divide-y-0">
          <div className="bordered-div-padding flex flex-col gap-6">
            <div>
              <h3 className="font-weight-display text-lg md:text-2xl">Open Source</h3>
              <p className="font-weight-display mt-6 text-base md:text-xl">$0 / forever</p>
            </div>
            <ul className="space-y-4 text-sm text-muted-foreground">
              <li>Self-host on your own infrastructure</li>
              <li>Full access to the OpenInvoice core</li>
              <li>GitHub community support</li>
              <li>Ideal for internal tools</li>
            </ul>
            <Button className="mt-auto w-fit rounded-full bg-border text-foreground" asChild>
              <Link href="/docs">View documentation</Link>
            </Button>
          </div>
          <div className="bordered-div-padding relative flex flex-col gap-6">
            <div className="absolute right-0 top-0 bg-secondary px-3 py-2 text-xs font-medium">
              Most popular
            </div>
            <div>
              <h3 className="font-weight-display text-lg md:text-2xl">Cloud</h3>
              <p className="font-weight-display mt-6 text-base md:text-xl">From $29 / month</p>
            </div>
            <ul className="space-y-4 text-sm text-muted-foreground">
              <li>Fully managed infrastructure</li>
              <li>Team permissions and audit trails</li>
              <li>Integrated analytics and alerts</li>
              <li>Priority support and monitoring</li>
            </ul>
            <Button className="mt-auto w-fit rounded-full" asChild>
              <Link href="/docs">Start Free Trial</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}
