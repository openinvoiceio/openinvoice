import { popModal } from "@/components/push-modals";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DialogContent,
  DialogDescription,
  DialogGroup,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { useSessionSuspense } from "@/hooks/use-session";
import { zodResolver } from "@hookform/resolvers/zod";
import { captureFeedback } from "@sentry/react";
import { useTransition } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const types = [
  {
    label: "Report a bug",
    value: "bug" as const,
  },
  {
    label: "Book a demo",
    value: "demo" as const,
  },
  {
    label: "Suggest a feature",
    value: "feature" as const,
  },
  {
    label: "Report a security issue",
    value: "security" as const,
  },
  {
    label: "Something else",
    value: "question" as const,
  },
];

const schema = z.object({
  type: z.enum(["bug", "demo", "feature", "security", "question"]),
  message: z.string().min(1, { message: "Message is required" }),
  blocker: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

export function SupportDialog() {
  const { user } = useSessionSuspense();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      type: undefined,
      message: "",
      blocker: false,
    },
  });
  const [isPending, startTransition] = useTransition();
  const watchType = form.watch("type");

  async function onSubmit(values: FormValues) {
    if (isPending) return;

    startTransition(async () => {
      try {
        captureFeedback(
          {
            name: user.name,
            email: user.email,
            message: values.message,
          },
          {
            includeReplay: false,
            captureContext: {
              tags: { type: values.type, blocker: values.blocker },
            },
          },
        );
        toast.success("Request sent");
        popModal();
      } catch (error) {
        console.error(error);
      }
    });
  }

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Support</DialogTitle>
        <DialogDescription>
          Please fill out the form below to get in touch with us.
        </DialogDescription>
      </DialogHeader>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <DialogGroup className="my-0">
            <FormField
              control={form.control}
              name="type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Type</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="What you need help with" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {types.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            {watchType ? (
              <FormField
                control={form.control}
                name="message"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Message</FormLabel>
                    <FormControl>
                      <Textarea placeholder="Tell us about it..." {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            ) : null}
            {watchType === "bug" ? (
              <FormField
                control={form.control}
                name="blocker"
                render={({ field }) => (
                  <FormItem className="flex items-start">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <FormLabel className="leading-none font-normal">
                      This bug prevents me from using the product.
                    </FormLabel>
                  </FormItem>
                )}
              />
            ) : null}
            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending && <Spinner />}
              Submit
            </Button>
          </DialogGroup>
        </form>
      </Form>
    </DialogContent>
  );
}
