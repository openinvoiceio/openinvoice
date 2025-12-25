import { useVerifyEmail } from "@/api/endpoints/authentication-account/authentication-account";
import { getGetSessionQueryKey } from "@/api/endpoints/authentication-current-session/authentication-current-session.ts";
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
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card";
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from "@/components/ui/input-otp";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

export const Route = createFileRoute("/(public)/verification")({
  component: RouteComponent,
});

const OTP_LENGTH = 6;

const schema = z.object({
  key: z.string().min(OTP_LENGTH, {
    message: `Verification code must be at least ${OTP_LENGTH} characters long`,
  }),
});

type FormValues = z.infer<typeof schema>;

function RouteComponent() {
  const navigate = Route.useNavigate();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      key: "",
    },
  });

  const { mutateAsync, isPending } = useVerifyEmail({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getGetSessionQueryKey("browser"),
        });
      },
      onError: async (error) => {
        const response = error.response?.data;
        if (response?.status === 401) {
          await navigate({ to: "/login" });
        } else if (response?.status === 409) {
          toast.error("Verification code expired. Please login again.");
          await navigate({ to: "/login" });
        } else if (response?.status === 400) {
          response?.errors?.map((e) => {
            form.setError("key", {
              type: "custom",
              message: e.message.toString(),
            });
          });
        }
      },
    },
  });

  const key = form.watch("key");
  useEffect(() => {
    if (key?.length === OTP_LENGTH) {
      form.trigger("key").then((ok) => {
        if (ok) form.handleSubmit(onSubmit)();
      });
    }
  }, [key, form]);

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      client: "browser",
      data: {
        key: values.key,
      },
    });
  }

  return (
    <main className="flex h-svh w-full items-center justify-center">
      <Form {...form}>
        <form className="w-full max-w-lg">
          <FormCard>
            <FormCardHeader>
              <FormCardTitle>Email verification</FormCardTitle>
              <FormCardDescription>
                Please enter the verification code sent to your email address.
              </FormCardDescription>
            </FormCardHeader>
            <FormCardContent>
              <FormField
                control={form.control}
                name="key"
                render={({ field }) => (
                  <FormItem className="mx-auto">
                    <FormLabel className="sr-only">
                      Email verification
                    </FormLabel>
                    <FormControl>
                      <InputOTP maxLength={OTP_LENGTH} {...field}>
                        <InputOTPGroup>
                          {Array.from({ length: OTP_LENGTH }).map((_, i) => (
                            <InputOTPSlot
                              key={i}
                              index={i}
                              className="h-12 w-12 text-2xl"
                            />
                          ))}
                        </InputOTPGroup>
                      </InputOTP>
                    </FormControl>
                    <FormMessage className="mx-auto" />
                  </FormItem>
                )}
              />
            </FormCardContent>
            <FormCardFooter className="flex flex-col">
              <Button
                type="button"
                onClick={() => navigate({ to: "/login" })}
                className="w-full"
              >
                Back to login
              </Button>
            </FormCardFooter>
          </FormCard>
        </form>
      </Form>
    </main>
  );
}
