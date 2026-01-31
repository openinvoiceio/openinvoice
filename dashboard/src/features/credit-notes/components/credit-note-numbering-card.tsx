import {
  getCreditNotesListQueryKey,
  getCreditNotesRetrieveQueryKey,
  getPreviewCreditNoteQueryKey,
  useUpdateCreditNote,
} from "@/api/endpoints/credit-notes/credit-notes";
import { useNumberingSystemsRetrieve } from "@/api/endpoints/numbering-systems/numbering-systems";
import { NumberingSystemAppliesToEnum, type CreditNote } from "@/api/models";
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
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Input } from "@/components/ui/input";
import { NumberingSystemCombobox } from "@/features/settings/components/numbering-system-combobox";
import { useDebouncedCallback } from "@/hooks/use-debounced-callback";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  number: z.string(),
  numbering_system_id: z.string().uuid().nullable(),
});

type FormValuesInput = z.input<typeof schema>;
type FormValuesOutput = z.output<typeof schema>;

export function CreditNoteNumberingCard({
  creditNote,
}: {
  creditNote: CreditNote;
}) {
  const queryClient = useQueryClient();
  const form = useForm<FormValuesInput, any, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      number: creditNote.number ?? "",
      numbering_system_id: creditNote.numbering_system_id,
    },
  });

  const numberingSystemId = form.watch("numbering_system_id");
  const { data: numberingSystem } = useNumberingSystemsRetrieve(
    numberingSystemId || "",
    {
      query: { enabled: !!numberingSystemId },
    },
  );

  const updateMutation = useUpdateCreditNote({
    mutation: {
      onSuccess: async (result) => {
        form.setValue("number", result.number ?? "");
        await queryClient.invalidateQueries({
          queryKey: getCreditNotesRetrieveQueryKey(creditNote.id),
        });
        await queryClient.invalidateQueries({
          queryKey: getCreditNotesListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getPreviewCreditNoteQueryKey(creditNote.id),
        });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  async function onSubmit(values: FormValuesInput) {
    if (updateMutation.isPending) return;

    await updateMutation.mutateAsync({
      id: creditNote.id,
      data: {
        number: values.numbering_system_id
          ? null
          : values.number.trim() || null,
        numbering_system_id: values.numbering_system_id ?? null,
      },
    });
  }

  const submit = form.handleSubmit(onSubmit);
  const debouncedSubmit = useDebouncedCallback(() => submit(), 400);

  return (
    <Form {...form}>
      <form>
        <FormCard className="pb-4">
          <FormCardHeader>
            <FormCardTitle>Numbering</FormCardTitle>
            <FormCardDescription>
              Configure credit note number and numbering system
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent className="md:grid-cols-2">
            <FormField
              control={form.control}
              name="number"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Number</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Enter number"
                      disabled={!!numberingSystemId}
                      {...field}
                      onChange={(event) => {
                        field.onChange(event);
                        debouncedSubmit();
                      }}
                    />
                  </FormControl>
                  <FormDescription>
                    Leave empty to have a number assigned automatically when
                    issued
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="numbering_system_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Numbering system</FormLabel>
                  <FormControl>
                    <NumberingSystemCombobox
                      appliesTo={NumberingSystemAppliesToEnum.credit_note}
                      selected={numberingSystem}
                      onSelect={async (selected) => {
                        field.onChange(selected ? selected.id : null);
                        await submit();
                      }}
                    >
                      <ComboboxButton>
                        {numberingSystem ? (
                          <span>{numberingSystem.description}</span>
                        ) : (
                          <span className="text-muted-foreground">
                            Select numbering system
                          </span>
                        )}
                      </ComboboxButton>
                    </NumberingSystemCombobox>
                  </FormControl>
                  <FormDescription>
                    Use a numbering system to automatically generate numbers
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormCardContent>
        </FormCard>
      </form>
    </Form>
  );
}
