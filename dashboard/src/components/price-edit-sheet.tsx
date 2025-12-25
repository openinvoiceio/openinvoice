import {
  getPricesListQueryKey,
  useUpdatePrice,
} from "@/api/endpoints/prices/prices";
import {
  getProductsListQueryKey,
  getProductsRetrieveQueryKey,
} from "@/api/endpoints/products/products";
import { CurrencyEnum, PriceModelEnum, type Price } from "@/api/models";
import { CurrencyCombobox } from "@/components/currency-combobox.tsx";
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
  FormSheetFooter,
  FormSheetGroup,
  FormSheetHeader,
  FormSheetTitle,
} from "@/components/ui/form-sheet";
import { Input, inputClassName } from "@/components/ui/input";
import { Select, SelectTrigger } from "@/components/ui/select.tsx";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table.tsx";
import { usePriceTiers } from "@/hooks/use-price-tiers.ts";
import { getErrorSummary } from "@/lib/api/errors";
import { isZeroDecimalCurrency, sanitizeCurrencyAmount } from "@/lib/currency";
import { formatEnum } from "@/lib/formatters.ts";
import { cn, listToRecord, recordToList } from "@/lib/utils";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { PlusIcon, XIcon } from "lucide-react";
import { useId } from "react";
import CurrencyInput from "react-currency-input-field";
import { useFieldArray, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  currency: z.enum(CurrencyEnum),
  model: z.enum(PriceModelEnum),
  amount: z.string(),
  code: z.string(),
  metadata: z.array(
    z.object({
      key: z.string().min(1, "Key is required"),
      value: z.string(),
    }),
  ),
  tiers: z.array(
    z.object({
      unit_amount: z.string(),
      from_value: z.int(),
      to_value: z.int().nullable(),
    }),
  ),
});

type FormValues = z.infer<typeof schema>;

