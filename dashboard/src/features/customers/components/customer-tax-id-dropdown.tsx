import {
  getCustomersRetrieveQueryKey,
  useDeleteCustomerTaxId,
} from "@/api/endpoints/customers/customers";
import type { TaxId } from "@/api/models";
import { pushModal } from "@/components/push-modals";
import {
  ActionDropdown,
  type ActionDropdownProps,
  type DropdownAction,
} from "@/components/ui/action-dropdown";
import { getErrorSummary } from "@/lib/api/errors";
import { formatTaxIdType } from "@/lib/formatters";
import { useQueryClient } from "@tanstack/react-query";
import { PencilIcon, Trash2Icon } from "lucide-react";
import { toast } from "sonner";

function useEditCustomerTaxIdAction({
  customerId,
}: {
  customerId: string;
}): DropdownAction<TaxId> {
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    onSelect: (taxId) =>
      pushModal("CustomerTaxIdCreateSheet", {
        customerId,
        taxId,
      }),
  };
}

function useDeleteCustomerTaxIdAction({
  customerId,
}: {
  customerId: string;
}): DropdownAction<TaxId> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useDeleteCustomerTaxId({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getCustomersRetrieveQueryKey(customerId),
        });
        toast.success("Tax ID deleted");
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
    onSelect: (taxId) =>
      pushModal("DestructiveDialog", {
        entity: `${formatTaxIdType(taxId.type)} ${taxId.number}`,
        onConfirm: () =>
          void mutateAsync({
            customerId,
            id: taxId.id,
          }),
      }),
  };
}

export type CustomerTaxIdActionKey = "edit" | "delete";

export function CustomerTaxIdDropdown({
  taxId,
  customerId,
  actions,
  ...props
}: Omit<ActionDropdownProps<TaxId>, "data" | "sections" | "actions"> & {
  taxId: TaxId;
  customerId: string;
  actions?:
    | CustomerTaxIdActionKey[]
    | Partial<Record<CustomerTaxIdActionKey, boolean>>;
}) {
  return (
    <ActionDropdown<TaxId>
      data={taxId}
      actions={actions}
      sections={[
        { items: [useEditCustomerTaxIdAction({ customerId })] },
        { items: [useDeleteCustomerTaxIdAction({ customerId })], danger: true },
      ]}
      {...props}
    />
  );
}
