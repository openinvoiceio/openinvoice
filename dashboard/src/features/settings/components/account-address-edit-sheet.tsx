import {
  getAccountsAddressesListQueryKey,
  useUpdateAccountAddress,
} from "@/api/endpoints/accounts/accounts";
import { CountryEnum, type AddressDetail } from "@/api/models";
import { AddressCountryField } from "@/components/fields/address-country-field";
import { AddressLine1Field } from "@/components/fields/address-line1-field";
import { AddressLine2Field } from "@/components/fields/address-line2-field";
import { AddressLocalityField } from "@/components/fields/address-locality-field";
import { AddressPostalCodeField } from "@/components/fields/address-postal-code-field";
import { AddressStateField } from "@/components/fields/address-state-field";
import { popModal } from "@/components/push-modals";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";
import {
  FormSheetContent,
  FormSheetDescription,
  FormSheetFooter,
  FormSheetGroup,
  FormSheetHeader,
  FormSheetTitle,
} from "@/components/ui/form-sheet";
import { Spinner } from "@/components/ui/spinner";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useId } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
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

export function AccountAddressEditSheet({
  accountId,
  address,
}: {
  accountId: string;
  address: AddressDetail;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      line1: address.line1 || "",
      line2: address.line2 || "",
      locality: address.locality || "",
      state: address.state || "",
      postalCode: address.postal_code || "",
      country: address.country || undefined,
    },
  });
  const { mutateAsync, isPending } = useUpdateAccountAddress({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getAccountsAddressesListQueryKey(accountId),
        });
        toast.success("Address updated");
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
      id: address.id,
      data: {
        line1: values.line1 || null,
        line2: values.line2 || null,
        locality: values.locality || null,
        state: values.state || null,
        postal_code: values.postalCode || null,
        country: values.country || null,
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Edit address</FormSheetTitle>
        <FormSheetDescription>
          Update this saved address for the account.
        </FormSheetDescription>
      </FormSheetHeader>
      <Form {...form}>
        <form id={formId} onSubmit={form.handleSubmit(onSubmit)}>
          <FormSheetGroup>
            <AddressLine1Field name="line1" />
            <AddressLine2Field name="line2" />
            <AddressLocalityField name="locality" />
            <AddressPostalCodeField name="postalCode" />
            <AddressCountryField name="country" />
            <AddressStateField name="state" countryName="country" />
          </FormSheetGroup>
        </form>
      </Form>
      <FormSheetFooter>
        <Button type="submit" form={formId} disabled={isPending}>
          {isPending && <Spinner />}
          Save changes
        </Button>
      </FormSheetFooter>
    </FormSheetContent>
  );
}
