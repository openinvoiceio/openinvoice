import { useUploadFile } from "@/api/endpoints/files/files";
import {
  getProductsListQueryKey,
  getProductsRetrieveQueryKey,
  useUpdateProduct,
} from "@/api/endpoints/products/products";
import { FilePurposeEnum, type Product } from "@/api/models";
import { popModal } from "@/components/push-modals";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
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
  FormSheetFooter,
  FormSheetGroup,
  FormSheetHeader,
  FormSheetTitle,
} from "@/components/ui/form-sheet";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { BoxIcon } from "lucide-react";
import { useId } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string(),
  image: z
    .file()
    .max(512 * 1024, "Image must be less than 512KB")
    .mime(["image/png", "image/jpeg", "image/svg+xml"])
    .optional(),
});

type FormValues = z.infer<typeof schema>;

export function ProductEditSheet({
  product,
  onSuccess,
}: {
  product: Product;
  onSuccess?: (product: Product) => void;
}) {
  const formId = useId();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: product.name,
      description: product.description || "",
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

  const { isPending, mutateAsync } = useUpdateProduct({
    mutation: {
      onSuccess: async (product) => {
        await queryClient.invalidateQueries({
          queryKey: getProductsListQueryKey(),
        });
        await queryClient.invalidateQueries({
          queryKey: getProductsRetrieveQueryKey(product.id),
        });
        onSuccess?.(product);
        toast.success("Product updated");
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

    let imageId: string | undefined;
    if (values.image) {
      const file = await uploadFile.mutateAsync({
        data: { file: values.image, purpose: FilePurposeEnum.product_image },
      });
      imageId = file.id;
    }

    await mutateAsync({
      id: product.id,
      data: {
        name: values.name,
        description: values.description || null,
        ...(imageId && { image_id: imageId }),
      },
    });
  }

  return (
    <FormSheetContent>
      <FormSheetHeader>
        <FormSheetTitle>Update Product</FormSheetTitle>
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
                    <Input type="text" placeholder="Enter name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
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
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="image"
              render={({ field: { value, onChange, ...fieldProps } }) => (
                <FormItem>
                  <FormLabel>Image</FormLabel>
                  <FormControl>
                    <div className="flex items-center gap-2">
                      <Avatar className="rounded-md">
                        <AvatarImage src={product.image_url || undefined} />
                        <AvatarFallback className="rounded-md">
                          <BoxIcon className="size-4" />
                        </AvatarFallback>
                      </Avatar>
                      <Input
                        {...fieldProps}
                        type="file"
                        placeholder="Upload image"
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
