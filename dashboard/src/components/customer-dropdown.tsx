import {
  getCustomersListQueryKey,
  getCustomersRetrieveQueryKey,
  useDeleteCustomer,
} from "@/api/endpoints/customers/customers";
import type { Customer } from "@/api/models";
import { pushModal } from "@/components/push-modals";
import {
  ActionDropdown,
  type ActionDropdownProps,
  type DropdownAction,
} from "@/components/ui/action-dropdown";
import { getErrorSummary } from "@/lib/api/errors";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { CopyIcon, PencilIcon, Trash2Icon } from "lucide-react";
import { toast } from "sonner";

function useEditCustomerAction(): DropdownAction<Customer> {
  const navigate = useNavigate();
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    onSelect: (c) =>
      navigate({ to: "/customers/$id/edit", params: { id: c.id } }),
  };
}

function useCopyCustomerIdAction(): DropdownAction<Customer> {
  return {
    key: "copy-id",
    label: "Copy ID",
    icon: CopyIcon,
    shortcut: "C",
    hotkey: "c",
    onSelect: async (c) => {
      await navigator.clipboard.writeText(c.id);
      toast.success("Copied to clipboard");
    },
  };
}

function useDeleteCustomerAction(): DropdownAction<Customer> {
  const queryClient = useQueryClient();
  const { mutateAsync } = useDeleteCustomer({
    mutation: {
      onSuccess: async (_data, { id }) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getCustomersListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getCustomersRetrieveQueryKey(id),
          }),
        ]);
        toast.success("Customer deleted");
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
    onSelect: (customer) =>
      pushModal("DestructiveDialog", {
        entity: customer.name || "Customer",
        onConfirm: () => void mutateAsync({ id: customer.id }),
      }),
  };
}

export type CustomerActionKey = "edit" | "copy-id" | "delete";

export function CustomerDropdown({
  customer,
  actions,
  ...props
}: Omit<ActionDropdownProps<Customer>, "data" | "sections" | "actions"> & {
  customer: Customer;
  actions?: CustomerActionKey[] | Partial<Record<CustomerActionKey, boolean>>;
}) {
  return (
    <ActionDropdown<Customer>
      data={customer}
      actions={actions}
      sections={[
        { items: [useEditCustomerAction(), useCopyCustomerIdAction()] },
        { items: [useDeleteCustomerAction()], danger: true },
      ]}
      {...props}
    />
  );
}
