import {
  getCouponsListQueryKey,
  getCouponsRetrieveQueryKey,
  useDeleteCoupon,
} from "@/api/endpoints/coupons/coupons";
import type { Coupon } from "@/api/models";
import { popModal, pushModal } from "@/components/push-modals";
import {
  ActionDropdown,
  type ActionDropdownProps,
  type DropdownAction,
} from "@/components/ui/action-dropdown";
import { getErrorSummary } from "@/lib/api/errors";
import { useQueryClient } from "@tanstack/react-query";
import { PencilIcon, Trash2Icon } from "lucide-react";
import { toast } from "sonner";

function useEditCouponAction(): DropdownAction<Coupon> {
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    onSelect: (coupon) => pushModal("CouponEditSheet", { coupon }),
  };
}

function useDeleteCouponAction(): DropdownAction<Coupon> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useDeleteCoupon({
    mutation: {
      onSuccess: async (_data, { id }) => {
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: getCouponsListQueryKey() }),
          queryClient.invalidateQueries({
            queryKey: getCouponsRetrieveQueryKey(id),
          }),
        ]);
        toast.success("Coupon deleted");
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
    onSelect: (coupon) =>
      pushModal("DestructiveDialog", {
        entity: coupon.name || "Coupon",
        onConfirm: () => void mutateAsync({ id: coupon.id }),
      }),
  };
}

export type CouponActionKey = "edit" | "delete";

export function CouponDropdown({
  coupon,
  actions,
  ...props
}: Omit<ActionDropdownProps<Coupon>, "data" | "sections" | "actions"> & {
  coupon: Coupon;
  actions?: CouponActionKey[] | Partial<Record<CouponActionKey, boolean>>;
}) {
  return (
    <ActionDropdown
      data={coupon}
      actions={actions}
      sections={[
        { items: [useEditCouponAction()] },
        { items: [useDeleteCouponAction()], danger: true },
      ]}
      {...props}
    />
  );
}
