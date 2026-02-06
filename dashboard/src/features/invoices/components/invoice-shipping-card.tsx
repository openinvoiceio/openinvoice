import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
  useUpdateInvoice,
} from "@/api/endpoints/invoices/invoices";
import { useShippingRatesRetrieve } from "@/api/endpoints/shipping-rates/shipping-rates";
import {
  ShippingRatesListStatus,
  TaxRatesListStatus,
  type Invoice,
} from "@/api/models";
import { Button } from "@/components/ui/button";
import { ComboboxButton } from "@/components/ui/combobox-button";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import {
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardFooter,
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Spinner } from "@/components/ui/spinner";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { MAX_TAXES } from "@/config/invoices";
import { ShippingProfileCombobox } from "@/features/customers/components/shipping-profile-combobox";
import { ShippingRateCombobox } from "@/features/shipping-rates/components/shipping-rate-combobox";
import { TaxRateCombobox } from "@/features/tax-rates/components/tax-rate-combobox";
import { getErrorSummary } from "@/lib/api/errors";
import { formatAmount, formatPercentage } from "@/lib/formatters";
import { useQueryClient } from "@tanstack/react-query";
import { PlusIcon, XIcon } from "lucide-react";
import { toast } from "sonner";

export function InvoiceShippingCard({ invoice }: { invoice: Invoice }) {
  const queryClient = useQueryClient();
  const customerId = (invoice as { customer_id?: string }).customer_id;
  const shippingRateId = invoice.shipping?.shipping_rate_id;
  const taxRates = invoice.shipping?.tax_rates ?? [];
  const shippingProfile = invoice.shipping?.profile ?? null;
  const shippingProfileId = shippingProfile?.id ?? null;
  const limitReached = taxRates.length >= MAX_TAXES;

  const { data: shippingRate } = useShippingRatesRetrieve(
    shippingRateId || "",
    { query: { enabled: !!shippingRateId } },
  );

  const updateInvoice = useUpdateInvoice({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getInvoicesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getInvoicesRetrieveQueryKey(invoice.id),
        });
        await queryClient.invalidateQueries({
          queryKey: getPreviewInvoiceQueryKey(invoice.id),
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return (
    <FormCard data-testid="invoice-shipping-card">
      <FormCardHeader>
        <FormCardTitle>Shipping</FormCardTitle>
        <FormCardDescription>
          Configure shipping for this invoice.
        </FormCardDescription>
      </FormCardHeader>
      {invoice.shipping ? (
        <>
          <FormCardContent>
            <div className="grid gap-3">
              <div className="grid gap-2 md:grid-cols-2">
                <div className="grid gap-2">
                  <div className="text-sm font-medium">Shipping profile</div>
                  <ShippingProfileCombobox
                    customerId={customerId}
                    selected={shippingProfile}
                    align="start"
                    onSelect={async (selected) => {
                      if (!selected || !shippingRateId || !customerId) return;
                      await updateInvoice.mutateAsync({
                        id: invoice.id,
                        data: {
                          shipping: {
                            shipping_rate_id: shippingRateId,
                            shipping_profile_id: selected.id,
                            tax_rates: taxRates.map((rate) => rate.id),
                          },
                        },
                      });
                    }}
                  >
                    <ComboboxButton>
                      {shippingProfile ? (
                        <span>{shippingProfile.name || "Untitled"}</span>
                      ) : (
                        <span className="text-muted-foreground">
                          Select shipping profile
                        </span>
                      )}
                    </ComboboxButton>
                  </ShippingProfileCombobox>
                </div>
                <div className="grid gap-2">
                  <div className="text-sm font-medium">Shipping rate</div>
                  <ShippingRateCombobox
                    selected={shippingRate}
                    align="start"
                    status={ShippingRatesListStatus.active}
                    onSelect={async (selected) => {
                      if (!selected) return;
                      await updateInvoice.mutateAsync({
                        id: invoice.id,
                        data: {
                          shipping: {
                            shipping_rate_id: selected.id,
                            shipping_profile_id: shippingProfileId,
                            tax_rates: taxRates.map((rate) => rate.id),
                          },
                        },
                      });
                    }}
                  >
                    <ComboboxButton>
                      {shippingRate ? (
                        <div className="flex items-center gap-2">
                          <span>
                            {formatAmount(
                              invoice.shipping_amount,
                              invoice.currency,
                            )}
                          </span>
                          <span className="text-muted-foreground">
                            {shippingRate.name}
                          </span>
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </ComboboxButton>
                  </ShippingRateCombobox>
                </div>
              </div>
              <div className="grid gap-2">
                {taxRates.length > 0 && (
                  <div className="text-sm font-medium">Shipping taxes</div>
                )}
                {taxRates.map((taxRate) => (
                  <div key={taxRate.id} className="flex gap-2 text-sm">
                    <div className="flex flex-grow-1 items-center gap-2">
                      <span>{taxRate.name}</span>
                      <span className="text-muted-foreground">
                        {formatPercentage(taxRate.percentage)}
                      </span>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground size-8"
                      aria-label={`Remove tax ${taxRate.name}`}
                      onClick={() => {
                        if (!shippingRateId) return;
                        updateInvoice.mutate({
                          id: invoice.id,
                          data: {
                            shipping: {
                              shipping_rate_id: shippingRateId,
                              shipping_profile_id: shippingProfileId,
                              tax_rates: taxRates
                                .filter((rate) => rate.id !== taxRate.id)
                                .map((rate) => rate.id),
                            },
                          },
                        });
                      }}
                    >
                      <XIcon />
                    </Button>
                  </div>
                ))}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span tabIndex={limitReached ? 0 : undefined}>
                      <TaxRateCombobox
                        align="start"
                        status={TaxRatesListStatus.active}
                        onSelect={async (selected) => {
                          if (!selected || !shippingRateId) return;
                          await updateInvoice.mutateAsync({
                            id: invoice.id,
                            data: {
                              shipping: {
                                shipping_rate_id: shippingRateId,
                                shipping_profile_id: shippingProfileId,
                                tax_rates: [
                                  ...taxRates.map((rate) => rate.id),
                                  selected.id,
                                ],
                              },
                            },
                          });
                        }}
                      >
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          disabled={limitReached}
                        >
                          {updateInvoice.isPending ? (
                            <Spinner variant="outline" />
                          ) : (
                            <PlusIcon className="text-muted-foreground" />
                          )}
                          Add tax
                        </Button>
                      </TaxRateCombobox>
                    </span>
                  </TooltipTrigger>
                  {limitReached && (
                    <TooltipContent>
                      Maximum {MAX_TAXES} taxes reached
                    </TooltipContent>
                  )}
                </Tooltip>
              </div>
            </div>
          </FormCardContent>
          <FormCardFooter>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="text-destructive"
              onClick={() =>
                updateInvoice.mutateAsync({
                  id: invoice.id,
                  data: { shipping: null },
                })
              }
            >
              Remove shipping
            </Button>
          </FormCardFooter>
        </>
      ) : (
        <>
          <FormCardContent>
            <Empty className="border border-dashed">
              <EmptyHeader>
                <EmptyTitle>No shipping configured</EmptyTitle>
                <EmptyDescription>
                  Add a shipping rate to charge shipping and apply tax.
                </EmptyDescription>
              </EmptyHeader>
            </Empty>
          </FormCardContent>
          <FormCardFooter>
            <ShippingRateCombobox
              align="start"
              status={ShippingRatesListStatus.active}
              onSelect={async (selected) => {
                if (!selected) return;
                await updateInvoice.mutateAsync({
                  id: invoice.id,
                  data: {
                    shipping: {
                      shipping_rate_id: selected.id,
                      tax_rates: [],
                    },
                  },
                });
              }}
            >
              <Button type="button" variant="outline" size="sm">
                {updateInvoice.isPending ? (
                  <Spinner variant="outline" />
                ) : (
                  <PlusIcon className="text-muted-foreground" />
                )}
                Add shipping
              </Button>
            </ShippingRateCombobox>
          </FormCardFooter>
        </>
      )}
    </FormCard>
  );
}
