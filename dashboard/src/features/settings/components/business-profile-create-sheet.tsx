import {
  getAccountsBusinessProfilesListQueryKey,
  useCreateBusinessProfile,
} from "@/api/endpoints/accounts/accounts";
import { CountryEnum, type BusinessProfile } from "@/api/models";
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
import { Spinner } from "@/components/ui/spinner";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useId } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  legal_name: z.string().optional(),
  legal_number: z.string().optional(),
  email: z.email("Invalid email address").optional(),
  phone: z.string().optional(),
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

export function BusinessProfileCreateSheet({
  accountId,
  onSuccess,
}: {
  accountId: string;
  onSuccess?: (profile: BusinessProfile) => void;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      legal_name: "",
      legal_number: "",
      email: "",
      phone: "",
      address: {
        line1: "",
        line2: "",
        locality: "",
        state: "",
        postalCode: "",
        country: undefined,
      },
    },
  });
  const { mutateAsync, isPending } = useCreateBusinessProfile({
    mutation: {
      onSuccess: async (profile) => {
        await queryClient.invalidateQueries({
          queryKey: getAccountsBusinessProfilesListQueryKey(accountId),
        });
        onSuccess?.(profile);
        toast.success("Business profile created");
        popModal();
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      accountId,
      data: {
        legal_name: values.legal_name || null,
        legal_number: values.legal_number || null,
        email: values.email || null,
        phone: values.phone || null,
        address: {
          line1: values.address.line1 || null,
          line2: values.address.line2 || null,
          locality: values.address.locality || null,
          state: values.address.state || null,
          postal_code: values.address.postalCode || null,
          country: values.address.country || null,
        },
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Create business profile</FormSheetTitle>
        <FormSheetDescription>
          Add a business profile defining the legal and contact information
          about your business.
        </FormSheetDescription>
      </FormSheetHeader>
      <Form {...form}>
        <form id={formId} onSubmit={form.handleSubmit(onSubmit)}>
          <FormSheetGroup>
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
                </FormItem>
              )}
            />
          </FormSheetGroup>
          <FormSheetGroup>
            <FormSheetGroupTitle>Contact information</FormSheetGroupTitle>
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
            <FormField
              control={form.control}
              name="phone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Phone</FormLabel>
                  <FormControl>
                    <Input placeholder="+1234567890" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormSheetGroup>
          <FormSheetGroup>
            <FormSheetGroupTitle>Address</FormSheetGroupTitle>
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
