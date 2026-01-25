import { CountryCombobox } from "@/components/country-combobox";
import { ComboboxButton } from "@/components/ui/combobox-button";
import {
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { formatCountry } from "@/lib/formatters";
import { useFormContext } from "react-hook-form";

type AddressCountryFieldProps = {
  name?: string;
  label?: string;
  placeholder?: string;
  description?: string;
  className?: string;
};

export function AddressCountryField({
  name = "country",
  label = "Country",
  placeholder = "Select country",
  description,
  className,
}: AddressCountryFieldProps) {
  const form = useFormContext();

  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem className={className}>
          <FormLabel>{label}</FormLabel>
          <CountryCombobox
            selected={field.value}
            onSelect={async (value) => field.onChange(value ?? "")}
          >
            <ComboboxButton>
              {field.value ? (
                <span>{formatCountry(field.value)}</span>
              ) : (
                <span className="text-muted-foreground">{placeholder}</span>
              )}
            </ComboboxButton>
          </CountryCombobox>
          <FormMessage />
          {description && <FormDescription>{description}</FormDescription>}
        </FormItem>
      )}
    />
  );
}
