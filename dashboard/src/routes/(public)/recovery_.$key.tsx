import { useResetPassword } from "@/api/endpoints/authentication-password-reset/authentication-password-reset";
import { PasswordInput } from "@/components/password-input";
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
import { Spinner } from "@/components/ui/spinner";
import { zodResolver } from "@hookform/resolvers/zod";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

export const Route = createFileRoute("/(public)/recovery_/$key")({
  component: RouteComponent,
});

const schema = z.object({
  password: z
    .string()
    .min(8, {
      message: "Password must be at least 8 characters long.",
    })
    .refine((pw) => !/^\d+$/.test(pw), {
      message: "Password cannot be entirely numeric.",
    }),
});

type FormValues = z.infer<typeof schema>;

function RouteComponent() {
  const navigate = Route.useNavigate();
  const { key } = Route.useParams();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      password: "",
    },
  });
  const { mutateAsync, isPending } = useResetPassword({
    mutation: {
      onError: (error) => {
        const response = error.response?.data;
        if (response?.status === 401) {
          toast.success("Password reset");
          return navigate({ to: "/login" });
        } else if (response?.status === 400) {
          response?.errors?.map((e) => {
            form.setError((e.param as "password") || "root", {
              type: "custom",
              message: e.message.toString(),
            });
          });
          toast.error("Invalid request");
        } else {
          return navigate({ to: "/login" });
        }
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      client: "browser",
      data: {
        key,
        password: values.password,
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
              <FormCardDescription>Enter your new password</FormCardDescription>
            </FormCardHeader>
            <FormCardContent>
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>New password</FormLabel>
                    <FormControl>
                      <PasswordInput placeholder="Password" {...field} />
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
