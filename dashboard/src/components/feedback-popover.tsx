import type { User } from "@/api/models";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Kbd } from "@/components/ui/kbd";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { useIsMobile } from "@/hooks/use-mobile";
import { cn } from "@/lib/utils";
import { zodResolver } from "@hookform/resolvers/zod";
import { captureFeedback } from "@sentry/react";
import React, { useEffect, useState, useTransition } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  message: z.string().min(1),
});

type FormValues = z.infer<typeof schema>;

interface FeedbackPopoverProps extends Omit<
  React.ComponentPropsWithoutRef<typeof PopoverContent>,
  "children"
> {
  children: React.ReactElement;
  user: User;
}

export function FeedbackPopover({
  className,
  children,
  user,
  side = "right",
  align = "end",
  ...props
}: FeedbackPopoverProps) {
  const [open, setOpen] = useState(false);
  const isMobile = useIsMobile();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      message: "",
    },
  });
  const [isPending, startTransition] = useTransition();

  const onSubmit = (values: FormValues) => {
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
          },
        );
        toast.success("Feedback sent");
        setOpen(false);
      } catch (error) {
        console.error(error);
      }
    });
  };

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (open && (e.metaKey || e.ctrlKey) && e.key === "Enter") {
        form.handleSubmit(onSubmit)();
      }

      const target = e.target as HTMLElement;
      const isTyping =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;

      if (isTyping) return;

      if (!open) {
        if (e.key === "f") {
          e.preventDefault();
          setOpen(true);
        }
        return;
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [open, form, onSubmit]);

  useEffect(() => {
    if (!open) {
      form.reset();
    }
  }, [open, form]);

  if (isMobile) {
    return null;
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>{children}</PopoverTrigger>
      <PopoverContent
        side={side}
        align={align}
        className={cn("relative border-none p-0", className)}
        {...props}
      >
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <FormField
              control={form.control}
              name="message"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="sr-only">Feedback</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Ideas, bugs, or anything else..."
                      className="field-sizing-fixed h-[110px] resize-none p-3"
                      rows={4}
                      {...field}
                    />
                  </FormControl>
                </FormItem>
              )}
            />
            <Button
              size="sm"
              variant="ghost"
              className="absolute right-1.5 bottom-1.5 gap-0"
              type="submit"
              disabled={isPending}
            >
              {isPending ? (
                <Spinner />
              ) : (
                <>
                  Send
                  <Kbd>⌘</Kbd>
                  <Kbd>↵</Kbd>
                </>
              )}
            </Button>
          </form>
        </Form>
      </PopoverContent>
    </Popover>
  );
}
