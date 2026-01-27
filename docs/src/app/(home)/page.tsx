import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckCircle2 } from "lucide-react";
import Link from "next/link";


const marqueeItems = [
  "Invoices",
  "Quotes",
  "Credit Notes",
  "Customers",
  "Products",
  "Payments",
  "Taxes",
];

const invoiceFlowSteps = [
  {
    step: "01",
    title: "Set up customers",
    description: "Capture billing profiles, contacts, and tax details once.",
  },
  {
    step: "02",
    title: "Build your catalog",
    description: "Keep items, pricing, and tax rules ready to reuse.",
  },
  {
    step: "03",
    title: "Draft quotes",
    description: "Create proposals that convert directly into invoices.",
  },
  {
    step: "04",
    title: "Issue invoices",
    description: "Send invoices that stay consistent and easy to update.",
  },
  {
    step: "05",
    title: "Track payments",
    description: "Follow balances, due dates, and payment status in one view.",
  },
];

export default function HomePage() {
  return (
    <div className="overflow-hidden">
      <section>
        <div className="container">
          <div className="bordered-div-padding border-x text-center flex min-h-[70vh] flex-col items-center justify-center pt-16 pb-16 md:min-h-[80vh] md:pt-20 md:pb-20 lg:pt-24 lg:pb-24">
            <div className="mx-auto max-w-4xl space-y-6 md:space-y-8 -translate-y-6 md:-translate-y-8">
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
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="container">
          <div className="border border-b-0 section-lines">
          <div className="grid grid-cols-1 divide-y md:grid-cols-2 md:divide-x md:divide-y-0">
            <div className="bordered-div-padding space-y-8">
              <div className="space-y-4">
                <h2 className="text-muted-foreground flex items-center gap-2 text-sm font-medium">
                  <span className="inline-flex size-2 rounded-full bg-foreground/20" />
                  Invoicing
                </h2>
                <h3 className="font-weight-display text-lg md:text-xl">Move from draft to paid faster.</h3>
              </div>
              <p className="text-muted-foreground text-sm leading-relaxed md:text-base">
                Create, send, and update invoices while keeping every detail consistent.
              </p>
            </div>
            <div className="bordered-div-padding space-y-8">
              <div className="space-y-4">
                <h2 className="text-muted-foreground flex items-center gap-2 text-sm font-medium">
                  <span className="inline-flex size-2 rounded-full bg-foreground/20" />
                  Quotes & Credits
                </h2>
                <h3 className="font-weight-display text-lg md:text-xl">Quote, revise, and credit with ease.</h3>
              </div>
              <p className="text-muted-foreground text-sm leading-relaxed md:text-base">
                Turn proposals into invoices and issue credit notes without rework.
              </p>
            </div>
            <div className="bordered-div-padding space-y-6 md:border-t">
              <div className="space-y-4">
                <h2 className="text-muted-foreground flex items-center gap-2 text-sm font-medium">
                  <span className="inline-flex size-2 rounded-full bg-foreground/20" />
                  Customers
                </h2>
                <h3 className="font-weight-display text-lg md:text-xl">Keep customer records ready.</h3>
              </div>
              <p className="text-muted-foreground text-sm leading-relaxed md:text-base">
                Store addresses, contacts, and tax details where they are easy to reuse.
              </p>
            </div>
            <div className="bordered-div-padding space-y-6 md:border-t">
              <div className="space-y-4">
                <h2 className="text-muted-foreground flex items-center gap-2 text-sm font-medium">
                  <span className="inline-flex size-2 rounded-full bg-foreground/20" />
                  Product Catalog
                </h2>
                <h3 className="font-weight-display text-lg md:text-xl">Build a catalog once.</h3>
              </div>
              <p className="text-muted-foreground text-sm leading-relaxed md:text-base">
                Reuse items, pricing, and tax rules across every invoice and quote.
              </p>
            </div>
          </div>
          <div className="bordered-div-padding space-y-6 border-t">
            <div className="space-y-4">
              <h2 className="text-muted-foreground flex items-center gap-2 text-sm font-medium">
                <span className="inline-flex size-2 rounded-full bg-foreground/20" />
                Payments
              </h2>
              <h3 className="font-weight-display text-lg md:text-xl">Track every payment and balance.</h3>
            </div>
            <p className="text-muted-foreground text-sm leading-relaxed md:text-base">
              See what is paid, overdue, or coming up without stitching together spreadsheets.
            </p>
          </div>
          </div>
        </div>
      </section>

      <section>
        <div className="container">
          <div className="border border-b-0 border-t-0 section-lines">
            <div className="grid gap-10 bordered-div-padding md:grid-cols-[minmax(0,360px)_minmax(0,1fr)] md:gap-14">
              <div className="space-y-6">
                <h3 className="text-muted-foreground flex items-center gap-2 text-sm font-medium">
                  <span className="inline-flex size-2 rounded-full bg-foreground/20" />
                  From draft to paid
                </h3>
                <h2 className="font-weight-display text-xl leading-snug md:text-2xl">
                  A clear invoice flow your team can follow.
                </h2>
                <p className="text-muted-foreground text-sm leading-relaxed md:text-base">
                  Build your workflow once and keep customers, catalog, and payments aligned.
                </p>
              </div>
              <div className="divide-y border-t md:border-t-0">
                {invoiceFlowSteps.map((step) => (
                  <div
                    key={step.step}
                    className="group flex gap-6 py-6 transition-colors hover:bg-muted/40 md:px-6"
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-muted text-xs font-semibold text-muted-foreground">
                      {step.step}
                    </div>
                    <div className="space-y-2">
                      <h4 className="font-weight-display text-base md:text-lg">{step.title}</h4>
                      <p className="text-muted-foreground text-sm md:text-base">{step.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="container">
          <div className="bordered-div-padding border border-t-0 section-lines">
            <h2 className="text-muted-foreground flex items-center gap-2 text-sm font-medium">
              <span className="inline-flex size-2 rounded-full bg-foreground/20" />
              Core workflows
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
          <blockquote className="bordered-div-padding border border-b-0 border-t-0">
            <div className="space-y-3">
              <p className="font-weight-display text-2xl leading-snug tracking-tighter md:text-3xl">
                OpenInvoice keeps invoicing clear, auditable, and easy to share.
              </p>
              <p className="text-muted-foreground text-sm md:text-base">
                Everything stays connected from the first quote to the final payment reminder.
              </p>
            </div>
          </blockquote>
        </div>
      </section>

      <section>
        <div className="container">
          <div className="border-x bordered-div-padding section-lines">
            <h2 className="font-weight-display text-xl md:text-3xl lg:text-4xl">Choose how you run OpenInvoice.</h2>
          </div>
          <div className="grid divide-y border md:grid-cols-2 md:divide-x md:divide-y-0">
            <div className="bordered-div-padding flex flex-col gap-6">
              <div>
                <h3 className="font-weight-display text-lg md:text-2xl">Open Source</h3>
                <p className="font-weight-display mt-6 text-base md:text-xl">$0 / forever</p>
              </div>
              <ul className="space-y-4 text-sm text-muted-foreground">
                {[
                  "Self-host on your own infrastructure",
                  "Full access to the OpenInvoice core",
                  "GitHub community support",
                  "Ideal for internal workflows",
                ].map((feature) => (
                  <li key={feature} className="flex items-start gap-3">
                    <CheckCircle2 className="mt-0.5 size-4 text-foreground/70" />
                    <span>{feature}</span>
                  </li>
                ))}
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
                {[
                  "Fully managed infrastructure",
                  "Team permissions and audit trails",
                  "Integrated analytics and alerts",
                  "Priority support and monitoring",
                ].map((feature) => (
                  <li key={feature} className="flex items-start gap-3">
                    <CheckCircle2 className="mt-0.5 size-4 text-foreground/70" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              <Button className="mt-auto w-fit rounded-full" asChild>
                <Link href="/docs">Start Free Trial</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
