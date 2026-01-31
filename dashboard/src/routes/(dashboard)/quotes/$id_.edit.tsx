import {
  getPreviewQuoteQueryKey,
  getQuotesListQueryKey,
  getQuotesRetrieveQueryKey,
  useFinalizeQuote,
  useQuotesRetrieve,
} from "@/api/endpoints/quotes/quotes";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { AppSidebar } from "@/components/app-sidebar";
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { pushModal } from "@/components/push-modals.tsx";
import { SearchCommand } from "@/components/search-command.tsx";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Section,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar.tsx";
import { Spinner } from "@/components/ui/spinner";
import { QuoteAdditionalCard } from "@/features/quotes/components/quote-additional-card.tsx";
import { QuoteBadge } from "@/features/quotes/components/quote-badge";
import { QuoteCurrencyCard } from "@/features/quotes/components/quote-currency-card.tsx";
import { QuoteCustomerCard } from "@/features/quotes/components/quote-customer-card.tsx";
import { QuoteDeliveryCard } from "@/features/quotes/components/quote-delivery-card";
import { QuoteDiscountsCard } from "@/features/quotes/components/quote-discounts-card.tsx";
import { QuoteDropdown } from "@/features/quotes/components/quote-dropdown.tsx";
import { QuoteLinesCard } from "@/features/quotes/components/quote-lines-card.tsx";
import { QuoteNumberingCard } from "@/features/quotes/components/quote-numbering-card.tsx";
import { QuotePreview } from "@/features/quotes/components/quote-preview";
import { QuoteTaxesCard } from "@/features/quotes/components/quote-taxes-card.tsx";
import { getErrorSummary } from "@/lib/api/errors";
import { createFileRoute, Navigate } from "@tanstack/react-router";
import { CheckIcon, FileTextIcon, MoreHorizontalIcon } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/(dashboard)/quotes/$id_/edit")({
  component: RouteComponent,
});

function RouteComponent() {
  const navigate = Route.useNavigate();
  const { id } = Route.useParams();
  const { auth, account, queryClient } = Route.useRouteContext();

  const { data: quote } = useQuotesRetrieve(id);
  const finalizeQuote = useFinalizeQuote({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getQuotesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getQuotesRetrieveQueryKey(id),
        });
        await queryClient.invalidateQueries({
          queryKey: getPreviewQuoteQueryKey(id),
        });
        toast.success("Quote finalized");
        navigate({ to: "/quotes/$id", params: { id } });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  if (!quote) return null;
  if (quote.status !== "draft")
    return <Navigate to="/quotes/$id" params={{ id }} />;

  return (
    <SidebarProvider>
      <AppSidebar user={auth?.user} account={account} />
      <SidebarInset>
        <div>
          <AppHeader>
            <AppHeaderContent>
              <SidebarTrigger />
              <NavBreadcrumb
                items={[
                  {
                    type: "link",
                    label: "Quotes",
                    href: "/quotes",
                  },
                  {
                    type: "link",
                    label: quote.number || "",
                    href: `/quotes/${quote.id}`,
                  },
                  {
                    type: "page",
                    label: "Edit",
                  },
                ]}
              />
            </AppHeaderContent>
            <AppHeaderActions>
              <div className="flex items-center gap-2 text-sm">
                <SearchCommand />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="2xl:hidden"
                  onClick={() => pushModal("QuotePreviewDialog", { quote })}
                >
                  <FileTextIcon />
                  Preview
                </Button>
                <Button
                  type="button"
                  size="sm"
                  onClick={() =>
                    finalizeQuote.mutateAsync({ quoteId: quote.id })
                  }
                  disabled={finalizeQuote.isPending}
                >
                  {finalizeQuote.isPending ? <Spinner /> : <CheckIcon />}
                  <span>Finalize</span>
                </Button>
                <QuoteDropdown quote={quote}>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    className="data-[state=open]:bg-accent size-8"
                  >
                    <MoreHorizontalIcon />
                  </Button>
                </QuoteDropdown>
              </div>
            </AppHeaderActions>
          </AppHeader>
          <main className="flex-1">
            <SectionGroup className="grid gap-2 2xl:max-w-7xl 2xl:grid-cols-2">
              <ScrollArea
                className="h-[calc(100svh_-_152px)] pr-3"
                type="scroll"
              >
                <Section>
                  <SectionHeader>
                    <div className="flex items-center gap-2">
                      <SectionTitle>Edit quote</SectionTitle>
                      <QuoteBadge status={quote.status} />
                    </div>
                  </SectionHeader>
                  <QuoteCustomerCard quote={quote} />
                  <QuoteNumberingCard quote={quote} />
                  <QuoteCurrencyCard quote={quote} />
                  <QuoteLinesCard quote={quote} />
                  <QuoteDiscountsCard quote={quote} />
                  <QuoteTaxesCard quote={quote} />
                  <QuoteDeliveryCard quote={quote} />
                  <QuoteAdditionalCard quote={quote} />
                </Section>
              </ScrollArea>
              <Section className="hidden max-w-[600px] 2xl:block">
                <SectionHeader>
                  <SectionTitle>Preview</SectionTitle>
                </SectionHeader>
                <QuotePreview quote={quote} />
              </Section>
            </SectionGroup>
          </main>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
