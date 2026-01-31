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
  useCloneInvoice,
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
import {
  DropdownMenuItem,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
} from "@/components/ui/dropdown-menu";
import { useDownload } from "@/hooks/use-download";
import { getErrorSummary } from "@/lib/api/errors";
import { formatLanguage } from "@/lib/formatters";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import {
  CheckIcon,
  CopyIcon,
  CopyPlusIcon,
  CreditCardIcon,
  DownloadIcon,
  FileMinusIcon,
  PencilIcon,
  RotateCcwIcon,
  ShredderIcon,
  Trash2Icon,
} from "lucide-react";
import { toast } from "sonner";

function InvoiceDocumentDownloadItem({
  fileId,
  label,
  filename,
  download,
  isDownloading,
}: {
  fileId: string | null;
  label: string;
  filename: string;
  download: (url?: string, filename?: string) => void;
  isDownloading: boolean;
}) {
  const { data: file } = useFilesRetrieve(fileId ?? "", {
    query: { enabled: !!fileId },
  });

  return (
    <DropdownMenuItem
      disabled={!file?.url || isDownloading}
      onClick={() => download(file?.url, filename)}
    >
      <span>{label}</span>
    </DropdownMenuItem>
  );
}

function InvoiceDocumentDownloadSubmenu({
  invoice,
  download,
  isDownloading,
}: {
  invoice: Invoice;
  download: (url?: string, filename?: string) => void;
  isDownloading: boolean;
}) {
  const documents = invoice.documents.filter((document) => document.file_id);
  const filenameBase = invoice.number || "invoice";

  return (
    <DropdownMenuSub>
      <DropdownMenuSubTrigger>
        <DownloadIcon className="text-muted-foreground mr-2 size-4" />
        <span>Download</span>
      </DropdownMenuSubTrigger>
      <DropdownMenuSubContent>
        {documents.map((document) => (
          <InvoiceDocumentDownloadItem
            key={document.id}
            fileId={document.file_id}
            label={formatLanguage(document.language)}
            filename={`${filenameBase}-${document.language}.pdf`}
            download={download}
            isDownloading={isDownloading}
          />
        ))}
      </DropdownMenuSubContent>
    </DropdownMenuSub>
  );
}

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

export function useCloneInvoiceAction(): DropdownAction<Invoice> {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { mutateAsync, isPending } = useCloneInvoice({
    mutation: {
      onSuccess: async (clonedInvoice) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getInvoicesListQueryKey(),
          }),
        ]);

        toast.success("Invoice cloned");
        await navigate({
          to: "/invoices/$id/edit",
          params: { id: clonedInvoice.id },
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return {
    key: "clone",
    label: "Clone",
    icon: CopyPlusIcon,
    disabled: () => isPending,
    onSelect: (invoice) => void mutateAsync({ id: invoice.id }),
  };
}

export function useDownloadInvoiceActions(
  invoice: Invoice,
): DropdownAction<Invoice>[] {
  const documents = invoice.documents.filter((document) => document.file_id);
  const filenameBase = invoice.number || "invoice";
  const [primaryDocument] = documents;
  const { data: file } = useFilesRetrieve(primaryDocument?.file_id ?? "", {
    query: {
      enabled: documents.length === 1 && !!primaryDocument?.file_id,
    },
  });
  const { isDownloading, download } = useDownload();

  if (documents.length === 0) return [];

  if (documents.length === 1) {
    const filename = `${filenameBase}-${primaryDocument?.language}.pdf`;

    return [
      {
        key: "download",
        label: "Download",
        icon: DownloadIcon,
        shortcut: "D",
        hotkey: "d",
        disabled: () => !file?.url || isDownloading,
        onSelect: () => download(file?.url, filename),
      },
    ];
  }

  return [
    {
      key: "download",
      label: "Download",
      icon: DownloadIcon,
      render: () => (
        <InvoiceDocumentDownloadSubmenu
          invoice={invoice}
          download={download}
          isDownloading={isDownloading}
        />
      ),
    },
  ];
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
  | "clone"
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
        {
          items: [
            useEditInvoiceAction(),
            useCopyIdAction(),
            useCloneInvoiceAction(),
          ],
        },
        {
          items: [
            useFinalizeInvoiceAction(),
            useRecordPaymentAction(),
            useIssueCreditNoteAction(),
            useReviseInvoiceAction(),
            useVoidInvoiceAction(),
          ],
        },
        { items: useDownloadInvoiceActions(invoice) },
        { items: [useDeleteInvoiceAction()], danger: true },
      ]}
      {...props}
    />
  );
}
