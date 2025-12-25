import {
  useCreateCreditNoteLine,
  useCreateCreditNoteLineTax,
  useDeleteCreditNoteLine,
  useDeleteCreditNoteLineTax,
  useUpdateCreditNoteLine,
} from "@/api/endpoints/credit-note-lines/credit-note-lines.ts";
import {
  getCreditNotesListQueryKey,
  getCreditNotesRetrieveQueryKey,
  getPreviewCreditNoteQueryKey,
} from "@/api/endpoints/credit-notes/credit-notes.ts";
import { useInvoicesRetrieve } from "@/api/endpoints/invoices/invoices";
import type {
  CreditNote,
  CreditNoteLine,
  Invoice,
  InvoiceLine,
} from "@/api/models";
import { TaxRateCombobox } from "@/components/tax-rate-combobox.tsx";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox.tsx";
import {
  Form,
  FormControl,
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
  FormCardTitle,
} from "@/components/ui/form-card";
import { Input, inputClassName } from "@/components/ui/input";
import {
  InputGroup,
  InputGroupAddon,
  inputGroupInputClassName,
  InputGroupText,
} from "@/components/ui/input-group.tsx";
import { Spinner } from "@/components/ui/spinner";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { MAX_TAXES } from "@/config/invoices";
import { useDebouncedCallback } from "@/hooks/use-debounced-callback";
import { getErrorSummary } from "@/lib/api/errors";
import { isZeroDecimalCurrency } from "@/lib/currency";
import { formatAmount, formatPercentage } from "@/lib/formatters";
import { cn } from "@/lib/utils.ts";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import Decimal from "decimal.js";
import { PlusIcon, XIcon } from "lucide-react";
import { useState } from "react";
import CurrencyInput from "react-currency-input-field";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import z from "zod";

