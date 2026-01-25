import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useFormContext } from "react-hook-form";

type AddressPostalCodeFieldProps = {
  name?: string;
  label?: string;
  placeholder?: string;
  description?: string;
  className?: string;
};

export function AddressPostalCodeField({
  name = "postalCode",
  label = "Postal code",
  placeholder = "Enter postal code",
  description = "ZIP or postal code",
  className,
}: AddressPostalCodeFieldProps) {
  const form = useFormContext();

  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem className={className}>
          <FormLabel>{label}</FormLabel>
          <FormControl>
            <Input placeholder={placeholder} {...field} />
          </FormControl>
          <FormMessage />
          {description && <FormDescription>{description}</FormDescription>}
        </FormItem>
      )}
    />
  );
}
