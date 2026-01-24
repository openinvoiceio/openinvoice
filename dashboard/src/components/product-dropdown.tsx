import {
  getProductsListQueryKey,
  getProductsRetrieveQueryKey,
  useArchiveProduct,
  useDeleteProduct,
  useRestoreProduct,
} from "@/api/endpoints/products/products";
import { ProductCatalogStatusEnum, type Product } from "@/api/models";
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
  ArchiveRestoreIcon,
  CopyIcon,
  PencilIcon,
  PlusIcon,
  Trash2Icon,
} from "lucide-react";
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

function useArchiveProductAction(): DropdownAction<Product> {
  const queryClient = useQueryClient();
  const { mutate } = useArchiveProduct({
    mutation: {
      onSuccess: async (data) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getProductsListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getProductsRetrieveQueryKey(data.id),
          }),
        ]);
        toast.success("Product archived");
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
    label: "Archive",
    icon: ArchiveIcon,
    visible: (product) => product.status == ProductCatalogStatusEnum.active,
    onSelect: (product) => mutate({ id: product.id }),
  };
}

function useRestoreProductAction(): DropdownAction<Product> {
  const queryClient = useQueryClient();
  const { mutate } = useRestoreProduct({
    mutation: {
      onSuccess: async (data) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getProductsListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getProductsRetrieveQueryKey(data.id),
          }),
        ]);
        toast.success("Product restored");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return {
    key: "restore",
    label: "Restore",
    icon: ArchiveRestoreIcon,
    visible: (product) => product.status == ProductCatalogStatusEnum.archived,
    onSelect: (product) => mutate({ id: product.id }),
  };
}

function useNewPriceAction(): DropdownAction<Product> {
  return {
    key: "new-price",
    label: "New price",
    icon: PlusIcon,
    shortcut: "N",
    hotkey: "n",
    visible: (p) => p.status == ProductCatalogStatusEnum.active,
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

export type ProductActionKey =
  | "edit"
  | "archive"
  | "restore"
  | "new-price"
  | "delete";

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
        {
          items: [
            useNewPriceAction(),
            useArchiveProductAction(),
            useRestoreProductAction(),
          ],
        },
        { items: [useDeleteProductAction()], danger: true },
      ]}
      {...props}
    />
  );
}
