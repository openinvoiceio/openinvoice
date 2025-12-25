import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
  useUpdateInvoice,
} from "@/api/endpoints/invoices/invoices";
import type { Invoice } from "@/api/models";
import { Button } from "@/components/ui/button";
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
  FormCardSeparator,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useDebouncedCallback } from "@/hooks/use-debounced-callback";
import { getErrorSummary } from "@/lib/api/errors";
import { listToRecord, recordToList } from "@/lib/utils";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { PlusIcon, XIcon } from "lucide-react";
import { useFieldArray, useForm } from "react-hook-form";
import { toast } from "sonner";
import z from "zod";

const schema = z.object({
  footer: z.string().optional(),
  custom_fields: z.array(
    z.object({
      key: z.string().min(1, "Key is required"),
      value: z.string(),
    }),
  ),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

export function InvoiceAdditionalCard({ invoice }: { invoice: Invoice }) {
  const queryClient = useQueryClient();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      footer: invoice.footer || "",
      custom_fields: recordToList(
        invoice.custom_fields as Record<string, string>,
      ),
    },
  });
  const customFields = useFieldArray({
    control: form.control,
    name: "custom_fields",
  });

  const { isPending, mutateAsync } = useUpdateInvoice({
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
        toast.error(message, { description: description });
      },
    },
  });

  async function onSubmit(values: FormValuesInput) {
    if (isPending) return;

    await mutateAsync({
      id: invoice.id,
      data: {
        footer: values.footer || null,
        custom_fields: listToRecord(values.custom_fields),
      },
    });
  }

  const submit = form.handleSubmit(onSubmit);
  const debouncedSubmit = useDebouncedCallback(() => submit(), 500);

  return (
    <Form {...form}>
      <form>
        <FormCard className="pb-4">
          <FormCardHeader>
            <FormCardTitle>Additional</FormCardTitle>
            <FormCardDescription>
              Add extra information to the invoice
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent>
            <FormField
              control={form.control}
              name="footer"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Footer</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Enter footer text"
                      {...field}
                      onChange={(e) => {
                        field.onChange(e);
                        debouncedSubmit();
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormCardContent>
          <FormCardSeparator />
          <FormCardContent>
            <div className="grid gap-2">
              <FormLabel>Custom fields</FormLabel>
              <FormDescription>
                Custom fields will be displayed on the invoice
              </FormDescription>
            </div>
            {customFields.fields.map((field, index) => (
              <div key={field.id} className="flex gap-2">
                <FormField
                  control={form.control}
                  name={`custom_fields.${index}.key`}
                  render={({ field }) => (
                    <FormItem className="w-full">
                      <FormControl>
                        <Input
                          placeholder="Key"
                          {...field}
                          onChange={(e) => {
                            field.onChange(e);
                            debouncedSubmit();
                          }}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name={`custom_fields.${index}.value`}
                  render={({ field }) => (
                    <FormItem className="w-full">
                      <FormControl>
                        <Input
                          placeholder="Value"
                          {...field}
                          onChange={(e) => {
                            field.onChange(e);
                            debouncedSubmit();
                          }}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={async () => {
                    customFields.remove(index);
                    await submit();
                  }}
                  className="shrink-0"
                >
                  <XIcon />
                </Button>
              </div>
            ))}
            <div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => customFields.append({ key: "", value: "" })}
                disabled={customFields.fields.length >= 20}
              >
                <PlusIcon />
                Add item
              </Button>
            </div>
          </FormCardContent>
        </FormCard>
      </form>
    </Form>
  );
}
