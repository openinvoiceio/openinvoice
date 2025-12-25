import { useLogin } from "@/api/endpoints/authentication-account/authentication-account";
import { getGetSessionQueryKey } from "@/api/endpoints/authentication-current-session/authentication-current-session.ts";
import { PasswordInput } from "@/components/password-input.tsx";
import { Button } from "@/components/ui/button.tsx";
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
import { Spinner } from "@/components/ui/spinner.tsx";
import { hasPendingFlow } from "@/lib/api/auth";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import z from "zod";

export const Route = createFileRoute("/(public)/login")({
  component: RouteComponent,
});

const schema = z.object({
  email: z.email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
});

type FormValues = z.infer<typeof schema>;

function RouteComponent() {
  const navigate = Route.useNavigate();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "",
      password: "",
    },
  });
  const { mutateAsync, isPending } = useLogin({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getGetSessionQueryKey("browser"),
        });
      },
      onError: async (error) => {
        const response = error.response?.data;
        if (hasPendingFlow(response, "verify_email")) {
          return navigate({ to: "/verification" });
        } else if (response?.status === 400) {
          response?.errors?.map((e) => {
            form.setError(e.param || "root", {
              type: "custom",
              message: e.message.toString(),
            });
          });
        } else {
          toast.error("Login failed");
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
        password: values.password,
      },
    });
  }

  return (
    <main className="flex h-svh w-full items-center justify-center p-6 md:p-10">
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="w-full max-w-lg"
        >
          <FormCard>
            <FormCardHeader>
              <FormCardTitle>Login</FormCardTitle>
              <FormCardDescription>
                Enter your email and password below to login
              </FormCardDescription>
            </FormCardHeader>
            <FormCardContent className="grid gap-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder="name@example.com"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="flex justify-between">
                      <span>Password</span>
                      <Link
                        to="/recovery"
                        className="underline-offset-4 hover:underline"
                      >
                        Forgot password?
                      </Link>
                    </FormLabel>
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
                Login
              </Button>
              <FormCardFooterInfo className="flex w-full justify-center gap-1">
                <span>Don&apos;t have an account?</span>
                <Link to="/signup" className="underline underline-offset-4">
                  Signup
                </Link>
              </FormCardFooterInfo>
            </FormCardFooter>
          </FormCard>
        </form>
      </Form>
    </main>
  );
}
