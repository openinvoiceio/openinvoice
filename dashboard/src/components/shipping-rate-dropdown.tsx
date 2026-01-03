import {
  getShippingRatesListQueryKey,
  useArchiveShippingRate,
  useUnarchiveShippingRate,
} from "@/api/endpoints/shipping-rates/shipping-rates.ts";
import type { ShippingRate } from "@/api/models";
import { popModal, pushModal } from "@/components/push-modals";
import {
  ActionDropdown,
  type ActionDropdownProps,
  type DropdownAction,
} from "@/components/ui/action-dropdown";
import { getErrorSummary } from "@/lib/api/errors";
import { useQueryClient } from "@tanstack/react-query";
import { ArchiveIcon, PencilIcon } from "lucide-react";
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

function useArchiveToggleShippingRateAction(): DropdownAction<ShippingRate> {
  const queryClient = useQueryClient();

  const archiveShippingRate = useArchiveShippingRate({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getShippingRatesListQueryKey(),
        });
        toast.success("Shipping rate archived");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  const unarchiveShippingRate = useUnarchiveShippingRate({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getShippingRatesListQueryKey(),
        });
        toast.success("Shipping rate unarchived");
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
    label: (r) => (r.is_active ? "Archive" : "Unarchive"),
    icon: ArchiveIcon,
    shortcut: "A",
    hotkey: "a",
    onSelect: (r) =>
      r.is_active
        ? archiveShippingRate.mutate({ id: r.id })
        : unarchiveShippingRate.mutate({ id: r.id }),
  };
}

export type ShippingRateActionKey = "edit" | "archive";

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
        { items: [useArchiveToggleShippingRateAction()] },
      ]}
      {...props}
    />
  );
}
