import type { Invoice } from "@/api/models";
import { Button } from "@/components/ui/button";
import {
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { InvoicePreview } from "@/features/invoices/components/invoice-preview";

export function InvoicePreviewDialog({ invoice }: { invoice: Invoice }) {
  return (
    <DialogContent className="min-w-2xl">
      <DialogHeader>
        <DialogTitle>Invoice preview</DialogTitle>
      </DialogHeader>
      <InvoicePreview invoice={invoice} />
      <DialogFooter>
        <DialogClose asChild>
          <Button type="button" variant="secondary">
            Close
          </Button>
        </DialogClose>
      </DialogFooter>
    </DialogContent>
  );
}
