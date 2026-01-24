import {
  getShippingRatesListQueryKey,
  getShippingRatesRetrieveQueryKey,
  useArchiveShippingRate,
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
import { ArchiveIcon, ArchiveRestoreIcon, PencilIcon } from "lucide-react";
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

export type ShippingRateActionKey = "edit" | "archive" | "restore";

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
      ]}
      {...props}
    />
  );
}
