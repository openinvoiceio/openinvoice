import {
  getCustomersListQueryKey,
  getCustomersRetrieveQueryKey,
  useUpdateCustomer,
} from "@/api/endpoints/customers/customers";
import {
  getShippingProfilesListQueryKey,
  useDeleteShippingProfile,
} from "@/api/endpoints/shipping-profiles/shipping-profiles";
import type { ShippingProfile } from "@/api/models";
import { popModal, pushModal } from "@/components/push-modals";
import {
  ActionDropdown,
  type ActionDropdownProps,
  type DropdownAction,
} from "@/components/ui/action-dropdown";
import { getErrorSummary } from "@/lib/api/errors";
import { useQueryClient } from "@tanstack/react-query";
import { PencilIcon, StarIcon, Trash2Icon } from "lucide-react";
import { toast } from "sonner";

function useEditShippingProfileAction(): DropdownAction<ShippingProfile> {
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    onSelect: (profile) => pushModal("ShippingProfileEditSheet", { profile }),
  };
}

function useSetDefaultShippingProfileAction({
  customerId,
  defaultProfileId,
}: {
  customerId: string;
  defaultProfileId: string | null;
}): DropdownAction<ShippingProfile> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useUpdateCustomer({
    mutation: {
      onSuccess: async () => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getCustomersListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getCustomersRetrieveQueryKey(customerId),
          }),
          queryClient.invalidateQueries({
            queryKey: getShippingProfilesListQueryKey(),
          }),
        ]);
        toast.success("Shipping profile set as default");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return {
    key: "set-default",
    label: "Set as default",
    icon: StarIcon,
    shortcut: "S",
    hotkey: "s",
    visible: (profile) => profile.id !== defaultProfileId,
    onSelect: (profile) =>
      mutateAsync({
        id: customerId,
        data: { default_shipping_profile_id: profile.id },
      }),
  };
}

function useDeleteShippingProfileAction({
  defaultProfileId,
}: {
  defaultProfileId: string | null;
}): DropdownAction<ShippingProfile> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useDeleteShippingProfile({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getShippingProfilesListQueryKey(),
        });
        toast.success("Shipping profile deleted");
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
    disabled: (profile) => profile.id === defaultProfileId,
    tooltip: (profile) =>
      profile.id === defaultProfileId
        ? "Default profiles cannot be deleted."
        : undefined,
    onSelect: (profile) =>
      pushModal("DestructiveDialog", {
        entity: profile.name || "Shipping profile",
        onConfirm: () => void mutateAsync({ id: profile.id }),
      }),
  };
}

export type ShippingProfileActionKey = "edit" | "set-default" | "delete";

export function ShippingProfileDropdown({
  profile,
  customerId,
  defaultProfileId,
  actions,
  ...props
}: Omit<
  ActionDropdownProps<ShippingProfile>,
  "data" | "sections" | "actions"
> & {
  profile: ShippingProfile;
  customerId: string;
  defaultProfileId: string | null;
  actions?:
    | ShippingProfileActionKey[]
    | Partial<Record<ShippingProfileActionKey, boolean>>;
}) {
  return (
    <ActionDropdown
      data={profile}
      actions={actions}
      sections={[
        { items: [useEditShippingProfileAction()] },
        {
          items: [
            useSetDefaultShippingProfileAction({
              customerId,
              defaultProfileId,
            }),
          ],
        },
        {
          items: [useDeleteShippingProfileAction({ defaultProfileId })],
          danger: true,
        },
      ]}
      {...props}
    />
  );
}
