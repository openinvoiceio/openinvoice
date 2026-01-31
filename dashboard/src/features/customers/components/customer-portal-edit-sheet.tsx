import {
  getPortalCustomerRetrieveQueryKey,
  useUpdatePortalCustomer,
} from "@/api/endpoints/portal/portal";
import { CountryEnum, type PortalCustomer } from "@/api/models";
import { AddressCountryField } from "@/components/fields/address-country-field";
import { AddressLine1Field } from "@/components/fields/address-line1-field";
import { AddressLine2Field } from "@/components/fields/address-line2-field";
import { AddressLocalityField } from "@/components/fields/address-locality-field";
import { AddressPostalCodeField } from "@/components/fields/address-postal-code-field";
import { AddressStateField } from "@/components/fields/address-state-field";
import { popModal } from "@/components/push-modals";
import { Button } from "@/components/ui/button";
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
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useId } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  legal_name: z.string().optional(),
  legal_number: z.string().optional(),
  email: z.email("Invalid email address").optional(),
  shipping: z.object({
    name: z.string().optional(),
    phone: z.string().optional(),
    address: z.object({
      line1: z.string().optional(),
      line2: z.string().optional(),
      locality: z.string().optional(),
      state: z.string().optional(),
      postalCode: z.string().optional(),
      country: z.enum(CountryEnum).optional(),
    }),
  }),
  address: z.object({
    line1: z.string().optional(),
    line2: z.string().optional(),
    locality: z.string().optional(),
    state: z.string().optional(),
    postalCode: z.string().optional(),
    country: z.enum(CountryEnum).optional(),
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
      address: {
        line1: customer.address?.line1 || "",
        line2: customer.address?.line2 || "",
        locality: customer.address?.locality || "",
        state: customer.address?.state || "",
        postalCode: customer.address?.postal_code || "",
        country: customer.address?.country || undefined,
      },
      shipping: {
        name: customer.shipping?.name || "",
        phone: customer.shipping?.phone || "",
        address: {
          line1: customer.shipping?.address?.line1 || "",
          line2: customer.shipping?.address?.line2 || "",
          locality: customer.shipping?.address?.locality || "",
          state: customer.shipping?.address?.state || "",
          postalCode: customer.shipping?.address?.postal_code || "",
          country: customer.shipping?.address?.country || undefined,
        },
      },
    },
  });
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
        address: {
          line1: values.address.line1 || null,
          line2: values.address.line2 || null,
          locality: values.address.locality || null,
          state: values.address.state || null,
          postal_code: values.address.postalCode || null,
          country: values.address.country || null,
        },
        shipping: {
          name: values.shipping.name || null,
          phone: values.shipping.phone || null,
          address: {
            line1: values.shipping.address.line1 || null,
            line2: values.shipping.address.line2 || null,
            locality: values.shipping.address.locality || null,
            state: values.shipping.address.state || null,
            postal_code: values.shipping.address.postalCode || null,
            country: values.shipping.address.country || null,
          },
        },
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Update information</FormSheetTitle>
        <FormSheetDescription>
          Update your billing and shipping information. This information will be
          used for invoicing.
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
            <AddressLine1Field name="address.line1" />
            <AddressLine2Field name="address.line2" />
            <AddressLocalityField name="address.locality" />
            <AddressPostalCodeField name="address.postalCode" />
            <AddressCountryField name="address.country" />
            <AddressStateField
              name="address.state"
              countryName="address.country"
            />
          </FormSheetGroup>
          <Separator />
          <FormSheetGroup>
            <FormSheetGroupTitle>Shipping</FormSheetGroupTitle>
            <FormField
              control={form.control}
              name="shipping.name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Shipping name</FormLabel>
                  <FormControl>
                    <Input placeholder="Recipient name" {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    Recipient name for shipping deliveries.
                  </FormDescription>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="shipping.phone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Shipping phone</FormLabel>
                  <FormControl>
                    <Input placeholder="+1234567890" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormSheetGroup>
          <Separator />
          <FormSheetGroup>
            <FormSheetGroupTitle>Shipping address</FormSheetGroupTitle>
            <AddressLine1Field name="shipping.address.line1" />
            <AddressLine2Field name="shipping.address.line2" />
            <AddressLocalityField name="shipping.address.locality" />
            <AddressPostalCodeField name="shipping.address.postalCode" />
            <AddressCountryField name="shipping.address.country" />
            <AddressStateField
              name="shipping.address.state"
              countryName="shipping.address.country"
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
