import {
  getCouponsListQueryKey,
  getCouponsRetrieveQueryKey,
  useArchiveCoupon,
  useDeleteCoupon,
  useRestoreCoupon,
} from "@/api/endpoints/coupons/coupons";
import { ProductCatalogStatusEnum, type Coupon } from "@/api/models";
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

function useArchiveCouponAction(): DropdownAction<Coupon> {
  const queryClient = useQueryClient();
  const { mutate } = useArchiveCoupon({
    mutation: {
      onSuccess: async (data) => {
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: getCouponsListQueryKey() }),
          queryClient.invalidateQueries({
            queryKey: getCouponsRetrieveQueryKey(data.id),
          }),
        ]);
        toast.success("Coupon archived");
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
    visible: (coupon) => coupon.status == ProductCatalogStatusEnum.active,
    onSelect: (coupon) => mutate({ id: coupon.id }),
  };
}

function useRestoreCouponAction(): DropdownAction<Coupon> {
  const queryClient = useQueryClient();
  const { mutate } = useRestoreCoupon({
    mutation: {
      onSuccess: async (data) => {
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: getCouponsListQueryKey() }),
          queryClient.invalidateQueries({
            queryKey: getCouponsRetrieveQueryKey(data.id),
          }),
        ]);
        toast.success("Coupon restored");
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
    visible: (coupon) => coupon.status == ProductCatalogStatusEnum.archived,
    onSelect: (coupon) => mutate({ id: coupon.id }),
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

export type CouponActionKey = "edit" | "archive" | "restore" | "delete";

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
        { items: [useArchiveCouponAction(), useRestoreCouponAction()] },
        { items: [useDeleteCouponAction()], danger: true },
      ]}
      {...props}
    />
  );
}
