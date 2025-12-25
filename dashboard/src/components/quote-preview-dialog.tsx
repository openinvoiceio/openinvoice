import type { Quote } from "@/api/models";
import { QuotePreview } from "@/components/quote-preview.tsx";
import { Button } from "@/components/ui/button";
import {
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export function QuotePreviewDialog({ quote }: { quote: Quote }) {
  return (
    <DialogContent className="min-w-2xl">
      <DialogHeader>
        <DialogTitle>Quote preview</DialogTitle>
      </DialogHeader>
      <QuotePreview quote={quote} />
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
