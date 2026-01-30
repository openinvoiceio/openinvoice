import { NoteVisibilityEnum, type Note } from "@/api/models";
import type { NoteCreate } from "@/api/models";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Spinner } from "@/components/ui/spinner";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { zodResolver } from "@hookform/resolvers/zod";
import { PlusIcon } from "lucide-react";
import { useForm } from "react-hook-form";
import z from "zod";

const schema = z.object({
  content: z
    .string()
    .trim()
    .min(1, "Note cannot be empty")
    .max(2048, "Note is too long"),
  visibility: z.enum([NoteVisibilityEnum.internal, NoteVisibilityEnum.public]),
});

type FormValues = z.infer<typeof schema>;

export function NotesForm({
  isCreating = false,
  onCreate,
}: {
  isCreating?: boolean;
  onCreate: (data: NoteCreate) => Promise<Note> | void;
}) {
  const form = useForm<FormValues>({
    defaultValues: {
      content: "",
      visibility: NoteVisibilityEnum.internal,
    },
    mode: "onSubmit",
    reValidateMode: "onSubmit",
    resolver: zodResolver(schema),
  });

  async function handleCreate(values: FormValues) {
    await onCreate({
      content: values.content.trim(),
      visibility: values.visibility,
    });
    form.reset({ content: "", visibility: NoteVisibilityEnum.internal });
  }

  const contentValue = form.watch("content");
  const isDisabled = isCreating || contentValue.trim().length === 0;

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(handleCreate)}
        className="bg-input/30 focus-within:border-ring border-input rounded-lg border px-3 py-2 transition-colors"
      >
        <FormField
          control={form.control}
          name="content"
          render={({ field }) => (
            <FormItem>
              <FormControl>
                <Textarea
                  {...field}
                  className="text-foreground min-h-12 resize-none border-none bg-transparent p-0 text-sm shadow-none focus-visible:border-transparent focus-visible:ring-0 dark:bg-transparent"
                  placeholder="Write a note..."
                  maxLength={2048}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      if (!isDisabled) {
                        void form.handleSubmit(handleCreate)();
                      }
                    }
                  }}
                />
              </FormControl>
            </FormItem>
          )}
        />
        <div className="mt-2 flex items-center justify-between gap-3">
          <FormField
            control={form.control}
            name="visibility"
            render={({ field }) => (
              <FormItem className="flex items-center gap-2">
                <FormControl>
                  <Switch
                    checked={field.value === NoteVisibilityEnum.internal}
                    onCheckedChange={(checked) =>
                      field.onChange(
                        checked
                          ? NoteVisibilityEnum.internal
                          : NoteVisibilityEnum.public,
                      )
                    }
                    className="data-[state=checked]:bg-foreground"
                  />
                </FormControl>
                <FormLabel className="text-xs">Internal</FormLabel>
              </FormItem>
            )}
          />
          <Button
            type="submit"
            size="icon"
            className="size-7"
            disabled={isDisabled}
          >
            {isCreating ? <Spinner /> : <PlusIcon />}
          </Button>
        </div>
      </form>
    </Form>
  );
}
