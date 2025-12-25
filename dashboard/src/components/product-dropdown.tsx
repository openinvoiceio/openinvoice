import {
  getProductsListQueryKey,
  getProductsRetrieveQueryKey,
  useArchiveProduct,
  useDeleteProduct,
  useUnarchiveProduct,
} from "@/api/endpoints/products/products";
import type { Product } from "@/api/models";
import { popModal, pushModal } from "@/components/push-modals";
import {
  ActionDropdown,
  type ActionDropdownProps,
  type DropdownAction,
} from "@/components/ui/action-dropdown";
import { getErrorSummary } from "@/lib/api/errors";
import { useQueryClient } from "@tanstack/react-query";
import {
  ArchiveIcon,
  CopyIcon,
  PencilIcon,
  PlusIcon,
  Trash2Icon,
} from "lucide-react";
import { useCallback } from "react";
import { toast } from "sonner";

function useEditProductAction(): DropdownAction<Product> {
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    onSelect: (product) => pushModal("ProductEditSheet", { product }),
  };
}

export function useCopyIdAction(): DropdownAction<Product> {
  return {
    key: "copy-id",
    label: "Copy ID",
    icon: CopyIcon,
    shortcut: "C",
    hotkey: "c",
    onSelect: async (p) => {
      await navigator.clipboard.writeText(p.id);
      toast.success("Copied to clipboard");
    },
  };
}

function useArchiveToggleProductAction(): DropdownAction<Product> {
  const queryClient = useQueryClient();

  const invalidate = useCallback(
    async (id: string) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: getProductsListQueryKey() }),
        queryClient.invalidateQueries({
          queryKey: getProductsRetrieveQueryKey(id),
        }),
      ]);
    },
    [queryClient],
  );

  const archive = useArchiveProduct({
    mutation: {
      onSuccess: async (p) => {
        await invalidate(p.id);
        toast.success("Product archived");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  const unarchive = useUnarchiveProduct({
    mutation: {
      onSuccess: async (p) => {
        await invalidate(p.id);
        toast.success("Product unarchived");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return {
    key: "archive",
    label: (p) => (p.is_active ? "Archive" : "Unarchive"),
    icon: ArchiveIcon,
    shortcut: "A",
    hotkey: "a",
    onSelect: (p) =>
      p.is_active
        ? archive.mutate({ id: p.id })
        : unarchive.mutate({ id: p.id }),
  };
}

function useNewPriceAction(): DropdownAction<Product> {
  return {
    key: "new-price",
    label: "New price",
    icon: PlusIcon,
    shortcut: "N",
    hotkey: "n",
    visible: (p) => p.is_active,
    onSelect: (p) => pushModal("PriceCreateSheet", { productId: p.id }),
  };
}

function useDeleteProductAction(): DropdownAction<Product> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useDeleteProduct({
    mutation: {
      onSuccess: async (_, { id }) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getProductsListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getProductsRetrieveQueryKey(id),
          }),
        ]);
        toast.success("Product deleted");
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
    visible: (p) => p.prices_count === 0, // only show when deletable
    onSelect: (p) =>
      pushModal("DestructiveDialog", {
        entity: p.name || "Product",
        onConfirm: () => mutateAsync({ id: p.id }),
      }),
  };
}

export type ProductActionKey = "edit" | "archive" | "new-price" | "delete";

export function ProductDropdown({
  product,
  actions,
  ...props
}: Omit<ActionDropdownProps<Product>, "data" | "sections" | "actions"> & {
  product: Product;
  actions?: ProductActionKey[] | Partial<Record<ProductActionKey, boolean>>;
}) {
  return (
    <ActionDropdown<Product>
      data={product}
      actions={actions}
      sections={[
        { items: [useEditProductAction(), useCopyIdAction()] },
        { items: [useNewPriceAction(), useArchiveToggleProductAction()] },
        { items: [useDeleteProductAction()], danger: true },
      ]}
      {...props}
    />
  );
}
