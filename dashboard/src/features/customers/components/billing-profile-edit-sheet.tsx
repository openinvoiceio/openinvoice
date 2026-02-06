import {
  getBillingProfilesListQueryKey,
  useUpdateBillingProfile,
} from "@/api/endpoints/billing-profiles/billing-profiles";
import { useNumberingSystemsRetrieve } from "@/api/endpoints/numbering-systems/numbering-systems";
import {
  CountryEnum,
  CurrencyEnum,
  LanguageEnum,
  NumberingSystemAppliesToEnum,
  type BillingProfile,
} from "@/api/models";
import { CurrencyCombobox } from "@/components/currency-combobox";
import { AddressCountryField } from "@/components/fields/address-country-field";
import { AddressLine1Field } from "@/components/fields/address-line1-field";
import { AddressLine2Field } from "@/components/fields/address-line2-field";
import { AddressLocalityField } from "@/components/fields/address-locality-field";
import { AddressPostalCodeField } from "@/components/fields/address-postal-code-field";
import { AddressStateField } from "@/components/fields/address-state-field";
import { LanguageCombobox } from "@/components/language-combobox";
import { popModal } from "@/components/push-modals";
import { Button } from "@/components/ui/button";
import { ComboboxButton } from "@/components/ui/combobox-button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  FormSheetContent,
  FormSheetDescription,
  FormSheetFooter,
  FormSheetGroup,
  FormSheetHeader,
  FormSheetTitle,
} from "@/components/ui/form-sheet";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { MAX_CUSTOMER_TAX_RATES } from "@/config/customers";
import { MAX_TAX_IDS } from "@/config/tax-ids";
import { CustomerTaxIdsCombobox } from "@/features/customers/components/customer-tax-ids-combobox";
import { NumberingSystemCombobox } from "@/features/settings/components/numbering-system-combobox";
import { TaxRateCombobox } from "@/features/tax-rates/components/tax-rate-combobox";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useId } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  legal_name: z.string().optional(),
  legal_number: z.string().optional(),
  email: z.email("Invalid email address").optional(),
  phone: z.string().optional(),
  currency: z.enum(CurrencyEnum).optional(),
  language: z.enum(LanguageEnum).optional(),
  net_payment_term: z
    .union([z.string(), z.number()])
    .optional()
    .transform((value) => {
      if (value === undefined || value === "") return null;
      return typeof value === "string" ? Number(value) : value;
    })
    .pipe(z.number().int().min(0).max(365).nullable()),
  invoice_numbering_system_id: z.string().uuid().nullable().optional(),
  credit_note_numbering_system_id: z.string().uuid().nullable().optional(),
  tax_ids: z.array(z.string()).optional(),
  tax_rates: z.array(z.string()).optional(),
  address: z.object({
    line1: z.string().optional(),
    line2: z.string().optional(),
    locality: z.string().optional(),
    state: z.string().optional(),
    postalCode: z.string().optional(),
    country: z.enum(CountryEnum).optional(),
  }),
});

type FormValues = z.infer<typeof schema>;

