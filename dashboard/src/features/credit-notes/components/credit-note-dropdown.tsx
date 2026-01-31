import {
  getCreditNotesListQueryKey,
  getCreditNotesRetrieveQueryKey,
  getPreviewCreditNoteQueryKey,
  useDeleteCreditNote,
  useIssueCreditNote,
  useVoidCreditNote,
} from "@/api/endpoints/credit-notes/credit-notes";
import { useFilesRetrieve } from "@/api/endpoints/files/files";
import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
} from "@/api/endpoints/invoices/invoices.ts";
import { CreditNoteStatusEnum, type CreditNote } from "@/api/models";
import { popModal, pushModal } from "@/components/push-modals";
import {
  ActionDropdown,
  type ActionDropdownProps,
  type DropdownAction,
} from "@/components/ui/action-dropdown";
import { useDownload } from "@/hooks/use-download";
import { getErrorSummary } from "@/lib/api/errors";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import {
  CheckIcon,
  CopyIcon,
  DownloadIcon,
  PencilIcon,
  ShredderIcon,
  Trash2Icon,
} from "lucide-react";
import { toast } from "sonner";

export function useEditCreditNoteAction(): DropdownAction<CreditNote> {
  const navigate = useNavigate();
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    visible: (creditNote) => creditNote.status === CreditNoteStatusEnum.draft,
    onSelect: (creditNote) =>
      navigate({ to: "/credit-notes/$id/edit", params: { id: creditNote.id } }),
  };
}

export function useCopyCreditNoteIdAction(): DropdownAction<CreditNote> {
  return {
    key: "copy-id",
    label: "Copy ID",
    icon: CopyIcon,
    shortcut: "C",
    hotkey: "c",
    onSelect: async (creditNote) => {
      await navigator.clipboard.writeText(creditNote.id);
      toast.success("Copied to clipboard");
    },
  };
}

export function useFinalizeCreditNoteAction(): DropdownAction<CreditNote> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useIssueCreditNote({
    mutation: {
      onSuccess: async (creditNote) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getCreditNotesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getCreditNotesRetrieveQueryKey(creditNote.id),
          }),
          queryClient.invalidateQueries({
            queryKey: getPreviewCreditNoteQueryKey(creditNote.id),
          }),
          queryClient.invalidateQueries({
            queryKey: getInvoicesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getInvoicesRetrieveQueryKey(creditNote.invoice_id),
          }),
        ]);
        toast.success("Credit note finalized");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });
  return {
    key: "finalize",
    label: "Finalize",
    icon: CheckIcon,
    visible: (creditNote) => creditNote.status === CreditNoteStatusEnum.draft,
    onSelect: (creditNote) => void mutateAsync({ id: creditNote.id, data: {} }),
  };
}

export function useDownloadCreditNoteAction(
  creditNote: CreditNote,
): DropdownAction<CreditNote> {
  const enabled = !!creditNote.pdf_id;
  const { data: file } = useFilesRetrieve(creditNote.pdf_id ?? "", {
    query: { enabled },
  });
  const { isDownloading, download } = useDownload();
  const filename = `${creditNote.number}.pdf`;
  return {
    key: "download",
    label: "Download",
    icon: DownloadIcon,
    shortcut: "D",
    hotkey: "d",
    visible: () => enabled,
    disabled: () => !file?.url || isDownloading,
    onSelect: () => download(file?.url, filename),
  };
}

export function useVoidCreditNoteAction(): DropdownAction<CreditNote> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useVoidCreditNote({
    mutation: {
      onSuccess: async (creditNote) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getCreditNotesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getCreditNotesRetrieveQueryKey(creditNote.id),
          }),
          queryClient.invalidateQueries({
            queryKey: getPreviewCreditNoteQueryKey(creditNote.id),
          }),
        ]);
        toast.success("Credit note voided");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });
  return {
    key: "void",
    label: "Void",
    icon: ShredderIcon,
    visible: (creditNote) => creditNote.status === CreditNoteStatusEnum.issued,
    onSelect: (creditNote) => void mutateAsync({ id: creditNote.id, data: {} }),
  };
}

export function useDeleteCreditNoteAction(): DropdownAction<CreditNote> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useDeleteCreditNote({
    mutation: {
      onSuccess: async (_, { id }) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getCreditNotesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getCreditNotesRetrieveQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getCreditNotesRetrieveQueryKey(id),
          }),
        ]);
        toast.success("Credit note deleted");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });
  return {
    key: "delete",
    label: "Delete",
    icon: Trash2Icon,
    disabled: (creditNote) => creditNote.status !== CreditNoteStatusEnum.draft,
    onSelect: (creditNote) =>
      pushModal("DestructiveDialog", {
        entity: creditNote.number || "Credit note",
        onConfirm: () => void mutateAsync({ id: creditNote.id }),
      }),
  };
}

export type CreditNoteActionKey =
  | "edit"
  | "copy-id"
  | "finalize"
  | "download"
  | "void"
  | "delete";

export function CreditNoteDropdown({
  creditNote,
  actions,
  ...props
}: Omit<ActionDropdownProps<CreditNote>, "data" | "sections" | "actions"> & {
  creditNote: CreditNote;
  actions?:
    | CreditNoteActionKey[]
    | Partial<Record<CreditNoteActionKey, boolean>>;
}) {
  return (
    <ActionDropdown
      data={creditNote}
      actions={actions}
      sections={[
        { items: [useEditCreditNoteAction(), useCopyCreditNoteIdAction()] },
        { items: [useFinalizeCreditNoteAction(), useVoidCreditNoteAction()] },
        { items: [useDownloadCreditNoteAction(creditNote)] },
        { items: [useDeleteCreditNoteAction()], danger: true },
      ]}
      {...props}
    />
  );
}
