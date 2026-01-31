import {
  getQuotesCommentsListQueryKey,
  useCreateQuoteComment,
  useDeleteQuoteComment,
  useQuotesCommentsList,
  useQuotesRetrieve,
} from "@/api/endpoints/quotes/quotes";
import { QuoteStatusEnum } from "@/api/models";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { AppSidebar } from "@/components/app-sidebar";
import { CommentsForm } from "@/components/comments-form";
import { CommentsList } from "@/components/comments-list";
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { QuoteBadge } from "@/components/quote-badge";
import { QuoteDropdown } from "@/components/quote-dropdown";
import { SearchCommand } from "@/components/search-command";
import { Button } from "@/components/ui/button";
import {
  Section,
  SectionDescription,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { getErrorSummary } from "@/lib/api/errors";
import { formatAmount } from "@/lib/formatters";
import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { MoreHorizontalIcon, PencilIcon } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/(dashboard)/quotes/$id")({
  component: RouteComponent,
});

function RouteComponent() {
  const { auth, account } = Route.useRouteContext();
  const { id } = Route.useParams();
  const queryClient = useQueryClient();
  const { data: quote } = useQuotesRetrieve(id);

  const comments = useQuotesCommentsList(id, undefined, {
    query: { enabled: !!id },
  });
  const createComment = useCreateQuoteComment({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getQuotesCommentsListQueryKey(id),
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });
  const deleteComment = useDeleteQuoteComment({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getQuotesCommentsListQueryKey(id),
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  if (!quote) return null;

  return (
    <SidebarProvider>
      <AppSidebar user={auth.user} account={account} />
      <SidebarInset>
        <div>
          <AppHeader>
            <AppHeaderContent>
              <SidebarTrigger />
              <NavBreadcrumb
                items={[
                  { type: "link", label: "Quotes", href: "/quotes" },
                  { type: "page", label: quote.number || "Quote" },
                ]}
              />
            </AppHeaderContent>
            <AppHeaderActions>
              <div className="flex items-center gap-2 text-sm">
                <SearchCommand />
                {quote.status === QuoteStatusEnum.draft && (
                  <Button type="button" variant="outline" size="sm" asChild>
                    <Link to="/quotes/$id/edit" params={{ id: quote.id }}>
                      <PencilIcon />
                      Edit
                    </Link>
                  </Button>
                )}
                <QuoteDropdown quote={quote} actions={{ edit: false }}>
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
          <main className="flex min-h-[calc(100svh_-_56px)]">
            <SectionGroup className="w-full flex-1">
              <Section>
                <SectionHeader>
                  <div className="flex items-center gap-2">
                    <SectionTitle>{quote.number || quote.id}</SectionTitle>
                    <QuoteBadge status={quote.status} />
                  </div>
                  <SectionDescription>
                    <span>Quoted to </span>
                    <Link
                      to="/customers/$id"
                      params={{ id: quote.customer.id }}
                    >
                      <span className="text-primary underline-offset-4 hover:underline">
                        {quote.customer.name}
                      </span>
                    </Link>
                    <span> - </span>
                    <span>
                      {formatAmount(quote.total_amount, quote.currency)}
                    </span>
                  </SectionDescription>
                </SectionHeader>
              </Section>
              <Section>
                <SectionHeader>
                  <SectionTitle>Comments</SectionTitle>
                </SectionHeader>
                <div className="space-y-4">
                  <CommentsList
                    comments={comments.data?.results ?? []}
                    isLoading={comments.isLoading}
                    onDelete={(commentId) =>
                      deleteComment.mutateAsync({
                        quoteId: quote.id,
                        id: commentId,
                      })
                    }
                  />
                  <CommentsForm
                    isCreating={createComment.isPending}
                    onCreate={(data) =>
                      createComment.mutateAsync({ quoteId: quote.id, data })
                    }
                  />
                </div>
              </Section>
            </SectionGroup>
          </main>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
