import {
  getAccountsRetrieveQueryKey,
  useCreateAccountTaxId,
} from "@/api/endpoints/accounts/accounts";
import { CountryEnum, type TaxId } from "@/api/models";
import { CountryCombobox } from "@/components/country-combobox.tsx";
import { popModal } from "@/components/push-modals";
import { Button } from "@/components/ui/button";
import { ComboboxButton } from "@/components/ui/combobox-button.tsx";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  FormSheetContent,
  FormSheetFooter,
  FormSheetGroup,
  FormSheetHeader,
  FormSheetTitle,
} from "@/components/ui/form-sheet";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { TAX_ID_NUMBER_HINTS, TAX_ID_TYPES } from "@/config/tax-ids";
import { getErrorSummary } from "@/lib/api/errors";
import { formatCountry, formatTaxIdType } from "@/lib/formatters";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useId } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  type: z.enum(TAX_ID_TYPES),
  number: z.string().min(1, "Number is required"),
  country: z.enum(CountryEnum).optional(),
});

export type TaxIdFormValues = z.infer<typeof schema>;

export function AccountTaxIdCreateSheet({
  accountId,
  onSuccess,
}: {
  accountId: string;
  onSuccess?: (taxId: TaxId) => void;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const form = useForm<TaxIdFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      type: undefined,
      number: "",
      country: undefined,
    },
  });

  const selectedType = form.watch("type");

  const { isPending, mutateAsync } = useCreateAccountTaxId({
    mutation: {
      onSuccess: async (taxId) => {
        await queryClient.invalidateQueries({
          queryKey: getAccountsRetrieveQueryKey(accountId),
        });
        onSuccess?.(taxId);
        toast.success("Tax ID created");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  async function onSubmit(values: TaxIdFormValues) {
    if (isPending) return;
    await mutateAsync({
      accountId,
      data: {
        type: values.type,
        number: values.number,
        country: values.country || undefined,
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Create Tax ID</FormSheetTitle>
      </FormSheetHeader>
      <Form {...form}>
        <form id={formId} onSubmit={form.handleSubmit(onSubmit)}>
          <FormSheetGroup>
            <FormField
              control={form.control}
              name="type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Type</FormLabel>
                  <Select
                    defaultValue={field.value}
                    onValueChange={field.onChange}
                  >
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {TAX_ID_TYPES.map((type) => (
                        <SelectItem key={type} value={type}>
                          {formatTaxIdType(type)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="number"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Number</FormLabel>
                  <FormControl>
                    <Input
                      type="text"
                      placeholder={
                        TAX_ID_NUMBER_HINTS[
                          selectedType as keyof typeof TAX_ID_NUMBER_HINTS
                        ] || "123456789"
                      }
                      {...field}
                    />
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
