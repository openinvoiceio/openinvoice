import { useChangePassword } from "@/api/endpoints/account-password/account-password";
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
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Spinner } from "@/components/ui/spinner";
import { zodResolver } from "@hookform/resolvers/zod";
import React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  current_password: z.string().min(1, "Password is required"),
  new_password: z
    .string()
    .min(8, {
      message: "Password must be at least 8 characters long.",
    })
    .refine((pw) => !/^\d+$/.test(pw), {
      message: "Password cannot be entirely numeric.",
    }),
});

type FormValues = z.infer<typeof schema>;

export function ProfilePasswordCard({
  hasUsablePassword,
  ...props
}: Omit<React.ComponentProps<"form">, "onSubmit"> & {
  hasUsablePassword: boolean;
}) {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      current_password: "",
      new_password: "",
    },
  });
  const { mutateAsync, isPending } = useChangePassword({
    mutation: {
      onSuccess: async () => {
        toast.success("Password changed");
      },
      onError: (error) => {
        const response = error.response?.data;
        if (response?.status === 400) {
          response?.errors?.map((e) => {
            // @ts-ignore
            form.setError(e.attr || "root", { message: e.detail });
          });
          toast.error("Invalid request");
        } else {
          toast.error("Could not change password");
        }
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      client: "browser",
      data: {
        current_password: values.current_password,
        new_password: values.new_password,
      },
    });
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} {...props}>
        <FormCard>
          <FormCardHeader>
            <FormCardTitle>Password</FormCardTitle>
            <FormCardDescription>
              Update your password to keep your account secure.
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent>
            {hasUsablePassword && (
              <FormField
                control={form.control}
                name="current_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Current password</FormLabel>
                    <FormControl>
                      <PasswordInput
                        placeholder="Enter current password"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}
            <FormField
              control={form.control}
              name="new_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>New password</FormLabel>
                  <FormControl>
                    <PasswordInput
                      placeholder="Enter new password"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormCardContent>
          <FormCardFooter>
            <Button type="submit" size="sm" disabled={isPending}>
              {isPending && <Spinner />}
              Submit
            </Button>
          </FormCardFooter>
        </FormCard>
      </form>
    </Form>
  );
}
