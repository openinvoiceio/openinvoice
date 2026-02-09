import {
  getAccountsAddressesListQueryKey,
  useDeleteAccountAddress,
} from "@/api/endpoints/accounts/accounts";
import type { AddressDetail } from "@/api/models";
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

function useEditAccountAddressAction({
  accountId,
}: {
  accountId: string;
}): DropdownAction<AddressDetail> {
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    onSelect: (address) =>
      pushModal("AccountAddressEditSheet", { address, accountId }),
  };
}

function useDeleteAccountAddressAction({
  accountId,
}: {
  accountId: string;
}): DropdownAction<AddressDetail> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useDeleteAccountAddress({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getAccountsAddressesListQueryKey(accountId),
        });
        toast.success("Address deleted");
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
    onSelect: (address) =>
      pushModal("DestructiveDialog", {
        entity: address.line1 || address.locality || "Address",
        onConfirm: () => void mutateAsync({ accountId, id: address.id }),
      }),
  };
}

export type AccountAddressActionKey = "edit" | "delete";

export function AccountAddressDropdown({
  address,
  accountId,
  actions,
  ...props
}: Omit<ActionDropdownProps<AddressDetail>, "data" | "sections" | "actions"> & {
  address: AddressDetail;
  accountId: string;
  actions?:
    | AccountAddressActionKey[]
    | Partial<Record<AccountAddressActionKey, boolean>>;
}) {
  return (
    <ActionDropdown
      data={address}
      actions={actions}
      sections={[
        {
          items: [useEditAccountAddressAction({ accountId })],
        },
        {
          items: [useDeleteAccountAddressAction({ accountId })],
          danger: true,
        },
      ]}
      {...props}
    />
  );
}
