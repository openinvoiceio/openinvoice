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

type AddressLine1FieldProps = {
  name?: string;
  label?: string;
  placeholder?: string;
  description?: string;
  className?: string;
};

export function AddressLine1Field({
  name = "line1",
  label = "Line 1",
  placeholder = "Enter line 1",
  description = "Main street address",
  className,
}: AddressLine1FieldProps) {
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
