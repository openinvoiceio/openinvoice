import { usePreviewCreditNoteSuspense } from "@/api/endpoints/credit-notes/credit-notes";
import type { CreditNote } from "@/api/models";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  FormCard,
  FormCardContent,
  FormCardHeader,
} from "@/components/ui/form-card";
import { Spinner } from "@/components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { formatDatetime, formatEmailList } from "@/lib/formatters";
import { Suspense, useEffect, useRef, useState } from "react";

export function CreditNotePreview({ creditNote }: { creditNote: CreditNote }) {
  return (
    <FormCard>
      <Tabs defaultValue="pdf">
        <FormCardHeader>
          <TabsList className="w-full">
            <TabsTrigger value="pdf">PDF</TabsTrigger>
            <TabsTrigger value="email">Email</TabsTrigger>
          </TabsList>
        </FormCardHeader>
        <FormCardContent className="pb-4">
          <TabsContent value="pdf">
            <Suspense fallback={<Spinner />}>
              <PdfPreview creditNoteId={creditNote.id} />
            </Suspense>
          </TabsContent>
          <TabsContent value="email">
            <Suspense fallback={<Spinner />}>
              <EmailPreview
                creditNote={creditNote}
                emailTo={
                  creditNote.customer.email ? [creditNote.customer.email] : []
                }
              />
            </Suspense>
          </TabsContent>
        </FormCardContent>
      </Tabs>
    </FormCard>
  );
}

function PdfPreview({ creditNoteId }: { creditNoteId: string }) {
  const { data: srcDoc } = usePreviewCreditNoteSuspense(creditNoteId, {
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

function EmailPreview({
  creditNote,
  emailTo,
  emailCc,
}: {
  creditNote: CreditNote;
  emailTo: string[];
  emailCc?: string[];
}) {
  const { data: srcDoc } = usePreviewCreditNoteSuspense(creditNote.id, {
    format: "email",
  });
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [height, setHeight] = useState<number | undefined>();

  const number = creditNote.number ?? creditNote.id;
  const subject = `Credit note ${number} from ${creditNote.account.name}`;

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
