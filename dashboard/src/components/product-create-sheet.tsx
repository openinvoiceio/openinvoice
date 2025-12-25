import { useUploadFile } from "@/api/endpoints/files/files";
import { getPricesListQueryKey } from "@/api/endpoints/prices/prices";
import {
  getProductsListQueryKey,
  useCreateProduct,
} from "@/api/endpoints/products/products";
import { CurrencyEnum, FilePurposeEnum, type Product } from "@/api/models";
import { CurrencyCombobox } from "@/components/currency-combobox.tsx";
import { popModal } from "@/components/push-modals";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
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
  FormSheetGroupTitle,
  FormSheetHeader,
  FormSheetTitle,
} from "@/components/ui/form-sheet";
import { Input, inputClassName } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { useActiveAccount } from "@/hooks/use-active-account";
import { getErrorSummary } from "@/lib/api/errors";
import { isZeroDecimalCurrency, sanitizeCurrencyAmount } from "@/lib/currency";
import { cn } from "@/lib/utils";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { BoxIcon } from "lucide-react";
import { useId } from "react";
import CurrencyInput from "react-currency-input-field";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string(),
  image: z
    .file()
    .max(512 * 1024, "Image must be less than 512KB")
    .mime(["image/png", "image/jpeg", "image/svg+xml"])
    .optional(),
  currency: z.enum(CurrencyEnum),
  amount: z.string(),
  code: z.string(),
});

type FormValues = z.infer<typeof schema>;

export function ProductCreateSheet({
  name,
  onSuccess,
  withoutPrice,
}: {
  name?: string;
  onSuccess?: (product: Product) => void;
  withoutPrice?: boolean;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const { account } = useActiveAccount();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: name || "",
      description: "",
      currency: account.default_currency,
      amount: "0",
      code: "",
    },
  });
  const currency = form.watch("currency");

  const uploadFile = useUploadFile({
    mutation: {
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  const { isPending, mutateAsync } = useCreateProduct({
    mutation: {
      onSuccess: async (product) => {
        await queryClient.invalidateQueries({
          queryKey: getProductsListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getPricesListQueryKey(),
        });
        onSuccess?.(product);
        toast.success("Product created");
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

    let imageId: string | undefined;
    if (values.image) {
      const file = await uploadFile.mutateAsync({
        data: { file: values.image, purpose: FilePurposeEnum.product_image },
      });
      imageId = file.id;
    }

    await mutateAsync({
      data: {
        name: values.name,
        description: values.description || null,
        ...(imageId && { image_id: imageId }),
        metadata: {},
        ...(!withoutPrice && {
          default_price: {
            currency: values.currency,
            amount: values.amount.toString(),
            code: values.code || null,
            metadata: {},
          },
        }),
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Create Product</FormSheetTitle>
        <FormSheetDescription>
          Create a new product with price to use in your invoices.
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
                    <Input type="text" placeholder="Enter name" {...field} />
                  </FormControl>
                  <FormMessage />
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
                    <Textarea {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="image"
              render={({ field: { value, onChange, ...fieldProps } }) => (
                <FormItem>
                  <FormLabel>Image</FormLabel>
                  <FormControl>
                    <div className="flex items-center gap-2">
                      <Avatar className="rounded-md">
                        <AvatarImage src={undefined} />
                        <AvatarFallback className="rounded-md">
                          <BoxIcon className="size-4" />
                        </AvatarFallback>
                      </Avatar>
                      <Input
                        {...fieldProps}
                        type="file"
                        placeholder="Upload image"
                        onChange={(event) =>
                          onChange(event.target.files && event.target.files[0])
                        }
                      />
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormSheetGroup>
          {!withoutPrice && (
            <>
              <Separator />
              <FormSheetGroup>
                <FormSheetGroupTitle>Price</FormSheetGroupTitle>
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

                <FormField
                  control={form.control}
                  name="code"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Code</FormLabel>
                      <FormControl>
                        <Input
                          type="text"
                          placeholder="Enter code"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                      <FormDescription></FormDescription>
                    </FormItem>
                  )}
                />
              </FormSheetGroup>
            </>
          )}
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
