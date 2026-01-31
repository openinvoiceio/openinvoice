import {
  getTaxRatesListQueryKey,
  useUpdateTaxRate,
} from "@/api/endpoints/tax-rates/tax-rates";
import { CountryEnum, type TaxRate } from "@/api/models";
import { CountryCombobox } from "@/components/country-combobox.tsx";
import { popModal } from "@/components/push-modals";
import { Button } from "@/components/ui/button";
import { ComboboxButton } from "@/components/ui/combobox-button.tsx";
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
import { Input, inputClassName } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { getErrorSummary } from "@/lib/api/errors";
import { formatCountry } from "@/lib/formatters";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useId } from "react";
import CurrencyInput from "react-currency-input-field";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  percentage: z.string(),
  country: z.enum(CountryEnum).optional(),
});

type FormValues = z.infer<typeof schema>;

export function TaxRateEditSheet({ taxRate }: { taxRate: TaxRate }) {
  const formId = useId();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: taxRate.name,
      description: taxRate.description || "",
      percentage: taxRate.percentage,
      country: taxRate.country || undefined,
    },
  });

  const { isPending, mutateAsync } = useUpdateTaxRate({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getTaxRatesListQueryKey(),
        });
        toast.success("Tax rate updated");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      id: taxRate.id,
      data: {
        name: values.name,
        description: values.description || null,
        country: values.country || null,
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Edit Tax Rate</FormSheetTitle>
        <FormSheetDescription>
          Update the tax rate details.
        </FormSheetDescription>
      </FormSheetHeader>
      <Form {...form}>
        <form id={formId} onSubmit={form.handleSubmit(onSubmit)}>
          <FormSheetGroup>
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input type="text" placeholder="VAT" {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    The tax label shown on customer invoices.
                  </FormDescription>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="percentage"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Percentage</FormLabel>
                  <FormControl>
                    <div className="relative">
                      <CurrencyInput
                        placeholder="20"
                        className={inputClassName}
                        value={field.value}
                        onValueChange={(value) => {
                          field.onChange(value || "0");
                        }}
                        maxLength={3}
                        decimalsLimit={1}
                        allowNegativeValue={false}
                        disableAbbreviations={true}
                        disabled={true}
                      />
                      <div className="text-muted-foreground absolute inset-y-0 end-0 flex items-center pe-3 text-sm">
                        %
                      </div>
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="country"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Country</FormLabel>
                  <CountryCombobox
                    selected={field.value}
                    onSelect={async (value) => field.onChange(value ?? "")}
                  >
                    <ComboboxButton>
                      {field.value ? (
                        <span>{formatCountry(field.value)}</span>
                      ) : (
                        <span className="text-muted-foreground">
                          Select country
                        </span>
                      )}
                    </ComboboxButton>
                  </CountryCombobox>
                  <FormMessage />
                  <FormDescription>
                    Country where this tax rate is valid.
                  </FormDescription>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea placeholder="Optional description" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormSheetGroup>
        </form>
      </Form>
      <FormSheetFooter>
        <Button type="submit" form={formId} disabled={isPending}>
          {isPending && <Spinner />}
          Submit
        </Button>
      </FormSheetFooter>
    </FormSheetContent>
  );
}
