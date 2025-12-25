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
  FormCardSeparator,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { formatCountry } from "@/lib/formatters";
import { zodResolver } from "@hookform/resolvers/zod";
import { allCountries } from "country-region-data";
import React, { useTransition } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

const schema = z.object({
  line1: z.string().optional(),
  line2: z.string().optional(),
  locality: z.string().optional(),
  state: z.string().optional(),
  postalCode: z.string().optional(),
  country: z.enum(CountryEnum).optional(),
});

type FormValues = z.infer<typeof schema>;

export function AddressCard({
  title,
  description,
  defaultValues,
  onSubmit,
  ...props
}: Omit<React.ComponentProps<"form">, "onSubmit"> & {
  description?: string;
  defaultValues?: FormValues;
  onSubmit?: (values: FormValues) => Promise<void>;
}) {
  const [isPending, startTransition] = useTransition();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: defaultValues ?? {
      line1: "",
      line2: "",
      locality: "",
      state: "",
      postalCode: "",
      country: undefined,
    },
  });
  const country = form.watch("country");
  const countryData = allCountries.find(
    ([, countrySlug]) => countrySlug === country,
  );
  const regions = countryData ? countryData[2] : [];

  function submitAction(values: FormValues) {
    if (isPending) return;
    startTransition(async () => await onSubmit?.(values));
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(submitAction)} {...props}>
        <FormCard>
          <FormCardHeader>
            <FormCardTitle>{title || "Address"}</FormCardTitle>
            {description && (
              <FormCardDescription>{description}</FormCardDescription>
            )}
          </FormCardHeader>
          <FormCardContent>
            <FormField
              control={form.control}
              name="line1"
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
              name="line2"
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
              name="locality"
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
              name="postalCode"
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
              name="country"
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
              name="state"
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
            <Button type="submit" disabled={isPending}>
              {isPending && <Spinner />}
              Submit
            </Button>
          </FormCardFooter>
        </FormCard>
      </form>
    </Form>
  );
}
