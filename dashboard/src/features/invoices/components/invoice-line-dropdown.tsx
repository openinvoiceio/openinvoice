import { useDeleteInvoiceLine } from "@/api/endpoints/invoice-lines/invoice-lines";
import {
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
} from "@/api/endpoints/invoices/invoices";
import type { Invoice, InvoiceLine } from "@/api/models";
import { popModal, pushModal } from "@/components/push-modals";
import {
  ActionDropdown,
  type ActionDropdownProps,
  type DropdownAction,
} from "@/components/ui/action-dropdown";
import { getErrorSummary } from "@/lib/api/errors";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { BoxIcon, PencilIcon, Trash2Icon } from "lucide-react";
import { toast } from "sonner";

type LineContext = { invoice: Invoice; line: InvoiceLine };

function useEditLineAction(): DropdownAction<LineContext> {
  const navigate = useNavigate();
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    visible: ({ invoice }) => invoice.status === "draft",
    onSelect: ({ invoice }) =>
      navigate({ to: "/invoices/$id/edit", params: { id: invoice.id } }),
  };
}

function useViewProductAction(): DropdownAction<LineContext> {
  const navigate = useNavigate();
  return {
    key: "view-product",
    label: "View product",
    icon: BoxIcon,
    shortcut: "P",
    hotkey: "p",
    visible: ({ line }) => !!line.product_id,
    onSelect: ({ line }) =>
      navigate({ to: "/products/$id", params: { id: line.product_id! } }),
  };
}

function useDeleteLineAction(invoiceId: string): DropdownAction<LineContext> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useDeleteInvoiceLine({
    mutation: {
      onSuccess: async () => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getInvoicesRetrieveQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getInvoicesRetrieveQueryKey(invoiceId),
          }),
          queryClient.invalidateQueries({
            queryKey: getPreviewInvoiceQueryKey(invoiceId),
          }),
        ]);
        toast.success("Invoice line deleted");
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
    shortcut: "⌘⌫",
    hotkey: "mod+backspace",
    visible: ({ invoice }) => invoice.status === "draft",
    onSelect: ({ line }) =>
      pushModal("DestructiveDialog", {
        entity: line.description || "Invoice line",
        onConfirm: () =>
          // pass optional context so onSuccess can invalidate precisely
          mutateAsync({ id: line.id }),
      }),
  };
}

export type InvoiceLineActionKey = "edit" | "view-product" | "delete";

export function InvoiceLineDropdown({
  invoice,
  line,
  actions,
  ...props
}: Omit<ActionDropdownProps<LineContext>, "data" | "sections" | "actions"> & {
  invoice: Invoice;
  line: InvoiceLine;
  actions?:
    | InvoiceLineActionKey[]
    | Partial<Record<InvoiceLineActionKey, boolean>>;
}) {
  return (
    <ActionDropdown<LineContext>
      data={{ invoice, line }}
      actions={actions}
      sections={[
        { items: [useEditLineAction(), useViewProductAction()] },
        { items: [useDeleteLineAction(invoice.id)], danger: true },
      ]}
      {...props}
    />
  );
}