const schema = z.object({
  unit_amount: z.string(),
  description: z.string(),
  quantity: z
    .union([z.string(), z.number()])
    .transform((v) => (typeof v === "string" ? Number(v) : v))
    .pipe(z.number().int().min(0, "Quantity cannot be negative")),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

function CreditNoteLineForm({
  line,
  creditNote,
}: {
  line: CreditNoteLine;
  creditNote: CreditNote;
}) {
  const queryClient = useQueryClient();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      unit_amount: line.unit_amount,
      description: line.description || "",
      quantity: line.quantity || 1,
    },
  });

  const taxesLimitReached = line.taxes.length >= MAX_TAXES;

  async function invalidate() {
    await queryClient.invalidateQueries({
      queryKey: getCreditNotesListQueryKey(),
    });
    await queryClient.invalidateQueries({
      queryKey: getCreditNotesRetrieveQueryKey(creditNote.id),
    });
    await queryClient.invalidateQueries({
      queryKey: getPreviewCreditNoteQueryKey(creditNote.id),
    });
  }

  const updateCreditNoteLine = useUpdateCreditNoteLine({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });
  const applyCreditNoteLineTax = useCreateCreditNoteLineTax({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });
  const deleteCreditNoteLineTax = useDeleteCreditNoteLineTax({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  const isPending =
    updateCreditNoteLine.isPending ||
    applyCreditNoteLineTax.isPending ||
    deleteCreditNoteLineTax.isPending;

  async function onSubmit(values: FormValuesOutput) {
    if (isPending) return;
    await updateCreditNoteLine.mutateAsync({
      id: line.id,
      data: {
        description: values.description,
        quantity: values.quantity,
        unit_amount: values.unit_amount,
      },
    });
  }

  const submit = form.handleSubmit(onSubmit);
  const debouncedSubmit = useDebouncedCallback(() => submit(), 500);

  return (
    <Form {...form}>
      <form className="grid gap-4 py-2">
        <FormCardContent>
          <FormField
            control={form.control}
            name="description"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Description</FormLabel>
                <FormControl>
                  <Input
                    placeholder="Enter line description"
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
        <FormCardContent className="md:grid-cols-2">
          <FormField
            control={form.control}
            name="unit_amount"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Price</FormLabel>
                <FormControl>
                  <CurrencyInput
                    placeholder="Enter price"
                    className={inputClassName}
                    value={field.value}
                    onValueChange={(value) => {
                      field.onChange(value);
                      debouncedSubmit();
                    }}
                    maxLength={8}
                    decimalsLimit={
                      isZeroDecimalCurrency(creditNote.currency) ? 0 : 2
                    }
                    allowDecimals={!isZeroDecimalCurrency(creditNote.currency)}
                    allowNegativeValue={false}
                    disableAbbreviations={true}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="quantity"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Quantity</FormLabel>
                <FormControl>
                  <CurrencyInput
                    placeholder="Enter quantity"
                    className={inputClassName}
                    value={field.value}
                    onValueChange={(value) => {
                      field.onChange(value || "0");
                      debouncedSubmit();
                    }}
                    maxLength={8}
                    allowDecimals={false}
                    allowNegativeValue={false}
                    disableAbbreviations={true}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </FormCardContent>
        {line.taxes.length > 0 && (
          <FormCardContent className="gap-2">
            <FormLabel>Line taxes</FormLabel>
            <div>
              {line.taxes.map((tax) => (
                <div key={tax.id} className="flex gap-2">
                  <span className="flex flex-grow-1 items-center justify-between">
                    <div className="flex gap-2">
                      <span>{tax.name}</span>
                      <span className="text-muted-foreground">
                        {formatPercentage(tax.rate)}
                      </span>
                    </div>
                    <span>{formatAmount(tax.amount, creditNote.currency)}</span>
                  </span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground size-8"
                    onClick={() =>
                      deleteCreditNoteLineTax.mutateAsync({
                        id: tax.id,
                        lineId: line.id,
                      })
                    }
                  >
                    <XIcon />
                  </Button>
                </div>
              ))}
            </div>
          </FormCardContent>
        )}
        <FormCardContent className="flex gap-1">
          <Tooltip>
            <TooltipTrigger asChild>
              <span tabIndex={taxesLimitReached ? 0 : undefined}>
                <TaxRateCombobox
                  align="start"
                  onSelect={async (selected) => {
                    if (!selected) return;
                    await applyCreditNoteLineTax.mutateAsync({
                      lineId: line.id,
                      data: { tax_rate_id: selected.id },
                    });
                  }}
                >
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    disabled={taxesLimitReached}
                  >
                    {applyCreditNoteLineTax.isPending ? (
                      <Spinner variant="outline" />
                    ) : (
                      <PlusIcon className="text-muted-foreground" />
                    )}
                    Add tax
                  </Button>
                </TaxRateCombobox>
              </span>
            </TooltipTrigger>
            {taxesLimitReached && (
              <TooltipContent>Maximum {MAX_TAXES} taxes reached</TooltipContent>
            )}
          </Tooltip>
        </FormCardContent>
      </form>
    </Form>
  );
}

function InvoiceLineForm({
  invoice,
  invoiceLine,
  creditLine,
  creditNote,
}: {
  invoice: Invoice;
  invoiceLine: InvoiceLine;
  creditLine: CreditNoteLine;
  creditNote: CreditNote;
}) {
  const queryClient = useQueryClient();
  // TODO: we need to fix it on backend?
  const lineOutstandingAmount = new Decimal(invoiceLine.outstanding_amount)
    .sub(new Decimal(invoiceLine.total_tax_amount))
    .plus(new Decimal(invoiceLine.total_discount_amount));
  // TODO: refine validation, so when we add custom credit note line and partly fill amount, then available remaining is calculated accordingly
  const invoiceOutstandingAmount = new Decimal(invoice.outstanding_amount);
  const availableCreditAmount = invoiceOutstandingAmount;
  const minOutstandingAmount = Decimal.min(
    lineOutstandingAmount,
    availableCreditAmount,
  );

  const schema = z
    .object({
      amount: z.string().default("0"),
      quantity: z.union([z.string(), z.number(), z.null()]).transform((v) => {
        if (v === null) return null;
        if (typeof v === "number") return v;
        // treat empty string as null, otherwise number
        return v.trim() === "" ? null : Number(v);
      }),
    })
    .superRefine((data, ctx) => {
      if (data.quantity === null) {
        const amount = new Decimal(data.amount || "0");

        if (amount.lt(0)) {
          ctx.addIssue({
            code: "custom",
            path: ["amount"],
            message: "Amount cannot be negative.",
          });
        } else if (amount.gt(minOutstandingAmount)) {
          ctx.addIssue({
            code: "custom",
            path: ["amount"],
            message: `Amount cannot exceed ${minOutstandingAmount.toFixed(2)} (line limit ${lineOutstandingAmount.toFixed(2)}, invoice limit ${availableCreditAmount.toFixed(2)}).`,
          });
        }
        return;
      }

      if (!Number.isInteger(data.quantity) || data.quantity < 0) {
        ctx.addIssue({
          code: "custom",
          path: ["quantity"],
          message: "Quantity must be a non-negative integer.",
        });
        return;
      }

      if (data.quantity > invoiceLine.outstanding_quantity) {
        ctx.addIssue({
          code: "custom",
          path: ["quantity"],
          message: `Quantity cannot exceed ${invoiceLine.outstanding_quantity}.`,
        });
      }

      const amount = new Decimal(invoiceLine.unit_amount).times(data.quantity);
      if (amount.gt(minOutstandingAmount)) {
        ctx.addIssue({
          code: "custom",
          path: ["quantity"],
          message: `Computed amount ${amount.toFixed(2)} exceeds allowed maximum ${minOutstandingAmount.toFixed(2)} (line limit ${lineOutstandingAmount.toFixed(2)}, invoice limit ${availableCreditAmount.toFixed(2)}).`,
        });
      }
    });

  type FormValues = z.infer<typeof schema>;
  const form = useForm<z.input<typeof schema>, any, FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      amount: creditLine.amount,
      quantity: creditLine.quantity,
    },
  });

  const updateCreditNoteLine = useUpdateCreditNoteLine({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getCreditNotesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getCreditNotesRetrieveQueryKey(creditNote.id),
        });
        await queryClient.invalidateQueries({
          queryKey: getPreviewCreditNoteQueryKey(creditNote.id),
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (updateCreditNoteLine.isPending) return;
    await updateCreditNoteLine.mutateAsync({
      id: creditLine.id,
      data: {
        amount: values.amount,
      },
    });
  }

  const submit = form.handleSubmit(onSubmit);
  const debouncedSubmit = useDebouncedCallback(() => submit(), 500);

  return (
    <Form {...form}>
      <form className="grid gap-4 py-2">
        <FormCardContent className="md:grid-cols-2">
          <FormField
            control={form.control}
            name="quantity"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Credit quantity</FormLabel>
                <FormControl>
                  <InputGroup>
                    <CurrencyInput
                      data-slot="input-group-control"
                      placeholder="Enter quantity"
                      className={cn(inputClassName, inputGroupInputClassName)}
                      value={field.value || undefined}
                      onValueChange={(value) => {
                        field.onChange(value || "0");
                        debouncedSubmit();
                      }}
                      maxLength={8}
                      allowDecimals={false}
                      allowNegativeValue={false}
                      disableAbbreviations={true}
                    />
                    <InputGroupAddon align="inline-end" className="font-normal">
                      <InputGroupText>
                        / {invoiceLine.outstanding_quantity}
                      </InputGroupText>
                    </InputGroupAddon>
                  </InputGroup>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="amount"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Credit amount</FormLabel>
                <FormControl>
                  <InputGroup>
                    <CurrencyInput
                      data-slot="input-group-control"
                      placeholder="Enter amount"
                      className={cn(inputClassName, inputGroupInputClassName)}
                      value={field.value}
                      onValueChange={(value) => {
                        field.onChange(value);
                        debouncedSubmit();
                      }}
                      maxLength={8}
                      decimalsLimit={
                        isZeroDecimalCurrency(creditNote.currency) ? 0 : 2
                      }
                      allowDecimals={
                        !isZeroDecimalCurrency(creditNote.currency)
                      }
                      allowNegativeValue={false}
                      disableAbbreviations={true}
                    />
                    <InputGroupAddon align="inline-end" className="font-normal">
                      <InputGroupText>
                        /{" "}
                        {formatAmount(
                          minOutstandingAmount.toString(),
                          creditNote.currency,
                        )}
                      </InputGroupText>
                    </InputGroupAddon>
                  </InputGroup>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </FormCardContent>
      </form>
    </Form>
  );
}

