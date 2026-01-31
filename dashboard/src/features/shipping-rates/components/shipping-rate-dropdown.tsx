import {
  getShippingRatesListQueryKey,
  getShippingRatesRetrieveQueryKey,
  useArchiveShippingRate,
  useDeleteShippingRate,
  useRestoreShippingRate,
} from "@/api/endpoints/shipping-rates/shipping-rates.ts";
import { ProductCatalogStatusEnum, type ShippingRate } from "@/api/models";
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
  PencilIcon,
  Trash2Icon,
} from "lucide-react";
import { toast } from "sonner";

function useEditShippingRateAction(): DropdownAction<ShippingRate> {
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    onSelect: (shippingRate) =>
      pushModal("ShippingRateEditSheet", { shippingRate }),
  };
}

function useArchiveShippingRateAction(): DropdownAction<ShippingRate> {
  const queryClient = useQueryClient();
  const { mutate } = useArchiveShippingRate({
    mutation: {
      onSuccess: async (data) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getShippingRatesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getShippingRatesRetrieveQueryKey(data.id),
          }),
        ]);
        toast.success("Shipping rate archived");
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
    visible: (shippingRate) =>
      shippingRate.status == ProductCatalogStatusEnum.active,
    onSelect: (shippingRate) => mutate({ id: shippingRate.id }),
  };
}

function useRestoreShippingRateAction(): DropdownAction<ShippingRate> {
  const queryClient = useQueryClient();
  const { mutate } = useRestoreShippingRate({
    mutation: {
      onSuccess: async (data) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getShippingRatesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getShippingRatesRetrieveQueryKey(data.id),
          }),
        ]);
        toast.success("Shipping rate restored");
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
    visible: (shippingRate) =>
      shippingRate.status == ProductCatalogStatusEnum.archived,
    onSelect: (shippingRate) => mutate({ id: shippingRate.id }),
  };
}

function useDeleteShippingRateAction(): DropdownAction<ShippingRate> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useDeleteShippingRate({
    mutation: {
      onSuccess: async (_data, { id }) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getShippingRatesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getShippingRatesRetrieveQueryKey(id),
          }),
        ]);
        toast.success("Shipping rate deleted");
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
    onSelect: (shippingRate) =>
      pushModal("DestructiveDialog", {
        entity: shippingRate.name || "Shipping rate",
        onConfirm: () => void mutateAsync({ id: shippingRate.id }),
      }),
  };
}

export type ShippingRateActionKey = "edit" | "archive" | "restore" | "delete";

export function ShippingRateDropdown({
  shippingRate,
  actions,
  ...props
}: Omit<ActionDropdownProps<ShippingRate>, "data" | "sections" | "actions"> & {
  shippingRate: ShippingRate;
  actions?:
    | ShippingRateActionKey[]
    | Partial<Record<ShippingRateActionKey, boolean>>;
}) {
  return (
    <ActionDropdown<ShippingRate>
      data={shippingRate}
      actions={actions}
      sections={[
        { items: [useEditShippingRateAction()] },
        {
          items: [
            useArchiveShippingRateAction(),
            useRestoreShippingRateAction(),
          ],
        },
        { items: [useDeleteShippingRateAction()], danger: true },
      ]}
      {...props}
    />
  );
}
