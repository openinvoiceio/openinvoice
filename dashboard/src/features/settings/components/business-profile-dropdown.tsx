import {
  getAccountsListQueryKey,
  getAccountsRetrieveQueryKey,
  useUpdateAccount,
} from "@/api/endpoints/accounts/accounts";
import {
  getBusinessProfilesListQueryKey,
  useDeleteBusinessProfile,
} from "@/api/endpoints/business-profiles/business-profiles";
import type { BusinessProfile } from "@/api/models";
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

function useEditBusinessProfileAction({
  accountId,
}: {
  accountId: string;
}): DropdownAction<BusinessProfile> {
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    onSelect: (profile) =>
      pushModal("BusinessProfileEditSheet", { profile, accountId }),
  };
}

function useSetDefaultBusinessProfileAction({
  accountId,
  defaultProfileId,
}: {
  accountId: string;
  defaultProfileId: string | null;
}): DropdownAction<BusinessProfile> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useUpdateAccount({
    mutation: {
      onSuccess: async () => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getAccountsListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getAccountsRetrieveQueryKey(accountId),
          }),
          queryClient.invalidateQueries({
            queryKey: getBusinessProfilesListQueryKey(),
          }),
        ]);
        toast.success("Business profile set as default");
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
        id: accountId,
        data: { default_business_profile_id: profile.id },
      }),
  };
}

function useDeleteBusinessProfileAction({
  defaultProfileId,
}: {
  defaultProfileId: string | null;
}): DropdownAction<BusinessProfile> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useDeleteBusinessProfile({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getBusinessProfilesListQueryKey(),
        });
        toast.success("Business profile deleted");
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
        entity: profile.legal_name || profile.email || "Business profile",
        onConfirm: () => void mutateAsync({ id: profile.id }),
      }),
  };
}

export type BusinessProfileActionKey = "edit" | "set-default" | "delete";

export function BusinessProfileDropdown({
  profile,
  accountId,
  defaultProfileId,
  actions,
  ...props
}: Omit<
  ActionDropdownProps<BusinessProfile>,
  "data" | "sections" | "actions"
> & {
  profile: BusinessProfile;
  accountId: string;
  defaultProfileId: string | null;
  actions?:
    | BusinessProfileActionKey[]
    | Partial<Record<BusinessProfileActionKey, boolean>>;
}) {
  return (
    <ActionDropdown
      data={profile}
      actions={actions}
      sections={[
        {
          items: [useEditBusinessProfileAction({ accountId })],
        },
        {
          items: [
            useSetDefaultBusinessProfileAction({
              accountId,
              defaultProfileId,
            }),
          ],
        },
        {
          items: [useDeleteBusinessProfileAction({ defaultProfileId })],
          danger: true,
        },
      ]}
      {...props}
    />
  );
}
