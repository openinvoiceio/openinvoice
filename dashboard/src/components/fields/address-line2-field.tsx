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

type AddressLine2FieldProps = {
  name?: string;
  label?: string;
  placeholder?: string;
  description?: string;
  className?: string;
};

export function AddressLine2Field({
  name = "line2",
  label = "Line 2",
  placeholder = "Enter line 2",
  description = "Apartment, suite, unit, building, floor, etc.",
  className,
}: AddressLine2FieldProps) {
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