export function CreditNoteLinesCard({
  creditNote,
}: {
  creditNote: CreditNote;
}) {
  const queryClient = useQueryClient();
  const [openItem, setOpenItem] = useState<string>();
  const { data: invoice } = useInvoicesRetrieve(creditNote.invoice_id);

  async function invalidate() {
    await queryClient.invalidateQueries({
      queryKey: getCreditNotesListQueryKey(),
    });
    await queryClient.invalidateQueries({
      queryKey: getCreditNotesRetrieveQueryKey(creditNote.id),
    });
    await queryClient.invalidateQueries({
      queryKey: getPreviewCreditNoteQueryKey(creditNote.id),
    });
  }

  const createCreditNoteLine = useCreateCreditNoteLine({
    mutation: {
      onSuccess: async (line) => {
        await invalidate();
        setOpenItem(line.id);
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  const deleteCreditNoteLine = useDeleteCreditNoteLine({
    mutation: {
      onSuccess: async () => {
        await invalidate();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  if (!invoice) return null;

  return (
    <FormCard className="gap-0">
      <FormCardHeader className="pb-4">
        <FormCardTitle>Lines</FormCardTitle>
        <FormCardDescription>
          Manage lines to be credited to the customer.
        </FormCardDescription>
      </FormCardHeader>
      <Accordion
        type="single"
        value={openItem}
        className="[&>:first-child]:border-t"
        onValueChange={setOpenItem}
        collapsible
      >
        {invoice.lines.map((invoiceLine) => {
          const creditLine = creditNote.lines.find(
            (cl) => cl.invoice_line_id === invoiceLine.id,
          );

          return (
            <AccordionItem
              key={invoiceLine.id}
              value={invoiceLine.id}
              className="data-[state=open]:bg-accent/35 relative border-x-0 transition outline-none"
              disabled={!creditLine}
            >
              <div className="flex w-full items-center justify-between">
                <div className="w-full [&_h3]:w-full">
                  <AccordionTrigger className="items-center justify-start px-4 py-3 leading-6 font-normal hover:no-underline focus-visible:ring-0 [&>svg]:-order-1">
                    {invoiceLine.description}
                    {creditLine?.quantity && (
                      <>
                        {" "}
                        ×{" "}
                        {creditLine
                          ? creditLine.quantity
                          : invoiceLine.quantity}
                      </>
                    )}
                  </AccordionTrigger>
                </div>
                <div className="flex items-center gap-2">
                  {invoiceLine.taxes.length > 0 && (
                    <Badge
                      variant="secondary"
                      className="text-muted-foreground"
                    >
                      {formatPercentage(
                        invoiceLine.taxes
                          .reduce(
                            (acc, tax) => acc.plus(new Decimal(tax.rate)),
                            new Decimal(0),
                          )
                          .toString(),
                      )}{" "}
                      tax
                    </Badge>
                  )}
                  <span className={cn("text-sm", !creditLine && "opacity-50")}>
                    {formatAmount(
                      creditLine ? creditLine.amount : invoiceLine.amount,
                      creditNote.currency,
                    )}
                  </span>
                  <Checkbox
                    className="mr-6 ml-2"
                    checked={!!creditLine}
                    onCheckedChange={async (checked) => {
                      if (checked) {
                        await createCreditNoteLine.mutateAsync({
                          data: {
                            credit_note_id: creditNote.id,
                            invoice_line_id: invoiceLine.id,
                          },
                        });
                      } else {
                        await deleteCreditNoteLine.mutateAsync({
                          id: creditLine?.id as string,
                        });
                      }
                    }}
                  />
                </div>
              </div>
              <AccordionContent>
                <InvoiceLineForm
                  invoice={invoice}
                  invoiceLine={invoiceLine}
                  creditLine={creditLine as CreditNoteLine}
                  creditNote={creditNote}
                />
              </AccordionContent>
            </AccordionItem>
          );
        })}
        {creditNote.lines
          .filter((line) => !line.invoice_line_id)
          .map((line) => (
            <AccordionItem
              key={line.id}
              value={line.id}
              className="data-[state=open]:bg-accent/35 relative border-x-0 transition outline-none"
            >
              <div className="flex w-full items-center justify-between">
                <div className="w-full [&_h3]:w-full">
                  <AccordionTrigger className="items-center justify-start px-4 py-3 leading-6 font-normal hover:no-underline focus-visible:ring-0 [&>svg]:-order-1">
                    {line.description} × {line.quantity}
                  </AccordionTrigger>
                </div>
                <div className="flex items-center gap-2">
                  {line.taxes.length > 0 && (
                    <Badge
                      variant="secondary"
                      className="text-muted-foreground"
                    >
                      {formatPercentage(
                        line.taxes
                          .reduce(
                            (acc, tax) => acc.plus(new Decimal(tax.rate)),
                            new Decimal(0),
                          )
                          .toString(),
                      )}{" "}
                      tax
                    </Badge>
                  )}
                  <span className="text-sm">
                    {formatAmount(line.amount, creditNote.currency)}
                  </span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground mr-4 size-8"
                    onClick={async (e) => {
                      e.preventDefault();
                      await deleteCreditNoteLine.mutateAsync({ id: line.id });
                    }}
                  >
                    <XIcon />
                  </Button>
                </div>
              </div>
              <AccordionContent>
                <CreditNoteLineForm line={line} creditNote={creditNote} />
              </AccordionContent>
            </AccordionItem>
          ))}
      </Accordion>
      <FormCardFooter>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={async () => {
            await createCreditNoteLine.mutateAsync({
              data: {
                credit_note_id: creditNote.id,
                unit_amount: "0",
                description: "",
                quantity: 1,
              },
            });
          }}
        >
          {createCreditNoteLine.isPending ? (
            <Spinner variant="outline" />
          ) : (
            <PlusIcon className="text-muted-foreground" />
          )}
          Add line
        </Button>
      </FormCardFooter>
    </FormCard>
  );
}
