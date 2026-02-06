import {
  getBillingProfilesListQueryKey,
  useDeleteBillingProfile,
} from "@/api/endpoints/billing-profiles/billing-profiles";
import {
  getCustomersListQueryKey,
  getCustomersRetrieveQueryKey,
  useUpdateCustomer,
} from "@/api/endpoints/customers/customers";
import type { BillingProfile } from "@/api/models";
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

function useEditBillingProfileAction({
  customerId,
}: {
  customerId: string;
}): DropdownAction<BillingProfile> {
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    onSelect: (profile) =>
      pushModal("BillingProfileEditSheet", { profile, customerId }),
  };
}

function useSetDefaultBillingProfileAction({
  customerId,
  defaultProfileId,
}: {
  customerId: string;
  defaultProfileId: string | null;
}): DropdownAction<BillingProfile> {
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
            queryKey: getBillingProfilesListQueryKey(),
          }),
        ]);
        toast.success("Billing profile set as default");
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
        data: { default_billing_profile_id: profile.id },
      }),
  };
}

function useDeleteBillingProfileAction({
  defaultProfileId,
}: {
  defaultProfileId: string | null;
}): DropdownAction<BillingProfile> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useDeleteBillingProfile({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getBillingProfilesListQueryKey(),
        });
        toast.success("Billing profile deleted");
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
        entity: profile.legal_name || profile.email || "Billing profile",
        onConfirm: () => void mutateAsync({ id: profile.id }),
      }),
  };
}

export type BillingProfileActionKey = "edit" | "set-default" | "delete";

export function BillingProfileDropdown({
  profile,
  customerId,
  defaultProfileId,
  actions,
  ...props
}: Omit<
  ActionDropdownProps<BillingProfile>,
  "data" | "sections" | "actions"
> & {
  profile: BillingProfile;
  customerId: string;
  defaultProfileId: string | null;
  actions?:
    | BillingProfileActionKey[]
    | Partial<Record<BillingProfileActionKey, boolean>>;
}) {
  return (
    <ActionDropdown
      data={profile}
      actions={actions}
      sections={[
        {
          items: [useEditBillingProfileAction({ customerId })],
        },
        {
          items: [
            useSetDefaultBillingProfileAction({
              customerId,
              defaultProfileId,
            }),
          ],
        },
        {
          items: [useDeleteBillingProfileAction({ defaultProfileId })],
          danger: true,
        },
      ]}
      {...props}
    />
  );
}
