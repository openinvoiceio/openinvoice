import { Button } from "@/components/ui/button.tsx";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty.tsx";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form.tsx";
import { Input } from "@/components/ui/input.tsx";
import { useDebouncedCallback } from "@/hooks/use-debounced-callback.ts";
import { cn, listToRecord, recordToList } from "@/lib/utils.ts";
import { zodResolver } from "@hookform/resolvers/zod";
import { PlusIcon, XIcon } from "lucide-react";
import React from "react";
import { useFieldArray, useForm } from "react-hook-form";
import { z } from "zod";

const schema = z.object({
  metadata: z.array(
    z.object({
      key: z.string().min(1, "Key is required"),
      value: z.string(),
    }),
  ),
});

type FormValues = z.infer<typeof schema>;

export function Metadata({
  data,
  className,
  onSubmit,
  submitOnChange,
  ...props
}: Omit<React.ComponentProps<"form">, "onSubmit"> & {
  data?: Record<string, string>;
  onSubmit?: (metadata: Record<string, string>) => void;
  submitOnChange?: boolean;
}) {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      metadata: recordToList(data),
    },
  });
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "metadata",
  });

  function handleSubmit(values: FormValues) {
    const metadata = listToRecord(values.metadata);
    onSubmit?.(metadata);
  }

  const submit = form.handleSubmit(handleSubmit);
  const debouncedSubmit = useDebouncedCallback(() => submit(), 1000);

  return (
    <Form {...form}>
      <form onSubmit={submit} {...props}>
        <div className={cn("flex flex-col gap-4", className)}>
          {fields.length === 0 && (
            <Empty>
              <EmptyHeader>
                <EmptyTitle>No metadata defined</EmptyTitle>
                <EmptyDescription>
                  Metadata is useful for storing additional information
                </EmptyDescription>
              </EmptyHeader>
            </Empty>
          )}
          <div className="flex flex-col gap-2">
            {fields.map((field, index) => (
              <div key={field.id} className="flex gap-2">
                <FormField
                  control={form.control}
                  name={`metadata.${index}.key`}
                  render={({ field }) => (
                    <FormItem className="w-full">
                      <FormControl>
                        <Input
                          placeholder="Key"
                          className="h-8 text-xs"
                          {...field}
                          onChange={(e) => {
                            field.onChange(e);
                            submitOnChange && debouncedSubmit();
                          }}
                        />
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
                        <Input
                          placeholder="Value"
                          className="h-8"
                          {...field}
                          onChange={(e) => {
                            field.onChange(e);
                            submitOnChange && debouncedSubmit();
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
                  onClick={() => {
                    remove(index);
                    submitOnChange && debouncedSubmit();
                  }}
                  className="size-8 shrink-0"
                >
                  <XIcon />
                </Button>
              </div>
            ))}
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => append({ key: "", value: "" })}
            disabled={fields.length >= 20}
          >
            <PlusIcon />
            Add item
          </Button>
        </div>
      </form>
    </Form>
  );
}