export function PriceEditSheet({
  price,
  onSuccess,
}: {
  price: Price;
  onSuccess?: (price: Price) => void;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      currency: price.currency,
      model: price.model,
      amount: price.amount,
      code: price.code || "",
      metadata: recordToList(price.metadata as Record<string, string>),
      tiers: price.tiers,
    },
  });
  const { tiers, onTierChange, onTierCreate, onTierRemove } = usePriceTiers({
    form,
  });
  const model = form.watch("model");
  const currency = form.watch("currency");
  const metadata = useFieldArray({
    control: form.control,
    name: "metadata",
  });

  const { mutateAsync, isPending } = useUpdatePrice({
    mutation: {
      onSuccess: async (price) => {
        await queryClient.invalidateQueries({
          queryKey: getPricesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getProductsListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getProductsRetrieveQueryKey(price.product.id),
        });
        onSuccess?.(price);
        toast.success("Price updated");
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
      id: price.id,
      data: {
        currency: values.currency,
        amount: values.amount.toString(),
        code: values.code || null,
        metadata: listToRecord(values.metadata),
        tiers: values.tiers,
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Update price in {price.product.name}</FormSheetTitle>
      </FormSheetHeader>
      <Form {...form}>
        <form id={formId} onSubmit={form.handleSubmit(onSubmit)}>
          <FormSheetGroup>
            <FormField
              control={form.control}
              name="model"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Model</FormLabel>
                  <FormControl>
                    <Select value={field.value} disabled>
                      <SelectTrigger className="w-full">
                        {formatEnum(model)}
                      </SelectTrigger>
                    </Select>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {model === PriceModelEnum.flat && (
              <div className="flex">
                <FormField
                  control={form.control}
                  name="amount"
                  render={({ field }) => (
                    <FormItem className="flex-1">
                      <FormLabel>Amount</FormLabel>
                      <FormControl>
                        <CurrencyInput
                          name={field.name}
                          placeholder="0"
                          className={cn(inputClassName, "rounded-r-none")}
                          value={field.value}
                          onValueChange={(value) => field.onChange(value)}
                          allowNegativeValue={false}
                          decimalsLimit={
                            isZeroDecimalCurrency(currency) ? 0 : 2
                          }
                          allowDecimals={!isZeroDecimalCurrency(currency)}
                          maxLength={19}
                          disableAbbreviations={true}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="currency"
                  render={({ field }) => (
                    <FormItem className="mt-auto w-24">
                      <FormControl>
                        <CurrencyCombobox
                          selected={field.value}
                          onSelect={async (value) => {
                            const code = value ?? "";
                            field.onChange(code);
                            const amount = form.getValues("amount");
                            form.setValue(
                              "amount",
                              sanitizeCurrencyAmount(amount, code),
                            );
                          }}
                        >
                          <ComboboxButton className="rounded-l-none">
                            <span>{field.value}</span>
                          </ComboboxButton>
                        </CurrencyCombobox>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            )}

            {(model === PriceModelEnum.volume ||
              model === PriceModelEnum.graduated) && (
              <div className="flex flex-col gap-2">
                <FormField
                  control={form.control}
                  name="currency"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Price</FormLabel>
                      <FormControl>
                        <CurrencyCombobox
                          selected={field.value}
                          onSelect={async (value) => {
                            const code = value ?? "";
                            field.onChange(code);
                            tiers.fields.map((_, index) => {
                              const tierAmount = form.getValues(
                                `tiers.${index}.unit_amount`,
                              );
                              form.setValue(
                                `tiers.${index}.unit_amount`,
                                sanitizeCurrencyAmount(tierAmount, code),
                              );
                            });
                          }}
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
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-background border">
                      <TableHead className="border">First unit</TableHead>
                      <TableHead className="border">Last unit</TableHead>
                      <TableHead className="border">Per unit</TableHead>
                      <TableHead className="border p-0"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tiers.fields.map((tier, index) => (
                      <TableRow
                        key={tier.id}
                        className="hover:bg-background border"
                      >
                        <FormField
                          control={form.control}
                          name={`tiers.${index}.from_value`}
                          render={({ field }) => (
                            <TableCell className="border py-0">
                              <FormControl>
                                <CurrencyInput
                                  placeholder="1"
                                  className={cn(
                                    inputClassName,
                                    "dark:bg-background border-none p-0 focus-visible:ring-0",
                                  )}
                                  value={field.value}
                                  onValueChange={(value) => {
                                    field.onChange(value || "0");
                                  }}
                                  disabled
                                  maxLength={8}
                                  allowDecimals={false}
                                  allowNegativeValue={false}
                                  disableAbbreviations={true}
                                />
                              </FormControl>
                            </TableCell>
                          )}
                        />
                        <FormField
                          control={form.control}
                          name={`tiers.${index}.to_value`}
                          render={({ field }) => (
                            <TableCell className="border py-0">
                              <FormControl>
                                <CurrencyInput
                                  placeholder={
                                    index === tiers.fields.length - 1
                                      ? "∞"
                                      : "0"
                                  }
                                  className={cn(
                                    inputClassName,
                                    "dark:bg-background border-none p-0 focus-visible:ring-0",
                                  )}
                                  value={field.value || undefined}
                                  onValueChange={(value) => {
                                    const normalized = value ?? null;
                                    field.onChange(normalized);
                                    onTierChange(index, normalized);
                                  }}
                                  maxLength={8}
                                  allowDecimals={false}
                                  allowNegativeValue={false}
                                  disableAbbreviations={true}
                                  disabled={index === tiers.fields.length - 1}
                                />
                              </FormControl>
                            </TableCell>
                          )}
                        />
                        <FormField
                          control={form.control}
                          name={`tiers.${index}.unit_amount`}
                          render={({ field }) => (
                            <TableCell className="border py-0">
                              <FormControl>
                                <CurrencyInput
                                  name={field.name}
                                  placeholder="0"
                                  className={cn(
                                    inputClassName,
                                    "dark:bg-background border-none p-0 focus-visible:ring-0",
                                  )}
                                  value={field.value}
                                  onValueChange={(value) =>
                                    field.onChange(value)
                                  }
                                  allowNegativeValue={false}
                                  decimalsLimit={
                                    isZeroDecimalCurrency(currency) ? 0 : 2
                                  }
                                  allowDecimals={
                                    !isZeroDecimalCurrency(currency)
                                  }
                                  maxLength={19}
                                  disableAbbreviations={true}
                                />
                              </FormControl>
                            </TableCell>
                          )}
                        />
                        <TableCell className="w-10 border p-0">
                          {index === 0 || tiers.fields.length <= 2 ? null : (
                            <Button
                              variant="ghost"
                              className="rounded-none"
                              onClick={() => onTierRemove(index)}
                            >
                              <XIcon />
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-fit"
                  type="button"
                  onClick={onTierCreate}
                >
                  <PlusIcon />
                  Add tier
                </Button>
              </div>
            )}

            <FormField
              control={form.control}
              name="code"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Code</FormLabel>
                  <FormControl>
                    <Input type="text" placeholder="Enter code" {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    An internal code to identify the price
                  </FormDescription>
                </FormItem>
              )}
            />
          </FormSheetGroup>
          <Separator />
          <FormSheetGroup>
            <FormLabel>Metadata</FormLabel>
            {metadata.fields.map((field, index) => (
              <div key={field.id} className="flex gap-2">
                <FormField
                  control={form.control}
                  name={`metadata.${index}.key`}
                  render={({ field }) => (
                    <FormItem className="w-full">
                      <FormControl>
                        <Input placeholder="Key" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name={`metadata.${index}.value`}
                  render={({ field }) => (
                    <FormItem className="w-full">
                      <FormControl>
                        <Input placeholder="Value" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => metadata.remove(index)}
                  className="shrink-0"
                >
                  <XIcon />
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="ml-auto w-fit"
              onClick={() => metadata.append({ key: "", value: "" })}
              disabled={metadata.fields.length >= 20}
            >
              <PlusIcon />
              Add item
            </Button>
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
