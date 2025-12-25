import {
  getPricesListQueryKey,
  getPricesRetrieveQueryKey,
  useArchivePrice,
  useDeletePrice,
  useUnarchivePrice,
} from "@/api/endpoints/prices/prices";
import {
  getProductsListQueryKey,
  getProductsRetrieveQueryKey,
  useUpdateProduct,
} from "@/api/endpoints/products/products";
import type { Price } from "@/api/models";
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
  StarIcon,
  Trash2Icon,
} from "lucide-react";
import { useCallback } from "react";
import { toast } from "sonner";

function useEditPriceAction(): DropdownAction<Price> {
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    onSelect: (price) => pushModal("PriceEditSheet", { price }),
  };
}

export function useCopyIdAction(): DropdownAction<Price> {
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

function useArchiveToggleAction(): DropdownAction<Price> {
  const queryClient = useQueryClient();

  const invalidate = useCallback(
    async (id: string) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: getPricesListQueryKey() }),
        queryClient.invalidateQueries({
          queryKey: getPricesRetrieveQueryKey(id),
        }),
      ]);
    },
    [queryClient],
  );

  const archivePrice = useArchivePrice({
    mutation: {
      onSuccess: async (p) => {
        await invalidate(p.id);
        toast.success("Price archived");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  const unarchivePrice = useUnarchivePrice({
    mutation: {
      onSuccess: async (p) => {
        await invalidate(p.id);
        toast.success("Price unarchived");
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
        ? archivePrice.mutate({ id: p.id })
        : unarchivePrice.mutate({ id: p.id }),
  };
}

function useSetDefaultPriceAction(): DropdownAction<Price> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useUpdateProduct({
    mutation: {
      onSuccess: async (p) => {
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: getPricesListQueryKey() }),
          queryClient.invalidateQueries({
            queryKey: getProductsListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getProductsRetrieveQueryKey(p.id),
          }),
        ]);
        toast.success("Price set as default");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return {
    key: "set-as-default",
    label: "Set as default",
    icon: StarIcon,
    shortcut: "S",
    hotkey: "s",
    visible: (p) =>
      p.is_active && p.product.is_active && p.id !== p.product.default_price_id,
    onSelect: (p) =>
      void mutateAsync({
        id: p.product.id,
        data: { default_price_id: p.id },
      }),
  };
}

function useDeletePriceAction(): DropdownAction<Price> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useDeletePrice({
    mutation: {
      onSuccess: async (p) => {
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: getPricesListQueryKey() }),
          queryClient.invalidateQueries({
            queryKey: getPricesRetrieveQueryKey(p.id),
          }),
        ]);
        toast.success("Price deleted");
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
    visible: (p) => !p.is_used, // hide entirely when used
    onSelect: (p) =>
      pushModal("DestructiveDialog", {
        entity: p.code || p.id,
        onConfirm: () => mutateAsync({ id: p.id }),
      }),
  };
}

export type PriceActionKey =
  | "edit"
  | "copy-id"
  | "archive"
  | "set-as-default"
  | "delete";

export function PriceDropdown({
  price,
  actions,
  ...props
}: Omit<ActionDropdownProps<Price>, "data" | "sections" | "actions"> & {
  price: Price;
  actions?: PriceActionKey[] | Partial<Record<PriceActionKey, boolean>>;
}) {
  return (
    <ActionDropdown<Price>
      data={price}
      actions={actions}
      sections={[
        { items: [useEditPriceAction(), useCopyIdAction()] },
        { items: [useSetDefaultPriceAction(), useArchiveToggleAction()] },
        { items: [useDeletePriceAction()], danger: true },
      ]}
      {...props}
    />
  );
}
