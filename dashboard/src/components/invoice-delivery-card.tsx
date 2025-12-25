import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
  useUpdateInvoice,
} from "@/api/endpoints/invoices/invoices";
import { DeliveryMethodEnum, type Invoice } from "@/api/models";
import {
  emailsToRecipientTags,
  recipientTagSchema,
  recipientTagsToEmails,
  recipientTagStyleClasses,
  validateRecipientTag,
  type RecipientTag,
} from "@/components/delivery-recipient-tags";
import { Badge } from "@/components/ui/badge.tsx";
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
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Label } from "@/components/ui/label.tsx";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group.tsx";
import { useActiveAccount } from "@/hooks/use-active-account.ts";
import { useDebouncedCallback } from "@/hooks/use-debounced-callback";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { TagInput, type Tag } from "emblor";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  delivery_method: z.enum(DeliveryMethodEnum),
  recipients: z.array(recipientTagSchema),
});

type FormValues = z.infer<typeof schema>;

export function InvoiceDeliveryCard({ invoice }: { invoice: Invoice }) {
  const queryClient = useQueryClient();
  const { account } = useActiveAccount();
  const defaultRecipients = emailsToRecipientTags(invoice.recipients);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      delivery_method: invoice.delivery_method,
      recipients: defaultRecipients,
    },
  });

  const [recipientTags, setRecipientTags] =
    useState<RecipientTag[]>(defaultRecipients);
  const [activeRecipientIndex, setActiveRecipientIndex] = useState<
    number | null
  >(null);

  const { mutateAsync, isPending } = useUpdateInvoice({
    mutation: {
      onSuccess: async ({ id }) => {
        await queryClient.invalidateQueries({
          queryKey: getInvoicesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getInvoicesRetrieveQueryKey(id),
        });
        await queryClient.invalidateQueries({
          queryKey: getPreviewInvoiceQueryKey(id),
        });
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
      id: invoice.id,
      data: {
        delivery_method: values.delivery_method,
        recipients: recipientTagsToEmails(values.recipients),
      },
    });
  }

  const submit = form.handleSubmit(onSubmit);
  const debouncedSubmit = useDebouncedCallback(() => submit(), 400);

  const deliveryMethod = form.watch("delivery_method");

  return (
    <Form {...form}>
      <form>
        <FormCard className="pb-4">
          <FormCardHeader>
            <FormCardTitle>Delivery</FormCardTitle>
            <FormCardDescription>
              Choose how this invoice is delivered to your customer
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent>
            <FormField
              control={form.control}
              name="delivery_method"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Method</FormLabel>
                  <FormControl>
                    <RadioGroup
                      className="grid-cols-2 gap-2"
                      value={field.value}
                      onValueChange={field.onChange}
                    >
                      <div className="border-input has-data-[state=checked]:border-primary/50 relative flex w-full items-start gap-2 rounded-md border p-4 shadow-xs outline-none">
                        <RadioGroupItem
                          value={DeliveryMethodEnum.manual}
                          className="order-1 after:absolute after:inset-0"
                        />
                        <div className="grid grow gap-2">
                          <Label className="h-4">Manual</Label>
                          <p className="text-muted-foreground text-xs">
                            You will need to send the invoice to the customer
                            manually.
                          </p>
                        </div>
                      </div>
                      <div className="border-input has-data-[state=checked]:border-primary/50 relative flex w-full items-start gap-2 rounded-md border p-4 shadow-xs outline-none">
                        <RadioGroupItem
                          value={DeliveryMethodEnum.automatic}
                          className="peer order-1 after:absolute after:inset-0"
                          disabled={!account.subscription}
                        />
                        <div className="grid grow gap-2 peer-disabled:opacity-50">
                          <Label className="h-4">
                            <span>Automatic</span>
                            {!account.subscription && (
                              <Badge className="px-1.5 py-0">Upgrade</Badge>
                            )}
                          </Label>
                          <p className="text-muted-foreground text-xs">
                            Invoice will be automatically sent to recipients
                            when finalized.
                          </p>
                        </div>
                      </div>
                    </RadioGroup>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormCardContent>
          {deliveryMethod === DeliveryMethodEnum.automatic && (
            <FormCardContent>
              <FormField
                control={form.control}
                name="recipients"
                render={({ field }) => (
                  <FormItem className="grid gap-2">
                    <FormLabel>Recipients</FormLabel>
                    <FormControl>
                      <TagInput
                        {...field}
                        placeholder="Add email"
                        minTags={0}
                        maxTags={10}
                        tags={recipientTags}
                        setTags={(newTags) => {
                          // @ts-ignore
                          const normalizedTags: RecipientTag[] = newTags.map(
                            (tag: Tag) => ({ id: tag.id, text: tag.text }),
                          );
                          setRecipientTags(normalizedTags);
                          form.setValue("recipients", normalizedTags, {
                            shouldDirty: true,
                            shouldTouch: true,
                            shouldValidate: true,
                          });
                          debouncedSubmit();
                        }}
                        validateTag={validateRecipientTag}
                        activeTagIndex={activeRecipientIndex}
                        setActiveTagIndex={setActiveRecipientIndex}
                        styleClasses={recipientTagStyleClasses}
                        inputProps={{ type: "email" }}
                      />
                    </FormControl>
                    <FormDescription>
                      Emails that will receive the invoice when it is finalized.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormCardContent>
          )}
        </FormCard>
      </form>
    </Form>
  );
}
