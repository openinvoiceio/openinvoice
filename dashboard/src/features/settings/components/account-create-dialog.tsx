import { useCreateAccount } from "@/api/endpoints/accounts/accounts";
import { CountryEnum } from "@/api/models";
import { CountryCombobox } from "@/components/country-combobox.tsx";
import { popModal } from "@/components/push-modals.tsx";
import { Button } from "@/components/ui/button";
import { ComboboxButton } from "@/components/ui/combobox-button.tsx";
import {
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogGroup,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { useActiveAccount } from "@/hooks/use-active-account";
import { useSessionSuspense } from "@/hooks/use-session";
import { getErrorSummary } from "@/lib/api/errors";
import { formatCountry } from "@/lib/formatters";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import z from "zod";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  legal_name: z.string().optional(),
  legal_number: z.string().optional(),
  email: z.email("Invalid email address"),
  country: z.enum(CountryEnum),
});

type FormValues = z.infer<typeof schema>;

export function AccountCreateDialog() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useSessionSuspense();
  const { account } = useActiveAccount();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      legal_name: "",
      legal_number: "",
      email: user.email,
      country: account.country,
    },
  });
  const { mutateAsync, isPending } = useCreateAccount({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries();
        toast.success("Account created");
        await navigate({ to: "/overview" });
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      data: {
        name: values.name,
        legal_name: values.legal_name || null,
        legal_number: values.legal_number || null,
        email: values.email,
        country: values.country,
      },
    });
  }

  return (
    <DialogContent>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Create account</DialogTitle>
            <DialogDescription>
              Create a new account to collaborate with your colleagues
            </DialogDescription>
          </DialogHeader>
          <DialogGroup>
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
                    Display name of your company
                  </FormDescription>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="legal_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Legal name</FormLabel>
                  <FormControl>
                    <Input placeholder="Acme Corporation LLC" {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    Registered legal name of your company
                  </FormDescription>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="legal_number"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Legal number</FormLabel>
                  <FormControl>
                    <Input placeholder="123456789" {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    Government-issued registration number
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
                    <ComboboxButton>
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
          </DialogGroup>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="secondary" disabled={isPending}>
                Cancel
              </Button>
            </DialogClose>
            <Button type="submit" disabled={isPending}>
              {isPending && <Spinner />}
              Submit
            </Button>
          </DialogFooter>
        </form>
      </Form>
    </DialogContent>
  );
}
