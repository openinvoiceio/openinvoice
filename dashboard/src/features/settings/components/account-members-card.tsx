import {
  getInvitationsListQueryKey,
  useCreateInvitation,
} from "@/api/endpoints/invitations/invitations";
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
  FormCardFooterInfo,
  FormCardHeader,
  FormCardSeparator,
  FormCardTitle,
  FormCardUpgrade,
} from "@/components/ui/form-card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { InvitationsTable } from "@/features/settings/components/invitations-table";
import { MembersTable } from "@/features/settings/components/members-table";
import { getErrorSummary } from "@/lib/api/errors";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { LockIcon } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const schema = z.object({
  email: z.email(),
});

type FormValues = z.infer<typeof schema>;

export function AccountMembersCard({ isLocked }: { isLocked: boolean }) {
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "",
    },
  });
  const { mutateAsync, isPending } = useCreateInvitation({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getInvitationsListQueryKey(),
        });
        toast.success("Invitation sent successfully");
      },
      onError: async (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  async function onSubmit(values: FormValues) {
    if (isPending) return;
    await mutateAsync({
      data: { email: values.email },
    });
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormCard>
          {isLocked && <FormCardUpgrade />}
          <FormCardHeader>
            <FormCardTitle>Members</FormCardTitle>
            <FormCardDescription>
              Manage your account members.
            </FormCardDescription>
          </FormCardHeader>
          <FormCardContent>
            <Tabs defaultValue="members">
              <TabsList>
                <TabsTrigger value="members">Members</TabsTrigger>
                <TabsTrigger value="invitations">Pending</TabsTrigger>
              </TabsList>
              <TabsContent value="members">
                <MembersTable />
              </TabsContent>
              <TabsContent value="invitations">
                <InvitationsTable />
              </TabsContent>
            </Tabs>
          </FormCardContent>
          <FormCardSeparator />
          <FormCardContent>
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
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                  <FormDescription>
                    Send an invitation to join the account.
                  </FormDescription>
                </FormItem>
              )}
            />
          </FormCardContent>
          <FormCardFooter>
            {isLocked ? (
              <>
                <FormCardFooterInfo>
                  This feature is available on the{" "}
                  <Link to="/settings/billing" className="font-medium">
                    Standard plan
                  </Link>
                  .
                </FormCardFooterInfo>
                <Button type="button" asChild>
                  <Link to="/settings/billing">
                    <LockIcon />
                    Upgrade
                  </Link>
                </Button>
              </>
            ) : (
              <Button type="submit" disabled={isPending}>
                {isPending && <Spinner />}
                Submit
              </Button>
            )}
          </FormCardFooter>
        </FormCard>
      </form>
    </Form>
  );
}
