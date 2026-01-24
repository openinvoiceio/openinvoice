import {
  getCreditNotesListQueryKey,
  getCreditNotesRetrieveQueryKey,
  useCreateCreditNote,
} from "@/api/endpoints/credit-notes/credit-notes";
import { useFilesRetrieve } from "@/api/endpoints/files/files";
import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
  useCreateInvoiceRevision,
  useDeleteInvoice,
  useFinalizeInvoice,
  useVoidInvoice,
} from "@/api/endpoints/invoices/invoices";
import { InvoiceStatusEnum, type Invoice } from "@/api/models";
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
  CreditCardIcon,
  DownloadIcon,
  FileMinusIcon,
  PencilIcon,
  RotateCcwIcon,
  ShredderIcon,
  Trash2Icon,
} from "lucide-react";
import { toast } from "sonner";

export function useEditInvoiceAction(): DropdownAction<Invoice> {
  const navigate = useNavigate();
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    visible: (i) => i.status === InvoiceStatusEnum.draft,
    onSelect: (i) =>
      navigate({ to: "/invoices/$id/edit", params: { id: i.id } }),
  };
}

export function useCopyIdAction(): DropdownAction<Invoice> {
  return {
    key: "copy-id",
    label: "Copy ID",
    icon: CopyIcon,
    shortcut: "C",
    hotkey: "c",
    onSelect: async (i) => {
      await navigator.clipboard.writeText(i.id);
      toast.success("Copied to clipboard");
    },
  };
}

export function useFinalizeInvoiceAction(): DropdownAction<Invoice> {
  const queryClient = useQueryClient();
  const finalize = useFinalizeInvoice({
    mutation: {
      onSuccess: async (i) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getInvoicesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getInvoicesRetrieveQueryKey(i.id),
          }),
          queryClient.invalidateQueries({
            queryKey: getPreviewInvoiceQueryKey(i.id),
          }),
        ]);
        toast.success("Invoice finalized");
      },
      onError: (e) => {
        const { message, description } = getErrorSummary(e);
        toast.error(message, { description });
      },
    },
  });
  return {
    key: "finalize",
    label: "Finalize",
    icon: CheckIcon,
    visible: (i) => i.status === InvoiceStatusEnum.draft,
    onSelect: (i) => void finalize.mutateAsync({ id: i.id }),
  };
}

export function useRecordPaymentAction(): DropdownAction<Invoice> {
  return {
    key: "record-payment",
    label: "Record payment",
    icon: CreditCardIcon,
    visible: (i) => i.status === InvoiceStatusEnum.open,
    onSelect: (i) => pushModal("PaymentRecordDialog", { invoice: i }),
  };
}

