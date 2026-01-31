import {
  getInvoicesListQueryKey,
  getInvoicesRetrieveQueryKey,
  getPreviewInvoiceQueryKey,
  useCreateInvoiceDocument,
  useDeleteInvoiceDocument,
  useUpdateInvoiceDocument,
} from "@/api/endpoints/invoices/invoices";
import {
  InvoiceDocumentAudienceEnum,
  type Invoice,
  type InvoiceDocument,
} from "@/api/models";
import { LanguageCombobox } from "@/components/language-combobox";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import {
  Field,
  FieldContent,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldTitle,
} from "@/components/ui/field.tsx";
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
  FormCardFooter,
  FormCardHeader,
  FormCardSeparator,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useDebouncedCallback } from "@/hooks/use-debounced-callback";
import { getErrorSummary } from "@/lib/api/errors";
import { formatEnum, formatLanguage } from "@/lib/formatters";
import { listToRecord, recordToList } from "@/lib/utils";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { PlusIcon, XIcon } from "lucide-react";
import { useMemo, useState } from "react";
import { useFieldArray, useForm } from "react-hook-form";
import { toast } from "sonner";
import z from "zod";

const schema = z.object({
  audience: z.array(z.enum(InvoiceDocumentAudienceEnum)),
  footer: z.string().optional(),
  memo: z.string().optional(),
  custom_fields: z.array(
    z.object({
      key: z.string().min(1, "Key is required"),
      value: z.string(),
    }),
  ),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

function InvoiceDocumentForm({
  invoice,
  document,
}: {
  invoice: Invoice;
  document: InvoiceDocument;
}) {
  const queryClient = useQueryClient();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      audience: document.audience ?? [],
      footer: document.footer || "",
      memo: document.memo || "",
      custom_fields: recordToList(
        document.custom_fields as Record<string, string>,
      ),
    },
  });
  const customFields = useFieldArray({
    control: form.control,
    name: "custom_fields",
  });

  const { mutateAsync, isPending } = useUpdateInvoiceDocument({
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

  async function onSubmit(values: FormValuesOutput) {
    if (isPending) return;

    await mutateAsync({
      invoiceId: invoice.id,
      id: document.id,
      data: {
        audience: values.audience,
        footer: values.footer || null,
        memo: values.memo || null,
        custom_fields: listToRecord(values.custom_fields),
      },
    });
  }

  const submit = form.handleSubmit(onSubmit);
  const debouncedSubmit = useDebouncedCallback(() => submit(), 500);
  const audienceOptions = useMemo(
    () => [
      {
        value: InvoiceDocumentAudienceEnum.customer,
        title: formatEnum(InvoiceDocumentAudienceEnum.customer),
        description: "Sent and visible to the customer.",
      },
      {
        value: InvoiceDocumentAudienceEnum.internal,
        title: formatEnum(InvoiceDocumentAudienceEnum.internal),
        description: "Visible to your internal team only.",
      },
      {
        value: InvoiceDocumentAudienceEnum.legal,
        title: formatEnum(InvoiceDocumentAudienceEnum.legal),
        description: "Reserved for compliance records.",
      },
    ],
    [],
  );

  return (
    <Form {...form}>
      <form className="grid gap-4 py-2">
        <FormCardContent>
          <FormField
            control={form.control}
            name="audience"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Audience</FormLabel>
                <FormControl>
                  <FieldGroup className="grid gap-2 sm:grid-cols-3">
                    {audienceOptions.map((audience) => (
                      <FieldLabel key={audience.value}>
                        <Field orientation="horizontal">
                          <FieldContent>
                            <FieldTitle>{audience.title}</FieldTitle>
                            <FieldDescription>
                              {audience.description}
                            </FieldDescription>
                          </FieldContent>
                          <Checkbox
                            checked={field.value.includes(audience.value)}
                            onCheckedChange={(checked) => {
                              const newValue = [...field.value];
                              if (checked) {
                                newValue.push(audience.value);
                              } else {
                                const index = newValue.indexOf(audience.value);
                                if (index > -1) {
                                  newValue.splice(index, 1);
                                }
                              }
                              field.onChange(newValue);
                              debouncedSubmit();
                            }}
                          />
                        </Field>
                      </FieldLabel>
                    ))}
                  </FieldGroup>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </FormCardContent>
        <FormCardContent>
          <FormField
            control={form.control}
            name="memo"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Memo</FormLabel>
                <FormDescription>
                  Add a note that appears near the top of the document.
                </FormDescription>
                <FormControl>
                  <Textarea
                    placeholder="Enter memo"
                    {...field}
                    onChange={(event) => {
                      field.onChange(event);
                      debouncedSubmit();
                    }}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </FormCardContent>
        <FormCardContent>
          <FormField
            control={form.control}
            name="footer"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Footer</FormLabel>
                <FormDescription>
                  Shown at the bottom of the invoice document.
                </FormDescription>
                <FormControl>
                  <Textarea
                    placeholder="Enter footer text"
                    {...field}
                    onChange={(event) => {
                      field.onChange(event);
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
              Custom fields will be displayed on the document.
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
                        onChange={(event) => {
                          field.onChange(event);
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
                        onChange={(event) => {
                          field.onChange(event);
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
      </form>
    </Form>
  );
}

export function InvoiceDocumentsCard({ invoice }: { invoice: Invoice }) {
  const queryClient = useQueryClient();
  const [openItem, setOpenItem] = useState<string | undefined>(
    invoice.documents[0]?.id,
  );

  async function invalidate() {
    await queryClient.invalidateQueries({
      queryKey: getInvoicesListQueryKey(),
    });
    await queryClient.invalidateQueries({
      queryKey: getInvoicesRetrieveQueryKey(invoice.id),
    });
    await queryClient.invalidateQueries({
      queryKey: getPreviewInvoiceQueryKey(invoice.id),
    });
  }

  const createDocument = useCreateInvoiceDocument({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  const deleteDocument = useDeleteInvoiceDocument({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return (
    <FormCard className="gap-0" data-testid="invoice-documents-card">
      <FormCardHeader className="pb-4">
        <FormCardTitle>Documents</FormCardTitle>
        <FormCardDescription>
          Configure the pdf documents generated for this invoice.
        </FormCardDescription>
      </FormCardHeader>
      <Accordion
        type="single"
        className="[&>:first-child]:border-t"
        value={openItem}
        onValueChange={setOpenItem}
        collapsible
      >
        {invoice.documents.map((document) => (
          <AccordionItem
            key={document.id}
            value={document.id}
            className="data-[state=open]:bg-accent/35 relative border-x-0 transition outline-none"
          >
            <div className="flex w-full items-center justify-between">
              <div className="w-full [&_h3]:w-full">
                <AccordionTrigger className="items-center justify-start px-4 py-3 leading-6 font-normal hover:no-underline focus-visible:ring-0 [&>svg]:-order-1">
                  {formatLanguage(document.language)}
                </AccordionTrigger>
              </div>
              <div className="flex items-center gap-2">
                {document.audience.map((audience) => (
                  <Badge
                    key={audience}
                    variant="secondary"
                    className="text-muted-foreground"
                  >
                    {formatEnum(audience)}
                  </Badge>
                ))}
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground mr-4 size-8"
                  aria-label={`Remove document ${document.language}`}
                  onClick={async (event) => {
                    event.preventDefault();
                    await deleteDocument.mutateAsync({
                      invoiceId: invoice.id,
                      id: document.id,
                    });
                  }}
                >
                  <XIcon />
                </Button>
              </div>
            </div>
            <AccordionContent>
              <InvoiceDocumentForm invoice={invoice} document={document} />
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
      {invoice.documents.length === 0 && (
        <Empty className="m-2 border border-dashed">
          <EmptyHeader>
            <EmptyTitle>No documents added yet</EmptyTitle>
            <EmptyDescription>
              Add a document to be generated for this invoice.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      )}
      <FormCardFooter>
        <LanguageCombobox
          align="end"
          onSelect={async (language) => {
            if (!language) return;
            await createDocument.mutateAsync({
              invoiceId: invoice.id,
              data: {
                language,
                audience: [],
                footer: null,
                memo: null,
                custom_fields: {},
              },
            });
          }}
        >
          <Button size="sm" variant="outline">
            <PlusIcon />
            Add document
          </Button>
        </LanguageCombobox>
      </FormCardFooter>
    </FormCard>
  );
}
