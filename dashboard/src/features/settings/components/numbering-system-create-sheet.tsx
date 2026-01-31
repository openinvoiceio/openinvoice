import {
  getNumberingSystemsListQueryKey,
  useCreateNumberingSystem,
} from "@/api/endpoints/numbering-systems/numbering-systems";
import {
  NumberingSystemAppliesToEnum,
  NumberingSystemResetIntervalEnum,
  type NumberingSystem,
} from "@/api/models";
import { popModal } from "@/components/push-modals";
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
  FormSheetContent,
  FormSheetDescription,
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
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { getErrorSummary } from "@/lib/api/errors";
import { formatEnum } from "@/lib/formatters.ts";
import { renderTemplate, templatePattern } from "@/lib/numbering-system";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { HelpCircleIcon } from "lucide-react";
import { useId } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const presetCode = {
  sequence: "sequence",
  yearSequence: "year/sequence",
  yearMonthSequence: "year-month/sequence",
  prefixYearSequence: "prefix-year-sequence",
  yearQuarterSequence: "year-quarter/sequence",
  custom: "custom",
} as const;

const presets = [
  {
    code: presetCode.sequence,
    description: "Sequence",
    template: "{nnnnnn}",
  },
  {
    code: presetCode.yearSequence,
    description: "Year / Sequence",
    template: "{yyyy}/{nnnnnn}",
  },
  {
    code: presetCode.yearMonthSequence,
    description: "Year - Month / Sequence",
    template: "{yyyy}-{mm}/{nnnnnn}",
  },
  {
    code: presetCode.prefixYearSequence,
    description: "Prefix - Year - Sequence",
    template: "INV-{yyyy}-{nnnnnn}",
  },
  {
    code: presetCode.yearQuarterSequence,
    description: "Year - Quarter / Sequence",
    template: "{yyyy}-Q{q}/{nnnnnn}",
  },
  {
    code: presetCode.custom,
    description: "Custom",
    template: "",
  },
];

const schema = z.object({
  applies_to: z.enum(NumberingSystemAppliesToEnum),
  template: z
    .string()
    .regex(templatePattern, "Invalid template format")
    .min(1, "Template is required")
    .max(100, "Template is too long"),
  reset_interval: z.enum(NumberingSystemResetIntervalEnum),
  description: z.string(),
  preset: z.enum(presetCode),
});

const appliesToOptions = Object.entries(NumberingSystemAppliesToEnum).map(
  ([key, value]) => ({
    value,
    label: `${formatEnum(key)}s`,
  }),
);

type FormValues = z.infer<typeof schema>;

export function NumberingSystemCreateSheet({
  description,
  appliesTo = NumberingSystemAppliesToEnum.invoice,
  onSuccess,
}: {
  description?: string;
  appliesTo?: NumberingSystemAppliesToEnum;
  onSuccess?: (numberingSystem: NumberingSystem) => void;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      applies_to: appliesTo,
      template: "",
      description: description || "",
      reset_interval: "monthly",
      preset: undefined,
    },
  });
  const selectedPreset = form.watch("preset");
  const template = form.watch("template");
  const { mutateAsync, isPending } = useCreateNumberingSystem({
    mutation: {
      onSuccess: async (customer) => {
        await queryClient.invalidateQueries({
          queryKey: getNumberingSystemsListQueryKey(),
        });
        onSuccess?.(customer);
        toast.success("Numbering system created");
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
      data: {
        applies_to: values.applies_to,
        template: values.template,
        reset_interval: values.reset_interval,
        description: values.description || null,
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Create Numbering System</FormSheetTitle>
        <FormSheetDescription>
          Used for automatic document number generation
        </FormSheetDescription>
      </FormSheetHeader>
      <Form {...form}>
        <form id={formId} onSubmit={form.handleSubmit(onSubmit)}>
          <FormSheetGroup>
            <div className="grid gap-2">
              <FormField
                control={form.control}
                name="applies_to"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Applied to</FormLabel>
                    <FormControl>
                      <Select
                        value={field.value}
                        onValueChange={(value) => field.onChange(value)}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select document type" />
                        </SelectTrigger>
                        <SelectContent>
                          {appliesToOptions.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="preset"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      <span>Template</span>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-3.5"
                          >
                            <HelpCircleIcon className="size-3.5 cursor-pointer" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent className="p-3 text-xs">
                          <p className="mb-2 font-medium">
                            Available variables
                          </p>
                          <ul className="grid grid-cols-[70px_1fr] gap-x-2 gap-y-1">
                            <li>
                              <code>{`{yyyy}`}</code>
                            </li>
                            <li>Full year (2025)</li>
                            <li>
                              <code>{`{yy}`}</code>
                            </li>
                            <li>Last two digits (25)</li>
                            <li>
                              <code>{`{q}`}</code>
                            </li>
                            <li>Quarter (1-4)</li>
                            <li>
                              <code>{`{mm}`}</code>
                            </li>
                            <li>Month zero-padded (08)</li>
                            <li>
                              <code>{`{m}`}</code>
                            </li>
                            <li>Month (8)</li>
                            <li>
                              <code>{`{nnnn}`}</code>
                            </li>
                            <li>Sequence number width (0012)</li>
                          </ul>
                        </TooltipContent>
                      </Tooltip>
                    </FormLabel>
                    <FormControl>
                      <Select
                        value={field.value}
                        onValueChange={(value) => {
                          field.onChange(value);
                          const preset = presets.find((p) => p.code === value);
                          form.setValue(
                            "description",
                            preset?.description || "",
                          );
                          form.setValue("template", preset?.template || "");
                        }}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select template" />
                        </SelectTrigger>
                        <SelectContent>
                          {presets.map((preset) => (
                            <SelectItem key={preset.code} value={preset.code}>
                              {preset.description}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {selectedPreset === presetCode.custom && (
                <FormField
                  control={form.control}
                  name="template"
                  render={({ field }) => (
                    <FormItem>
                      <FormControl>
                        <Input placeholder="INV-{yyyy}/{nnnnnn}" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}

              <FormDescription className="font-mono">
                {template ? renderTemplate(template) : "none"}
              </FormDescription>
            </div>

            <FormField
              control={form.control}
              name="reset_interval"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Reset interval</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger className="w-full capitalize">
                        <SelectValue placeholder="Select reset interval" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {Object.values(NumberingSystemResetIntervalEnum).map(
                        (resetInterval) => (
                          <SelectItem
                            key={resetInterval}
                            value={resetInterval}
                            className="capitalize"
                          >
                            {resetInterval}
                          </SelectItem>
                        ),
                      )}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                  <FormDescription>
                    The interval at which the numbering system resets sequence.
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
                    <Input
                      type="text"
                      placeholder="Enter description"
                      {...field}
                    />
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
