import {
  getAccountsListQueryKey,
  useCreateAccount,
} from "@/api/endpoints/accounts/accounts";
import { getGetSessionQueryKey } from "@/api/endpoints/authentication-current-session/authentication-current-session";
import { CountryEnum } from "@/api/models";
import { CountryCombobox } from "@/components/country-combobox.tsx";
import { Button } from "@/components/ui/button";
import { ComboboxButton } from "@/components/ui/combobox-button.tsx";
import {
  Form,
  FormControl,
  FormDescription,
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
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { formatCountry } from "@/lib/formatters";
import { zodResolver } from "@hookform/resolvers/zod";
import { createFileRoute } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { z } from "zod";

export const Route = createFileRoute("/setup/")({
  component: RouteComponent,
});

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.email("Invalid email address"),
  country: z.enum(CountryEnum, { error: "Country is required" }),
});

type FormValues = z.infer<typeof schema>;

function RouteComponent() {
  const { auth, queryClient } = Route.useRouteContext();
  const navigate = Route.useNavigate();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      email: auth?.user?.email,
      country: undefined,
    },
  });
  const { mutateAsync, isPending } = useCreateAccount({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getAccountsListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getGetSessionQueryKey("browser"),
        });
        navigate({ to: "/onboarding" });
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      data: {
        name: values.name,
        email: values.email,
        country: values.country,
      },
    });
  }

  return (
    <main className="flex h-svh w-full items-center justify-center">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FormCard>
            <FormCardHeader>
              <FormCardTitle>Register account</FormCardTitle>
              <FormCardDescription>
                Register a new account to access the dashboard.
              </FormCardDescription>
            </FormCardHeader>
            <FormCardContent className="grid gap-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Acme Corporation" {...field} />
                    </FormControl>
                    <FormMessage />
                    <FormDescription>
                      Legal name of your company fullname
                    </FormDescription>
                  </FormItem>
                )}
              />
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
                name="country"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Country of operation</FormLabel>
                    <CountryCombobox
                      selected={field.value}
                      onSelect={async (value) => field.onChange(value ?? "")}
                    >
                      <ComboboxButton className="w-full">
                        {field.value ? (
                          <span>{formatCountry(field.value)}</span>
                        ) : (
                          <span className="text-muted-foreground">
                            Select country
                          </span>
                        )}
                      </ComboboxButton>
                    </CountryCombobox>
                    <FormMessage />
                    <FormDescription>
                      The country in which your business is registered or where
                      you reside.
                    </FormDescription>
                  </FormItem>
                )}
              />
            </FormCardContent>
            <FormCardFooter>
              <Button type="submit" disabled={isPending}>
                {isPending && <Spinner />}
                Submit
              </Button>
            </FormCardFooter>
          </FormCard>
        </form>
      </Form>
    </main>
  );
}