export function BillingProfileEditSheet({
  profile,
  customerId,
}: {
  profile: BillingProfile;
  customerId: string;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      legal_name: profile.legal_name || "",
      legal_number: profile.legal_number || "",
      email: profile.email || "",
      phone: profile.phone || "",
      currency: profile.currency || undefined,
      language: profile.language || undefined,
      net_payment_term: profile.net_payment_term ?? "",
      invoice_numbering_system_id: profile.invoice_numbering_system_id || null,
      credit_note_numbering_system_id:
        profile.credit_note_numbering_system_id || null,
      tax_ids: profile.tax_ids.map((taxId) => taxId.id),
      tax_rates: profile.tax_rates.map((taxRate) => taxRate.id),
      address: {
        line1: profile.address.line1 || "",
        line2: profile.address.line2 || "",
        locality: profile.address.locality || "",
        state: profile.address.state || "",
        postalCode: profile.address.postal_code || "",
        country: profile.address.country || undefined,
      },
    },
  });
  const invoiceNumberingSystemId = form.watch("invoice_numbering_system_id");
  const creditNoteNumberingSystemId = form.watch(
    "credit_note_numbering_system_id",
  );
  const selectedTaxRates = form.watch("tax_rates") ?? [];
  const selectedTaxIds = form.watch("tax_ids") ?? [];
  const taxRatesLimitReached =
    selectedTaxRates.length >= MAX_CUSTOMER_TAX_RATES;
  const taxIdsLimitReached = selectedTaxIds.length >= MAX_TAX_IDS;
  const { data: invoiceNumberingSystem } = useNumberingSystemsRetrieve(
    invoiceNumberingSystemId || "",
    { query: { enabled: !!invoiceNumberingSystemId } },
  );
  const { data: creditNoteNumberingSystem } = useNumberingSystemsRetrieve(
    creditNoteNumberingSystemId || "",
    { query: { enabled: !!creditNoteNumberingSystemId } },
  );
  const { mutateAsync, isPending } = useUpdateBillingProfile({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getBillingProfilesListQueryKey(),
        });
        toast.success("Billing profile updated");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      id: profile.id,
      data: {
        legal_name: values.legal_name || null,
        legal_number: values.legal_number || null,
        email: values.email || null,
        phone: values.phone || null,
        currency: values.currency || null,
        language: values.language || null,
        net_payment_term: values.net_payment_term,
        invoice_numbering_system_id: values.invoice_numbering_system_id || null,
        credit_note_numbering_system_id:
          values.credit_note_numbering_system_id || null,
        tax_ids: values.tax_ids ?? [],
        tax_rates: values.tax_rates ?? [],
        address: {
          line1: values.address.line1 || null,
          line2: values.address.line2 || null,
          locality: values.address.locality || null,
          state: values.address.state || null,
          postal_code: values.address.postalCode || null,
          country: values.address.country || null,
        },
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Edit billing profile</FormSheetTitle>
        <FormSheetDescription>
          Update billing details for this customer.
        </FormSheetDescription>
      </FormSheetHeader>
      <Form {...form}>
        <form id={formId} onSubmit={form.handleSubmit(onSubmit)}>
          <FormSheetGroup>
            <FormField
              control={form.control}
              name="legal_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Legal name</FormLabel>
                  <FormControl>
                    <Input placeholder="Acme Corporation LLC" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="legal_number"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Legal number</FormLabel>
                  <FormControl>
                    <Input placeholder="123456789" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormSheetGroup>
          <FormSheetGroup>
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      placeholder="name@example.com"
                      autoCapitalize="none"
                      autoComplete="email"
                      autoCorrect="off"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="phone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Phone</FormLabel>
                  <FormControl>
                    <Input placeholder="+1234567890" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormSheetGroup>
          <FormSheetGroup className="grid-cols-2">
            <FormField
              control={form.control}
              name="currency"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Currency</FormLabel>
                  <FormControl>
                    <CurrencyCombobox
                      selected={field.value || null}
                      onSelect={async (code) =>
                        field.onChange(code || undefined)
                      }
                    >
                      <ComboboxButton>
                        {field.value ? (
                          <span>{field.value}</span>
                        ) : (
                          <span className="text-muted-foreground">
                            Select currency
                          </span>
                        )}
                      </ComboboxButton>
                    </CurrencyCombobox>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="language"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Language</FormLabel>
                  <FormControl>
                    <LanguageCombobox
                      selected={field.value || null}
                      onSelect={async (language) =>
                        field.onChange(language || undefined)
                      }
                    >
                      <ComboboxButton>
                        {field.value ? (
                          <span>{field.value}</span>
                        ) : (
                          <span className="text-muted-foreground">
                            Select language
                          </span>
                        )}
                      </ComboboxButton>
                    </LanguageCombobox>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormSheetGroup>
          <FormSheetGroup className="grid-cols-2">
            <FormField
              control={form.control}
              name="tax_ids"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tax IDs</FormLabel>
                  <FormControl>
                    <CustomerTaxIdsCombobox
                      customerId={customerId}
                      value={field.value ?? []}
                      onChange={field.onChange}
                      multiple
                    />
                  </FormControl>
                  <FormDescription>
                    {taxIdsLimitReached
                      ? `Limit reached (${MAX_TAX_IDS} tax ids).`
                      : "Select tax IDs to apply by default."}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="tax_rates"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tax rates</FormLabel>
                  <FormControl>
                    <TaxRateCombobox
                      multiple
                      value={field.value ?? []}
                      onChange={field.onChange}
                    >
                      <ComboboxButton className="w-full justify-between gap-2">
                        {selectedTaxRates.length === 0
                          ? "Select tax rates"
                          : `${selectedTaxRates.length} tax rates selected`}
                      </ComboboxButton>
                    </TaxRateCombobox>
                  </FormControl>
                  <FormDescription>
                    {taxRatesLimitReached
                      ? `Limit reached (${MAX_CUSTOMER_TAX_RATES} tax rates).`
                      : "Select default tax rates for this billing profile."}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormSheetGroup>
          <FormSheetGroup>
            <FormField
              control={form.control}
              name="net_payment_term"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Net payment term</FormLabel>
                  <FormControl>
                    <Input type="number" placeholder="30" {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    Default number of days before payment is due.
                  </FormDescription>
                </FormItem>
              )}
            />
          </FormSheetGroup>
          <FormSheetGroup className="grid-cols-2">
            <FormField
              control={form.control}
              name="invoice_numbering_system_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Invoice numbering system</FormLabel>
                  <FormControl>
                    <NumberingSystemCombobox
                      appliesTo={NumberingSystemAppliesToEnum.invoice}
                      selected={invoiceNumberingSystem ?? null}
                      onSelect={async (value) => {
                        field.onChange(value?.id ?? null);
                      }}
                    >
                      <ComboboxButton>
                        {invoiceNumberingSystem ? (
                          <span>
                            {invoiceNumberingSystem.description ||
                              invoiceNumberingSystem.id}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">
                            Select numbering system
                          </span>
                        )}
                      </ComboboxButton>
                    </NumberingSystemCombobox>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="credit_note_numbering_system_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Credit note numbering system</FormLabel>
                  <FormControl>
                    <NumberingSystemCombobox
                      appliesTo={NumberingSystemAppliesToEnum.credit_note}
                      selected={creditNoteNumberingSystem ?? null}
                      onSelect={async (value) => {
                        field.onChange(value?.id ?? null);
                      }}
                    >
                      <ComboboxButton>
                        {creditNoteNumberingSystem ? (
                          <span>
                            {creditNoteNumberingSystem.description ||
                              creditNoteNumberingSystem.id}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">
                            Select numbering system
                          </span>
                        )}
                      </ComboboxButton>
                    </NumberingSystemCombobox>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormSheetGroup>
          <FormSheetGroup>
            <AddressLine1Field name="address.line1" />
            <AddressLine2Field name="address.line2" />
          </FormSheetGroup>
          <FormSheetGroup className="grid-cols-2">
            <AddressLocalityField name="address.locality" />
            <AddressPostalCodeField name="address.postalCode" />
          </FormSheetGroup>
          <FormSheetGroup className="grid-cols-2">
            <AddressCountryField name="address.country" />
            <AddressStateField
              name="address.state"
              countryName="address.country"
            />
          </FormSheetGroup>
        </form>
      </Form>
      <FormSheetFooter>
        <Button type="submit" form={formId} disabled={isPending}>
          {isPending && <Spinner />}
          Save changes
        </Button>
      </FormSheetFooter>
    </FormSheetContent>
  );
}
