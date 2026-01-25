import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { allCountries } from "country-region-data";
import { useFormContext, useWatch } from "react-hook-form";

type AddressStateFieldProps = {
  name?: string;
  countryName?: string;
  label?: string;
  placeholder?: string;
  description?: string;
  className?: string;
};

export function AddressStateField({
  name = "state",
  countryName = "country",
  label = "State",
  placeholder = "Select state",
  description,
  className,
}: AddressStateFieldProps) {
  const form = useFormContext();
  const country = useWatch({ control: form.control, name: countryName });
  const countryData = allCountries.find(
    ([, countrySlug]) => countrySlug === country,
  );
  const regions = countryData ? countryData[2] : [];

  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem className={className}>
          <FormLabel>{label}</FormLabel>
          <Select
            defaultValue={field.value}
            onValueChange={field.onChange}
            disabled={regions.length === 0}
          >
            <FormControl>
              <SelectTrigger className="w-full">
                <SelectValue placeholder={placeholder} />
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
          {description && <FormDescription>{description}</FormDescription>}
        </FormItem>
      )}
    />
  );
}
