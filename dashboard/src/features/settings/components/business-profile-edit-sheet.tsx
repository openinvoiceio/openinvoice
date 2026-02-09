import {
  getAccountsBusinessProfilesListQueryKey,
  useAccountsRetrieve,
  useUpdateBusinessProfile,
} from "@/api/endpoints/accounts/accounts";
import type { AccountBusinessProfile } from "@/api/models";
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
  FormSheetHeader,
  FormSheetTitle,
} from "@/components/ui/form-sheet";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { AccountAddressCombobox } from "@/features/settings/components/account-address-combobox";
import { AccountTaxIdsCombobox } from "@/features/settings/components/account-tax-ids-combobox";
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
  addressId: z.string().nullable().optional(),
  tax_ids: z.array(z.string()).optional(),
});

type FormValues = z.infer<typeof schema>;

export function BusinessProfileEditSheet({
  profile,
  accountId,
}: {
  profile: AccountBusinessProfile;
  accountId: string;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const { data: account } = useAccountsRetrieve(accountId, {
    query: { enabled: !!accountId },
  });
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      legal_name: profile.legal_name || "",
      legal_number: profile.legal_number || "",
      email: profile.email || "",
      phone: profile.phone || "",
      addressId: profile.address?.id ?? null,
      tax_ids: profile.tax_ids?.map((taxId) => taxId.id) ?? [],
    },
  });
  const { mutateAsync, isPending } = useUpdateBusinessProfile({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getAccountsBusinessProfilesListQueryKey(accountId),
        });
        toast.success("Business profile updated");
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
      id: profile.id,
      data: {
        legal_name: values.legal_name || null,
        legal_number: values.legal_number || null,
        email: values.email || null,
        phone: values.phone || null,
        address_id: values.addressId || null,
        tax_ids: values.tax_ids ?? [],
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Edit business profile</FormSheetTitle>
        <FormSheetDescription>
          Update business profile details for your account.
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
            <FormField
              control={form.control}
              name="addressId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Address</FormLabel>
                  <FormControl>
                    <AccountAddressCombobox
                      accountId={accountId}
                      value={field.value ?? null}
                      onChange={field.onChange}
                      placeholder="Select address"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="tax_ids"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tax IDs</FormLabel>
                  <FormControl>
                    <AccountTaxIdsCombobox
                      taxIds={account?.tax_ids ?? []}
                      value={field.value ?? []}
                      onChange={field.onChange}
                      placeholder="Select tax ids"
                      multiple
                      disabled={!account || account.tax_ids.length === 0}
                    />
                  </FormControl>
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
          Save changes
        </Button>
      </FormSheetFooter>
    </FormSheetContent>
  );
}
