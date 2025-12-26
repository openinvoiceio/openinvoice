import { useRequestPasswordReset } from "@/api/endpoints/authentication-password-reset/authentication-password-reset";
import { Button } from "@/components/ui/button";
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
  FormCardFooterInfo,
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { zodResolver } from "@hookform/resolvers/zod";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

export const Route = createFileRoute("/(public)/recovery")({
  component: RouteComponent,
});

const schema = z.object({
  email: z.email("Invalid email address"),
});

type FormValues = z.infer<typeof schema>;

function RouteComponent() {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "",
    },
  });
  const { mutateAsync, isPending } = useRequestPasswordReset({
    mutation: {
      onSuccess: () => {
        toast.success("Password reset email sent");
      },
      onError: (error) => {
        const response = error.response?.data;
        if (response?.status === 400) {
          response?.errors?.map((e) => {
            form.setError((e.param as "email") || "root", {
              type: "custom",
              message: e.message.toString(),
            });
          });
          toast.error("Invalid request");
        } else {
          toast.error("Password reset failed");
        }
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      client: "browser",
      data: {
        email: values.email,
      },
    });
  }

  return (
    <main className="flex h-svh w-full items-center justify-center">
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="w-full max-w-lg"
        >
          <FormCard>
            <FormCardHeader>
              <FormCardTitle>Recovery</FormCardTitle>
              <FormCardDescription>
                We will send you an email with instructions on how to reset your
                password.
              </FormCardDescription>
            </FormCardHeader>
            <FormCardContent>
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="name@example.com"
                        type="email"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormCardContent>
            <FormCardFooter className="flex flex-col">
              <Button type="submit" disabled={isPending} className="w-full">
                {isPending && <Spinner />}
                Reset password
              </Button>
              <FormCardFooterInfo className="flex w-full justify-center gap-1">
                <span>Remember your password?</span>
                <Link to="/login" className="underline underline-offset-4">
                  Back to login
                </Link>
              </FormCardFooterInfo>
            </FormCardFooter>
          </FormCard>
        </form>
      </Form>
    </main>
  );
}
