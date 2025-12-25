import { popModal } from "@/components/push-modals";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { VariantProps } from "class-variance-authority";
import { useState } from "react";

interface AlertDialogProps extends VariantProps<typeof buttonVariants> {
  entity: string;
  confirmationValue?: string;
  onConfirm?: () => void;
}

export function DestructiveDialog({
  entity,
  confirmationValue,
  onConfirm,
}: AlertDialogProps) {
  const [value, setValue] = useState("");

  function onSubmit() {
    if (confirmationValue && value !== confirmationValue) return;
    onConfirm?.();
    popModal();
  }

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Are you sure about deleting "{entity}"?</DialogTitle>
        <DialogDescription>
          This action cannot be undone. This will permanently remove the entry
          from the database.
        </DialogDescription>
      </DialogHeader>
      {confirmationValue && (
        <form className="space-y-1">
          <p className="text-muted-foreground text-sm">
            Please write &apos;
            <span className="font-semibold">{confirmationValue}</span>
            &apos; to confirm
          </p>
          <Input value={value} onChange={(e) => setValue(e.target.value)} />
        </form>
      )}
      <DialogFooter>
        <DialogClose asChild>
          <Button variant="ghost">Cancel</Button>
        </DialogClose>
        <Button
          type="button"
          className="bg-destructive hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60 text-white shadow-xs"
          onClick={onSubmit}
          disabled={confirmationValue ? value !== confirmationValue : false}
        >
          Delete
        </Button>
      </DialogFooter>
    </DialogContent>
  );
}
