import { usePreviewInvoiceSuspense } from "@/api/endpoints/invoices/invoices";
import type { Invoice } from "@/api/models";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  FormCard,
  FormCardContent,
  FormCardHeader,
} from "@/components/ui/form-card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  formatDatetime,
  formatEmailList,
  formatLanguage,
} from "@/lib/formatters";
import { cn } from "@/lib/utils.ts";
import { Suspense, useEffect, useRef, useState } from "react";

export function InvoicePreview({ invoice }: { invoice: Invoice }) {
  const hasDocuments = invoice.documents.length > 0;
  const [selectedLanguage, setSelectedLanguage] = useState<string>(
    invoice.documents[0]?.language,
  );

  return (
    <FormCard>
      <Tabs defaultValue={hasDocuments ? "pdf" : "email"}>
        <FormCardHeader>
          <div
            className={
              hasDocuments
                ? "grid grid-cols-3 items-center gap-2"
                : "flex items-center"
            }
          >
            <TabsList className={cn("w-full", hasDocuments && "col-span-2")}>
              {hasDocuments && (
                <TabsTrigger value="pdf" className="flex-1">
                  PDF
                </TabsTrigger>
              )}
              <TabsTrigger value="email" className="flex-1">
                Email
              </TabsTrigger>
            </TabsList>
            {hasDocuments && (
              <div className="col-span-1 w-full min-w-0">
                <Select
                  value={selectedLanguage}
                  onValueChange={setSelectedLanguage}
                >
                  <SelectTrigger className="h-9 w-full min-w-0">
                    <SelectValue className="block max-w-full truncate" />
                  </SelectTrigger>
                  <SelectContent align="end">
                    {invoice.documents.map((document) => (
                      <SelectItem key={document.id} value={document.language}>
                        {formatLanguage(document.language)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
        </FormCardHeader>
        <FormCardContent className="pb-4">
          {hasDocuments && (
            <TabsContent value="pdf">
              <Suspense fallback={<Spinner />}>
                <PdfPreview invoiceId={invoice.id} />
              </Suspense>
            </TabsContent>
          )}
          <TabsContent value="email">
            <Suspense fallback={<Spinner />}>
              <EmailPreview
                invoice={invoice}
                emailTo={
                  invoice.billing_profile.email
                    ? [invoice.billing_profile.email]
                    : []
                }
              />
            </Suspense>
          </TabsContent>
        </FormCardContent>
      </Tabs>
    </FormCard>
  );
}

function PdfPreview({ invoiceId }: { invoiceId: string }) {
  const { data: srcDoc } = usePreviewInvoiceSuspense(invoiceId, {
    format: "pdf",
  });

  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [height, setHeight] = useState<number | undefined>();

  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;

    const handleLoad = () => {
      const html = iframe.contentDocument?.documentElement;
      if (!html) return;

      const update = () => setHeight(html.scrollHeight);

      const ro = new ResizeObserver(update);
      ro.observe(html);
      return () => ro.disconnect();
    };

    iframe.addEventListener("load", handleLoad);
    return () => iframe.removeEventListener("load", handleLoad);
  }, [srcDoc]);

  return (
    <div className="flex w-full bg-white">
      <iframe
        ref={iframeRef}
        title="Preview"
        srcDoc={srcDoc}
        className="w-full"
        style={{
          maxWidth: "420mm",
          height: height ? `${height}px` : "auto",
          margin: "0.38in",
        }}
      />
    </div>
  );
}

export function EmailPreview({
  invoice,
  emailTo,
  emailCc,
}: {
  invoice: Invoice;
  emailTo: string[];
  emailCc?: string[];
}) {
  const { data: srcDoc } = usePreviewInvoiceSuspense(invoice.id, {
    format: "email",
  });
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [height, setHeight] = useState<number | undefined>();

  const subjectPrefix = invoice.previous_revision_id
    ? "Corrective invoice"
    : "Invoice";
  const subject = `${subjectPrefix} ${invoice.number} from ${invoice.account.name}`;

  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;

    const handleLoad = () => {
      const html = iframe.contentDocument?.documentElement;
      if (!html) return;

      const update = () => {
        setHeight(html.scrollHeight);
      };

      const ro = new ResizeObserver(update);
      ro.observe(html);
      return () => ro.disconnect();
    };

    iframe.addEventListener("load", handleLoad);
    return () => iframe.removeEventListener("load", handleLoad);
  }, [srcDoc]);

  // TODO: modify styles
  return (
    <div className="rounded-lg bg-white px-4 text-black">
      <div className="border-border/25 flex w-full justify-between space-x-2 border-b py-4 text-black">
        <Avatar className="bg-background rounded-full">
          <AvatarImage
            src="/assets/logo-icon.svg"
            alt="INV"
            className="scale-[60%]"
          />
          <AvatarFallback>INV</AvatarFallback>
        </Avatar>
        <div className="flex-1 space-y-0.5">
          <h3 className="font-medium">Invoicence</h3>
          <div className="flex flex-col text-xs">
            <div>
              <span className="font-medium">To: </span>
              <span className="text-muted-foreground">
                {formatEmailList(emailTo)}
              </span>
            </div>
            {emailCc && emailCc.length > 0 && (
              <div>
                <span className="font-medium">Cc: </span>
                <span className="text-muted-foreground">
                  {formatEmailList(emailCc)}
                </span>
              </div>
            )}
          </div>
        </div>
        <p className="text-muted-foreground text-xs">
          {formatDatetime(new Date())}
        </p>
      </div>
      <div className="py-2 font-semibold">{subject}</div>
      <div className="bg-muted">
        <iframe
          ref={iframeRef}
          title="Email Preview"
          srcDoc={srcDoc}
          style={{
            width: "100%",
            height: height ? `${height}px` : "auto",
          }}
        />
      </div>
    </div>
  );
}
