import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
  useFinalizeInvoice,
  useInvoicesRetrieve,
} from "@/api/endpoints/invoices/invoices";
import {
  AppHeader,
  AppHeaderActions,
  AppHeaderContent,
} from "@/components/app-header";
import { InvoiceAdditionalCard } from "@/components/invoice-additional-card.tsx";
import { InvoiceBadge } from "@/components/invoice-badge";
import { InvoiceCurrencyCard } from "@/components/invoice-currency-card.tsx";
import { InvoiceCustomerCard } from "@/components/invoice-customer-card.tsx";
import { InvoiceDeliveryCard } from "@/components/invoice-delivery-card";
import { InvoiceDiscountsCard } from "@/components/invoice-discounts-card.tsx";
import { InvoiceDropdown } from "@/components/invoice-dropdown";
import { InvoiceLinesCard } from "@/components/invoice-lines-card.tsx";
import { InvoiceNumberingCard } from "@/components/invoice-numbering-card.tsx";
import { InvoicePaymentCollectionCard } from "@/components/invoice-payment-collection-card.tsx";
import { InvoicePreview } from "@/components/invoice-preview";
import { InvoiceTaxesCard } from "@/components/invoice-taxes-card.tsx";
import { NavBreadcrumb } from "@/components/nav-breadcrumb";
import { pushModal } from "@/components/push-modals";
import { SearchCommand } from "@/components/search-command.tsx";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Section,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
import { SidebarTrigger } from "@/components/ui/sidebar.tsx";
import { Spinner } from "@/components/ui/spinner";
import { getErrorSummary } from "@/lib/api/errors";
import { createFileRoute, Navigate } from "@tanstack/react-router";
import { CheckIcon, FileTextIcon, MoreHorizontalIcon } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/(dashboard)/invoices/$id_/edit")({
  component: RouteComponent,
});

function RouteComponent() {
  const navigate = Route.useNavigate();
  const { id } = Route.useParams();
  const { queryClient } = Route.useRouteContext();

  const { data: invoice } = useInvoicesRetrieve(id);
  const finalizeInvoice = useFinalizeInvoice({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getInvoicesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getInvoicesRetrieveQueryKey(id),
        });
        await queryClient.invalidateQueries({
          queryKey: getPreviewInvoiceQueryKey(id),
        });
        toast.success("Invoice finalized");
        navigate({ to: "/invoices/$id", params: { id } });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  if (!invoice) return null;
  if (invoice.status !== "draft")
    return <Navigate to="/invoices/$id" params={{ id }} />;

  return (
    <div>
      <AppHeader>
        <AppHeaderContent>
          <SidebarTrigger />
          <NavBreadcrumb
            items={[
              {
                type: "link",
                label: "Invoices",
                href: "/invoices",
              },
              {
                type: "link",
                label: invoice.number || "",
                href: `/invoices/${invoice.id}`,
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
              onClick={() => pushModal("InvoicePreviewDialog", { invoice })}
            >
              <FileTextIcon />
              Preview
            </Button>
            <Button
              type="button"
              size="sm"
              onClick={() => finalizeInvoice.mutateAsync({ id })}
              disabled={finalizeInvoice.isPending}
            >
              {finalizeInvoice.isPending ? <Spinner /> : <CheckIcon />}
              <span>Finalize</span>
            </Button>
            <InvoiceDropdown
              invoice={invoice}
              actions={{
                edit: false,
              }}
            >
              <Button
                type="button"
                size="icon"
                variant="outline"
                className="data-[state=open]:bg-accent size-8"
              >
                <MoreHorizontalIcon />
              </Button>
            </InvoiceDropdown>
          </div>
        </AppHeaderActions>
      </AppHeader>
      <main className="flex-1">
        <SectionGroup className="grid gap-2 2xl:max-w-7xl 2xl:grid-cols-2">
          <ScrollArea className="h-[calc(100svh_-_152px)] pr-3" type="scroll">
            <Section>
              <SectionHeader>
                <div className="flex items-center gap-2">
                  <SectionTitle>Edit invoice</SectionTitle>
                  <InvoiceBadge status={invoice.status} />
                </div>
              </SectionHeader>
              <InvoiceCustomerCard invoice={invoice} />
              <InvoiceNumberingCard invoice={invoice} />
              <InvoiceCurrencyCard invoice={invoice} />
              <InvoiceLinesCard invoice={invoice} />
              <InvoiceDiscountsCard invoice={invoice} />
              <InvoiceTaxesCard invoice={invoice} />
              <InvoicePaymentCollectionCard invoice={invoice} />
              <InvoiceDeliveryCard invoice={invoice} />
              <InvoiceAdditionalCard invoice={invoice} />
            </Section>
          </ScrollArea>
          <Section className="hidden max-w-[600px] 2xl:block">
            <SectionHeader>
              <SectionTitle>Preview</SectionTitle>
            </SectionHeader>
            <InvoicePreview invoice={invoice} />
          </Section>
        </SectionGroup>
      </main>
    </div>
  );
}
