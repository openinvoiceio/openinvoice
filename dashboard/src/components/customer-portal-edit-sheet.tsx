import {
  getPortalCustomerRetrieveQueryKey,
  useUpdatePortalCustomer,
} from "@/api/endpoints/portal/portal";
import { CountryEnum, type PortalCustomer } from "@/api/models";
import { CountryCombobox } from "@/components/country-combobox.tsx";
import { popModal } from "@/components/push-modals";
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
  FormSheetContent,
  FormSheetDescription,
  FormSheetFooter,
  FormSheetGroup,
  FormSheetGroupTitle,
  FormSheetHeader,
  FormSheetTitle,
} from "@/components/ui/form-sheet";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { getErrorSummary } from "@/lib/api/errors";
import { formatCountry } from "@/lib/formatters";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { allCountries } from "country-region-data";
import { useId } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  legal_name: z.string().optional(),
  legal_number: z.string().optional(),
  email: z.email("Invalid email address").optional(),
  billing_address: z.object({
    line1: z.string().optional(),
    line2: z.string().optional(),
    locality: z.string().optional(),
    state: z.string().optional(),
    postalCode: z.string().optional(),
    country: z.enum(CountryEnum),
  }),
});

type FormValues = z.infer<typeof schema>;

export function CustomerPortalEditSheet({
  customer,
  token,
  onSuccess,
}: {
  customer: PortalCustomer;
  token: string;
  onSuccess?: (customer: PortalCustomer) => void;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: customer.name || "",
      legal_name: customer.legal_name || "",
      legal_number: customer.legal_number || "",
      email: customer.email || "",
      billing_address: {
        line1: customer.billing_address?.line1 || "",
        line2: customer.billing_address?.line2 || "",
        locality: customer.billing_address?.locality || "",
        state: customer.billing_address?.state || "",
        postalCode: customer.billing_address?.postal_code || "",
        country: customer.billing_address?.country || undefined,
      },
    },
  });
  const country = form.watch("billing_address.country");
  const countryData = allCountries.find(
    ([, countrySlug]) => countrySlug === country,
  );
  const regions = countryData ? countryData[2] : [];
  const { mutateAsync, isPending } = useUpdatePortalCustomer({
    request: {
      headers: { Authorization: `Bearer ${token}` },
    },
    mutation: {
      onSuccess: async (customer) => {
        await queryClient.invalidateQueries({
          queryKey: getPortalCustomerRetrieveQueryKey(),
        });
        onSuccess?.(customer);
        toast.success("Information updated");
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
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Update information</FormSheetTitle>
        <FormSheetDescription>
          Update your billing information. This information will be used for
          invoicing.
        </FormSheetDescription>
      </FormSheetHeader>
      <Form {...form}>
        <form id={formId} onSubmit={form.handleSubmit(onSubmit)}>
          <FormSheetGroup>
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
                    Your full name or your company&apos;s name
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
                  <FormDescription>Your official legal name</FormDescription>
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
                    Your company&apos;s official registration number
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
          </FormSheetGroup>
          <Separator />
          <FormSheetGroup>
            <FormSheetGroupTitle>Billing address</FormSheetGroupTitle>
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
          </FormSheetGroup>
        </form>
      </Form>
      <FormSheetFooter>
        <Button type="submit" form={formId} disabled={isPending}>
          {isPending && <Spinner />}
          Submit
        </Button>
      </FormSheetFooter>
    </FormSheetContent>
  );
}
