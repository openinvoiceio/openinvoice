import { useSignup } from "@/api/endpoints/authentication-account/authentication-account";
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
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { hasPendingFlow } from "@/lib/api/auth";
import { zodResolver } from "@hookform/resolvers/zod";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

export const Route = createFileRoute("/(public)/signup")({
  component: RouteComponent,
});

const schema = z.object({
  email: z.email("Invalid email address"),
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
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "",
      password: "",
    },
  });
  const { mutateAsync, isPending } = useSignup({
    mutation: {
      onError: async (error) => {
        const response = error.response?.data;
        if (hasPendingFlow(response, "verify_email")) {
          return navigate({ to: "/verification" });
        } else if (response?.status === 403) {
          toast.error("Signup failed", {
            description: "Please try again later",
          });
        } else if (response?.status === 400) {
          response?.errors?.map((e) => {
            form.setError(e.param || "root", {
              type: "custom",
              message: e.message.toString(),
            });
          });
        } else {
          toast.error("Signup failed");
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
    <main className="flex h-svh w-full items-center justify-center">
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="w-full max-w-lg"
        >
          <FormCard>
            <FormCardHeader>
              <FormCardTitle>Signup</FormCardTitle>
              <FormCardDescription>
                Enter your email and password below to signup
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
                Signup
              </Button>
              <FormCardFooterInfo className="flex w-full justify-center gap-1">
                <span>Already have an account?</span>
                <Link to="/login" className="underline underline-offset-4">
                  Login
                </Link>
              </FormCardFooterInfo>
            </FormCardFooter>
          </FormCard>
        </form>
      </Form>
    </main>
  );
}
