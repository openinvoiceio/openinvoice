import type { CreditNote } from "@/api/models";
import { Button } from "@/components/ui/button";
import {
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { CreditNotePreview } from "@/features/credit-notes/components/credit-note-preview";

export function CreditNotePreviewDialog({
  creditNote,
}: {
  creditNote: CreditNote;
}) {
  return (
    <DialogContent className="min-w-2xl">
      <DialogHeader>
        <DialogTitle>Credit note preview</DialogTitle>
      </DialogHeader>
      <CreditNotePreview creditNote={creditNote} />
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
