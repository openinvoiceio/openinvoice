import {
  getTaxRatesListQueryKey,
  getTaxRatesRetrieveQueryKey,
  useArchiveTaxRate,
  useRestoreTaxRate,
} from "@/api/endpoints/tax-rates/tax-rates";
import { ProductCatalogStatusEnum, type TaxRate } from "@/api/models";
import { popModal, pushModal } from "@/components/push-modals";
import {
  ActionDropdown,
  type ActionDropdownProps,
  type DropdownAction,
} from "@/components/ui/action-dropdown";
import { getErrorSummary } from "@/lib/api/errors";
import { useQueryClient } from "@tanstack/react-query";
import { ArchiveIcon, ArchiveRestoreIcon, PencilIcon } from "lucide-react";
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

function useArchiveTaxRateAction(): DropdownAction<TaxRate> {
  const queryClient = useQueryClient();
  const { mutate } = useArchiveTaxRate({
    mutation: {
      onSuccess: async (data) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getTaxRatesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getTaxRatesRetrieveQueryKey(data.id),
          }),
        ]);
        toast.success("Tax rate archived");
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
    visible: (taxRate) => taxRate.status == ProductCatalogStatusEnum.active,
    onSelect: (taxRate) => mutate({ id: taxRate.id }),
  };
}

function useRestoreTaxRateAction(): DropdownAction<TaxRate> {
  const queryClient = useQueryClient();
  const { mutate } = useRestoreTaxRate({
    mutation: {
      onSuccess: async (data) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getTaxRatesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getTaxRatesRetrieveQueryKey(data.id),
          }),
        ]);
        toast.success("Tax rate restored");
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
    visible: (taxRate) => taxRate.status == ProductCatalogStatusEnum.archived,
    onSelect: (taxRate) => mutate({ id: taxRate.id }),
  };
}

export type TaxRateActionKey = "edit" | "archive" | "restore";

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
        { items: [useArchiveTaxRateAction(), useRestoreTaxRateAction()] },
      ]}
      {...props}
    />
  );
}
