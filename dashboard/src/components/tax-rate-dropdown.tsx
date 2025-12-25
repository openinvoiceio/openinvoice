import {
  getTaxRatesListQueryKey,
  useArchiveTaxRate,
  useUnarchiveTaxRate,
} from "@/api/endpoints/tax-rates/tax-rates";
import type { TaxRate } from "@/api/models";
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

function useEditTaxRateAction(): DropdownAction<TaxRate> {
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    onSelect: (taxRate) => pushModal("TaxRateEditSheet", { taxRate }),
  };
}

function useArchiveToggleTaxRateAction(): DropdownAction<TaxRate> {
  const queryClient = useQueryClient();

  const archiveTaxRate = useArchiveTaxRate({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getTaxRatesListQueryKey(),
        });
        toast.success("Tax rate archived");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  const unarchiveTaxRate = useUnarchiveTaxRate({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getTaxRatesListQueryKey(),
        });
        toast.success("Tax rate unarchived");
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
    label: (t) => (t.is_active ? "Archive" : "Unarchive"),
    icon: ArchiveIcon,
    shortcut: "A",
    hotkey: "a",
    onSelect: (t) =>
      t.is_active
        ? archiveTaxRate.mutate({ id: t.id })
        : unarchiveTaxRate.mutate({ id: t.id }),
  };
}

export type TaxRateActionKey = "edit" | "archive";

export function TaxRateDropdown({
  taxRate,
  actions,
  ...props
}: Omit<ActionDropdownProps<TaxRate>, "data" | "sections" | "actions"> & {
  taxRate: TaxRate;
  actions?: TaxRateActionKey[] | Partial<Record<TaxRateActionKey, boolean>>;
}) {
  return (
    <ActionDropdown<TaxRate>
      data={taxRate}
      actions={actions}
      sections={[
        { items: [useEditTaxRateAction()] },
        { items: [useArchiveToggleTaxRateAction()] },
      ]}
      {...props}
    />
  );
}
