import {
  usePortalCustomerRetrieve,
  usePortalInvoicesList,
} from "@/api/endpoints/portal/portal";
import { AddressView } from "@/components/address-view";
import { pushModal } from "@/components/push-modals";
import { Button } from "@/components/ui/button";
import {
  DataList,
  DataListItem,
  DataListLabel,
  DataListValue,
} from "@/components/ui/data-list";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import {
  MetricCard,
  MetricCardHeader,
  MetricCardTitle,
  MetricCardValue,
} from "@/components/ui/metric-card";
import {
  Section,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useDownload } from "@/hooks/use-download";
import { formatAmount, formatDate, formatTaxIdType } from "@/lib/formatters";
import { createFileRoute } from "@tanstack/react-router";
import { DownloadIcon } from "lucide-react";

export const Route = createFileRoute("/customer-portal/$token")({
  component: RouteComponent,
});

function RouteComponent() {
  const { token: encodedToken } = Route.useParams();
  const token = decodeURIComponent(encodedToken || "");
  const request = { headers: { Authorization: `Bearer ${token}` } };

  const { download, isDownloading } = useDownload();
  const { data: customer } = usePortalCustomerRetrieve({ request });
  const { data: invoices } = usePortalInvoicesList({}, { request });

  // TODO: improve ui error handling
  if (!customer) return null;

  return (
    <div className="grid min-h-svh grid-cols-12 gap-6">
      <nav className="bg-muted/50 sticky top-0 left-0 col-span-3 flex h-svh flex-col p-8">
        <div className="flex flex-col gap-8">
          <h1 className="text-2xl font-medium">{customer.name}</h1>
          <p className="text-normal font-medium">Manage your billing</p>
          <div className="text-muted-foreground text-xs">
            Powered by Invoicence
          </div>
        </div>
      </nav>
      <main className="col-span-9 overflow-y-auto">
        <SectionGroup>
          <Section>
            <SectionHeader>
              <div className="flex justify-between gap-2">
                <SectionTitle>Information</SectionTitle>
                <Button
                  size="sm"
                  className="h-7"
                  variant="outline"
                  onClick={() =>
                    pushModal("CustomerPortalEditSheet", { customer, token })
                  }
                >
                  Edit
                </Button>
              </div>
            </SectionHeader>
            <div className="grid grid-cols-2 gap-2">
              <DataList orientation="vertical" className="gap-4 text-sm">
                <DataListItem>
                  <DataListLabel>Name</DataListLabel>
                  <DataListValue>{customer.name}</DataListValue>
                </DataListItem>
                {customer.legal_name && (
                  <DataListItem>
                    <DataListLabel>Legal name</DataListLabel>
                    <DataListValue>{customer.legal_name}</DataListValue>
                  </DataListItem>
                )}
                {customer.legal_number && (
                  <DataListItem>
                    <DataListLabel>Legal number</DataListLabel>
                    <DataListValue>{customer.legal_number}</DataListValue>
                  </DataListItem>
                )}
                {customer.tax_ids?.length > 0 && (
                  <DataListItem>
                    <DataListLabel>Tax IDs</DataListLabel>
                    <DataListValue>
                      {customer.tax_ids?.map((taxId) => (
                        <div key={taxId.id}>
                          {formatTaxIdType(taxId.type)} {taxId.number}
                        </div>
                      ))}
                    </DataListValue>
                  </DataListItem>
                )}
              </DataList>
              <DataList orientation="vertical" className="gap-4 text-sm">
                <DataListItem>
                  <DataListLabel>Email</DataListLabel>
                  <DataListValue>{customer.email || "-"}</DataListValue>
                </DataListItem>
                <DataListItem>
                  <DataListLabel>Phone</DataListLabel>
                  <DataListValue>{customer.phone || "-"}</DataListValue>
                </DataListItem>
                <DataListItem>
                  <DataListLabel>Billing address</DataListLabel>
                  <DataListValue>
                    <AddressView address={customer.address} />
                  </DataListValue>
                </DataListItem>
              </DataList>

              {customer.shipping && (
                <DataList orientation="vertical" className="gap-4 text-sm">
                  <DataListItem>
                    <DataListLabel>Shipping mame</DataListLabel>
                    <DataListValue>
                      {customer.shipping.name || "-"}
                    </DataListValue>
                  </DataListItem>
                  <DataListItem>
                    <DataListLabel>Shipping phone</DataListLabel>
                    <DataListValue>
                      {customer.shipping.phone || "-"}
                    </DataListValue>
                  </DataListItem>
                  <DataListItem>
                    <DataListLabel>Shipping address</DataListLabel>
                    <DataListValue>
                      <AddressView address={customer.shipping.address} />
                    </DataListValue>
                  </DataListItem>
                </DataList>
              )}
            </div>
          </Section>

          <Section>
            <SectionHeader>
              <SectionTitle>Invoice history</SectionTitle>
            </SectionHeader>
            <div className="grid grid-cols-4 gap-4">
              <MetricCard>
                <MetricCardHeader>
                  <MetricCardTitle>Total invoiced</MetricCardTitle>
                </MetricCardHeader>
                <MetricCardValue>
                  {/* TODO: add metrics after introducing analytics*/}0
                </MetricCardValue>
              </MetricCard>
              <MetricCard>
                <MetricCardHeader>
                  <MetricCardTitle>Total overdue</MetricCardTitle>
                </MetricCardHeader>
                <MetricCardValue>
                  {/* TODO: add metrics after introducing analytics*/}0
                </MetricCardValue>
              </MetricCard>
            </div>
            {invoices && invoices.count > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Number</TableHead>
                    <TableHead>Issue date</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead className="sr-only">Download</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {invoices?.results.map((invoice) => (
                    <TableRow key={invoice.id}>
                      <TableCell>{invoice.number}</TableCell>
                      <TableCell>
                        {formatDate(invoice.issue_date || undefined)}
                      </TableCell>
                      <TableCell>
                        {formatAmount(invoice.total_amount, invoice.currency)}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          disabled={!invoice.pdf_url || isDownloading}
                          onClick={() =>
                            download(
                              invoice.pdf_url || "",
                              `${invoice.number}.pdf`,
                            )
                          }
                        >
                          <DownloadIcon />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <Empty className="border">
                <EmptyHeader>
                  <EmptyTitle>No invoices yet</EmptyTitle>
                  <EmptyDescription>
                    Invoices will appear here once they are generated.
                  </EmptyDescription>
                </EmptyHeader>
              </Empty>
            )}
          </Section>
        </SectionGroup>
      </main>
    </div>
  );
}
