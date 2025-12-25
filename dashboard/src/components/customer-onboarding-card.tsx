import {
  getCustomersListQueryKey,
  useCreateCustomer,
} from "@/api/endpoints/customers/customers.ts";
import { CountryEnum } from "@/api/models";
import { CountryCombobox } from "@/components/country-combobox.tsx";
import { Button } from "@/components/ui/button";
import { ComboboxButton } from "@/components/ui/combobox-button.tsx";
import {
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardFooter,
  FormCardHeader,
  FormCardSeparator,
  FormCardTitle,
} from "@/components/ui/form-card";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form.tsx";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select.tsx";
import { getErrorSummary } from "@/lib/api/errors.ts";
import { formatCountry } from "@/lib/formatters";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { allCountries } from "country-region-data";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { Input } from "./ui/input";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.email("Invalid email address").optional(),
  billing_address: z.object({
    line1: z.string().optional(),
    line2: z.string().optional(),
    locality: z.string().optional(),
    state: z.string().optional(),
    postalCode: z.string().optional(),
    country: z.enum(CountryEnum).optional(),
  }),
});

type FormValues = z.infer<typeof schema>;

export function CustomerOnboardingCard() {
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      email: undefined,
      billing_address: {
        line1: "",
        line2: "",
        locality: "",
        state: "",
        postalCode: "",
        country: undefined,
      },
    },
  });
  const country = form.watch("billing_address.country");
  const countryData = allCountries.find(
    ([, countrySlug]) => countrySlug === country,
  );
  const regions = countryData ? countryData[2] : [];

  const { mutateAsync, isPending } = useCreateCustomer({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getCustomersListQueryKey(),
        });
        toast.success("Customer created");
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
        email: values.email,
        billing_address: {
          line1: values.billing_address.line1 || null,
          line2: values.billing_address.line2 || null,
          locality: values.billing_address.locality || null,
          state: values.billing_address.state || null,
          postal_code: values.billing_address.postalCode || null,
          country: values.billing_address.country || null,
        },
      },
    });
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormCard>
          <FormCardHeader>
            <FormCardTitle>Create a customer</FormCardTitle>
            <FormCardDescription>
              Add your first customer to get started with invoicing.
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent className="grid-cols-2">
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
                  <FormDescription>Full name or company name.</FormDescription>
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
                      autoCapitalize="none"
                      autoComplete="email"
                      autoCorrect="off"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormCardContent>
          <FormCardSeparator />
          <FormCardContent>
            <FormField
              control={form.control}
              name="billing_address.line1"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Line 1</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter line 1" {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>Main street address</FormDescription>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="billing_address.line2"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Line 2</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter line 2" {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    Apartment, suite, unit, building, floor, etc.
                  </FormDescription>
                </FormItem>
              )}
            />
          </FormCardContent>
          <FormCardSeparator />
          <FormCardContent className="grid-cols-2">
            <FormField
              control={form.control}
              name="billing_address.locality"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Locality</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter locality" {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>City or town name</FormDescription>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="billing_address.postalCode"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Postal code</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter postal code" {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>ZIP or postal code</FormDescription>
                </FormItem>
              )}
            />
          </FormCardContent>
          <FormCardSeparator />
          <FormCardContent className="grid-cols-2">
            <FormField
              control={form.control}
              name="billing_address.country"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Country</FormLabel>
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
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="billing_address.state"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>State</FormLabel>
                  <Select
                    defaultValue={field.value}
                    onValueChange={field.onChange}
                    disabled={regions.length === 0}
                  >
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select state" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {regions.map(([region]) => (
                        <SelectItem key={region} value={region}>
                          {region}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormCardContent>
          <FormCardFooter>
            <Button type="submit">Submit</Button>
          </FormCardFooter>
        </FormCard>
      </form>
    </Form>
  );
}
