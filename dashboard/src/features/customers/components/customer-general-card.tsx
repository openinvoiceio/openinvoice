import {
  getCustomersListQueryKey,
  getCustomersRetrieveQueryKey,
  useUpdateCustomer,
} from "@/api/endpoints/customers/customers";
import { useUploadFile } from "@/api/endpoints/files/files";
import { getInvoicesListQueryKey } from "@/api/endpoints/invoices/invoices";
import { FilePurposeEnum, type Customer } from "@/api/models";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
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
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardFooter,
  FormCardHeader,
  FormCardSeparator,
  FormCardTitle,
} from "@/components/ui/form-card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { UserIcon } from "lucide-react";
import React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  logo: z
    .file()
    .max(512 * 1024, "Logo must be less than 512KB")
    .mime(["image/png", "image/jpeg", "image/svg+xml"])
    .optional(),
});

type FormValues = z.infer<typeof schema>;

export function CustomerGeneralCard({
  customer,
  ...props
}: Omit<React.ComponentProps<"form">, "onSubmit"> & {
  customer: Customer;
}) {
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: customer.name,
      description: customer.description || "",
    },
  });
  const uploadFile = useUploadFile({
    mutation: {
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });
  const { mutateAsync, isPending } = useUpdateCustomer({
    mutation: {
      onSuccess: async ({ id }) => {
        await queryClient.invalidateQueries({
          queryKey: getCustomersListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getCustomersRetrieveQueryKey(id),
        });
        await queryClient.invalidateQueries({
          queryKey: getInvoicesListQueryKey(),
        });
        toast.success("Customer updated");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (isPending) return;

    let logoId: string | undefined;
    if (values.logo) {
      const file = await uploadFile.mutateAsync({
        data: { file: values.logo, purpose: FilePurposeEnum.customer_logo },
      });
      logoId = file.id;
    }

    await mutateAsync({
      id: customer.id,
      data: {
        name: values.name,
        description: values.description || null,
        ...(logoId && { logo_id: logoId }),
      },
    });
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} {...props}>
        <FormCard>
          <FormCardHeader>
            <FormCardTitle>General</FormCardTitle>
            <FormCardDescription>
              Manage your essential customer information.
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent>
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
                    Display name of the customer. This name will be displayed on
                    invoices
                  </FormDescription>
                </FormItem>
              )}
            />
            <FormField
              name="logo"
              render={({ field: { value, onChange, ...fieldProps } }) => (
                <FormItem>
                  <FormLabel>Logo</FormLabel>
                  <FormControl>
                    <div className="flex items-center gap-2">
                      <Avatar className="size-9 rounded-md">
                        <AvatarImage src={customer.logo_url || undefined} />
                        <AvatarFallback className="rounded-md">
                          <UserIcon className="size-4.5" />
                        </AvatarFallback>
                      </Avatar>
                      <Input
                        {...fieldProps}
                        type="file"
                        placeholder="Upload logo"
                        onChange={(event) =>
                          onChange(event.target.files && event.target.files[0])
                        }
                      />
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </FormCardContent>
          <FormCardSeparator />
          <FormCardContent>
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea {...field} />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    Additional information about the customer. This can include
                    notes, preferences, or any other relevant details.
                  </FormDescription>
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
