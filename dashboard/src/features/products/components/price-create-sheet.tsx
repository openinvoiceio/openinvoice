import {
  getPricesListQueryKey,
  useCreatePrice,
} from "@/api/endpoints/prices/prices";
import {
  getProductsListQueryKey,
  getProductsRetrieveQueryKey,
  useProductsRetrieve,
} from "@/api/endpoints/products/products";
import {
  CurrencyEnum,
  PriceModelEnum,
  ProductsListStatus,
  type Price,
} from "@/api/models";
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
  FormSheetDescription,
  FormSheetFooter,
  FormSheetGroup,
  FormSheetHeader,
  FormSheetTitle,
} from "@/components/ui/form-sheet";
import { Input, inputClassName } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select.tsx";
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table.tsx";
import { ProductCombobox } from "@/features/products/components/product-combobox.tsx";
import { useActiveAccount } from "@/hooks/use-active-account";
import { usePriceTiers } from "@/hooks/use-price-tiers.ts";
import { getErrorSummary } from "@/lib/api/errors";
import { isZeroDecimalCurrency, sanitizeCurrencyAmount } from "@/lib/currency";
import { formatEnum } from "@/lib/formatters.ts";
import { cn } from "@/lib/utils";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { PlusIcon, XIcon } from "lucide-react";
import { useId } from "react";
import CurrencyInput from "react-currency-input-field";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  product_id: z.uuid(),
  model: z.enum(PriceModelEnum),
  currency: z.enum(CurrencyEnum),
  amount: z.string(),
  code: z.string(),
  tiers: z.array(
    z.object({
      unit_amount: z.string(),
      from_value: z.int(),
      to_value: z.int().nullable(),
    }),
  ),
});

type FormValues = z.infer<typeof schema>;

export function PriceCreateSheet({
  code,
  productId: defaultProductId,
  onSuccess,
}: {
  code?: string;
  productId?: string;
  onSuccess?: (price: Price) => void;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const { account } = useActiveAccount();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      product_id: defaultProductId,
      model: PriceModelEnum.flat,
      currency: account.default_currency,
      amount: "0",
      code: code || "",
      tiers: [],
    },
  });
  const { tiers, onTierChange, onTierCreate, onTierRemove } = usePriceTiers({
    form,
  });
  const model = form.watch("model");
  const currency = form.watch("currency");
  const productId = form.watch("product_id");
  const { data: product } = useProductsRetrieve(productId || "", {
    query: { enabled: !!productId },
  });
  const { mutateAsync, isPending } = useCreatePrice({
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
        toast.success("Price created");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  function onModelChange(model: PriceModelEnum) {
    switch (model) {
      case PriceModelEnum.flat: {
        tiers.remove();
        form.setValue("amount", "0");
        break;
      }
      case PriceModelEnum.volume:
      case PriceModelEnum.graduated: {
        const previousAmount = form.getValues("amount");
        form.setValue("amount", "0");
        if (tiers.fields.length === 0) {
          tiers.append({
            unit_amount: previousAmount || "0",
            from_value: 0,
            to_value: 1,
          });
          tiers.append({
            unit_amount: previousAmount || "0",
            from_value: 2,
            to_value: null,
          });
        }
        break;
      }
    }
  }

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      data: {
        product_id: values.product_id,
        model: values.model,
        currency: values.currency,
        amount: values.amount.toString(),
        tiers: values.tiers,
        code: values.code || null,
        metadata: {},
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Create Price</FormSheetTitle>
        <FormSheetDescription>
          Create a new price for a product. Prices are used to charge customers
          for products or services.
        </FormSheetDescription>
      </FormSheetHeader>
      <Form {...form}>
        <form id={formId} onSubmit={form.handleSubmit(onSubmit)}>
          <FormSheetGroup>
            <FormField
              control={form.control}
              name="product_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Product</FormLabel>
                  <FormControl>
                    <ProductCombobox
                      selected={product}
                      onSelect={async (selected) => {
                        field.onChange(selected?.id);
                      }}
                      status={ProductsListStatus.active}
                      withoutPrice={true}
                    >
                      <ComboboxButton>
                        {product ? (
                          <span>{product.name}</span>
                        ) : (
                          <span className="text-muted-foreground">
                            Select product
                          </span>
                        )}
                      </ComboboxButton>
                    </ProductCombobox>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="model"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Model</FormLabel>
                  <FormControl>
                    <Select
                      value={field.value}
                      onValueChange={(value) => {
                        field.onChange(value);
                        onModelChange(value as PriceModelEnum);
                      }}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select model" />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.values(PriceModelEnum).map((value) => (
                          <SelectItem key={value} value={value}>
                            {formatEnum(value)}
                          </SelectItem>
                        ))}
                      </SelectContent>
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