export function useIssueCreditNoteAction(): DropdownAction<Invoice> {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { mutateAsync, isPending } = useCreateCreditNote({
    mutation: {
      onSuccess: async (creditNote) => {
        const invoiceId = creditNote.invoice_id;

        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getCreditNotesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getCreditNotesRetrieveQueryKey(creditNote.id),
          }),
          queryClient.invalidateQueries({
            queryKey: getInvoicesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getCreditNotesListQueryKey({ invoice_id: invoiceId }),
          }),
          queryClient.invalidateQueries({
            queryKey: getInvoicesRetrieveQueryKey(invoiceId),
          }),
          queryClient.invalidateQueries({
            queryKey: getPreviewInvoiceQueryKey(invoiceId),
          }),
        ]);
        toast.success("Credit note created");
        await navigate({
          to: "/credit-notes/$id/edit",
          params: { id: creditNote.id },
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return {
    key: "issue-credit-note",
    label: "Issue credit note",
    icon: FileMinusIcon,
    visible: (invoice) => {
      if (
        !new Set<InvoiceStatusEnum>([
          InvoiceStatusEnum.open,
          InvoiceStatusEnum.paid,
        ]).has(invoice.status)
      ) {
        return false;
      }
      return invoice.outstanding_amount !== "0.00";
    },
    disabled: () => isPending,
    onSelect: (invoice) =>
      void mutateAsync({
        data: {
          invoice_id: invoice.id,
        },
      }),
  };
}

export function useReviseInvoiceAction(): DropdownAction<Invoice> {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { mutateAsync, isPending } = useCreateInvoiceRevision({
    mutation: {
      onSuccess: async (revision) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getInvoicesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getInvoicesRetrieveQueryKey(revision.id),
          }),
          queryClient.invalidateQueries({
            queryKey: getPreviewInvoiceQueryKey(revision.id),
          }),
          ...(revision.previous_revision_id
            ? [
                queryClient.invalidateQueries({
                  queryKey: getInvoicesRetrieveQueryKey(
                    revision.previous_revision_id,
                  ),
                }),
                queryClient.invalidateQueries({
                  queryKey: getPreviewInvoiceQueryKey(
                    revision.previous_revision_id,
                  ),
                }),
              ]
            : []),
        ]);

        toast.success("Invoice revision created");
        await navigate({
          to: "/invoices/$id/edit",
          params: { id: revision.id },
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return {
    key: "revise",
    label: "Revise",
    icon: RotateCcwIcon,
    visible: (i) => i.status === InvoiceStatusEnum.open,
    disabled: () => isPending,
    onSelect: (invoice) => void mutateAsync({ id: invoice.id, data: {} }),
  };
}

export function useDownloadInvoiceAction(
  invoice: Invoice,
): DropdownAction<Invoice> {
  const enabled = !!invoice.pdf_id;
  const { data: file } = useFilesRetrieve(invoice.pdf_id!, {
    query: { enabled },
  });
  const { isDownloading, download } = useDownload();
  const filename = `${invoice.number}.pdf`;
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

export function useVoidInvoiceAction(): DropdownAction<Invoice> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useVoidInvoice({
    mutation: {
      onSuccess: async (i) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getInvoicesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getInvoicesRetrieveQueryKey(i.id),
          }),
          queryClient.invalidateQueries({
            queryKey: getPreviewInvoiceQueryKey(i.id),
          }),
        ]);
        toast.success("Invoice voided");
      },
      onError: (e) => {
        const { message, description } = getErrorSummary(e);
        toast.error(message, { description });
      },
    },
  });
  return {
    key: "void",
    label: "Void",
    icon: ShredderIcon,
    visible: (i) =>
      new Set<InvoiceStatusEnum>([
        InvoiceStatusEnum.draft,
        InvoiceStatusEnum.open,
      ]).has(i.status),
    onSelect: (i) => void mutateAsync({ id: i.id }),
  };
}

export function useDeleteInvoiceAction(): DropdownAction<Invoice> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useDeleteInvoice({
    mutation: {
      onSuccess: async (_, { id }) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getInvoicesRetrieveQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getInvoicesRetrieveQueryKey(id),
          }),
          queryClient.invalidateQueries({
            queryKey: getPreviewInvoiceQueryKey(id),
          }),
        ]);
        toast.success("Invoice deleted");
        popModal();
      },
      onError: (e) => {
        const { message, description } = getErrorSummary(e);
        toast.error(message, { description });
      },
    },
  });
  return {
    key: "delete",
    label: "Delete",
    icon: Trash2Icon,
    disabled: (i) => i.status !== "draft",
    onSelect: (i) =>
      pushModal("DestructiveDialog", {
        entity: i.number || "Invoice",
        onConfirm: () => void mutateAsync({ id: i.id }),
      }),
  };
}

export type InvoiceActionKey =
  | "edit"
  | "copy-id"
  | "finalize"
  | "record-payment"
  | "issue-credit-note"
  | "revise"
  | "download"
  | "void"
  | "delete";

export function InvoiceDropdown({
  invoice,
  actions,
  ...props
}: Omit<ActionDropdownProps<Invoice>, "data" | "sections" | "actions"> & {
  invoice: Invoice;
  actions?: InvoiceActionKey[] | Partial<Record<InvoiceActionKey, boolean>>;
}) {
  return (
    <ActionDropdown
      data={invoice}
      actions={actions}
      sections={[
        { items: [useEditInvoiceAction(), useCopyIdAction()] },
        {
          items: [
            useFinalizeInvoiceAction(),
            useRecordPaymentAction(),
            useIssueCreditNoteAction(),
            useReviseInvoiceAction(),
            useVoidInvoiceAction(),
          ],
        },
        { items: [useDownloadInvoiceAction(invoice)] },
        { items: [useDeleteInvoiceAction()], danger: true },
      ]}
      {...props}
    />
  );
}
