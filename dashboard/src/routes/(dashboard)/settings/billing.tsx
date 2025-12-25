import { useCustomersListSuspense } from "@/api/endpoints/customers/customers";
import { useInvoicesListSuspense } from "@/api/endpoints/invoices/invoices";
import { useProductsListSuspense } from "@/api/endpoints/products/products";
import {
  useCreateStripeBillingPortal,
  useCreateStripeCheckout,
} from "@/api/endpoints/stripe/stripe";
import { BillingProgress } from "@/components/billing-progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DataList,
  DataListItem,
  DataListLabel,
  DataListValue,
} from "@/components/ui/data-list";
import {
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardFooter,
  FormCardFooterInfo,
  FormCardGroup,
  FormCardHeader,
  FormCardSeparator,
  FormCardTitle,
} from "@/components/ui/form-card";
import {
  Section,
  SectionDescription,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { plans } from "@/config/plans";
import { usePlan } from "@/hooks/use-plan";
import { getErrorSummary } from "@/lib/api/errors";
import { formatDate, formatISODate } from "@/lib/formatters";
import { stripePromise } from "@/lib/stripe";
import { cn } from "@/lib/utils";
import { createFileRoute } from "@tanstack/react-router";
import { addMonths, startOfMonth } from "date-fns";
import { CheckIcon } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/(dashboard)/settings/billing")({
  component: RouteComponent,
});

function RouteComponent() {
  const { account } = Route.useRouteContext();
  const datetime = formatISODate(startOfMonth(new Date()));
  const navigate = Route.useNavigate();
  const { data: invoices } = useInvoicesListSuspense({
    created_at_gt: datetime,
  });
  const { data: customers } = useCustomersListSuspense({
    created_at_gt: datetime,
  });
  const { data: products } = useProductsListSuspense({
    created_at_gt: datetime,
  });
  const recommendedPlanId = "standard";
  const { currentPlan, subscription } = usePlan(account);
  const renewalDate = subscription?.ended_at
    ? new Date(subscription.ended_at)
    : startOfMonth(addMonths(new Date(), 1));

  const createStripeCheckout = useCreateStripeCheckout({
    mutation: {
      onSuccess: async (response) => {
        const stripe = await stripePromise;
        if (!stripe) return;
        await stripe.redirectToCheckout({ sessionId: response.session_id });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  const createStripeBillingPortal = useCreateStripeBillingPortal({
    mutation: {
      onSuccess: (billing_portal) => {
        navigate({ to: billing_portal.url });
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description: description });
      },
    },
  });

  function renderLimit(value: string | number | boolean) {
    if (typeof value === "boolean") {
      return value ? (
        <CheckIcon className="text-foreground h-4 w-4" />
      ) : (
        <span className="text-muted-foreground/50">&#8208;</span>
      );
    }
    if (typeof value === "number") {
      return new Intl.NumberFormat("us").format(value).toString();
    }
    return value;
  }

  return (
    <SectionGroup>
      <Section>
        <SectionHeader>
          <SectionTitle>Billing</SectionTitle>
          <SectionDescription>
            Manage your billing information and payment methods.
          </SectionDescription>
        </SectionHeader>
        <FormCardGroup>
          <FormCard>
            <FormCardHeader>
              <FormCardTitle>Subscription</FormCardTitle>
              <FormCardDescription>
                Overview of your current subscription and limits.
              </FormCardDescription>
            </FormCardHeader>
            <FormCardContent>
              <DataList
                className="flex-row gap-6 text-sm"
                orientation="vertical"
              >
                <DataListItem>
                  <DataListLabel>Plan</DataListLabel>
                  <DataListValue>{currentPlan?.title}</DataListValue>
                </DataListItem>
                {subscription && (
                  <DataListItem>
                    <DataListLabel>Status</DataListLabel>
                    <DataListValue>
                      <Badge className="capitalize">
                        {subscription.status}
                      </Badge>
                    </DataListValue>
                  </DataListItem>
                )}
                <DataListItem>
                  <DataListLabel>Price</DataListLabel>
                  <DataListValue>{currentPlan?.price}€/month</DataListValue>
                </DataListItem>
                {subscription && subscription.ended_at !== null && (
                  <DataListItem>
                    <DataListLabel>Renewal date</DataListLabel>
                    <DataListValue>{formatDate(renewalDate)}</DataListValue>
                  </DataListItem>
                )}
                {subscription?.canceled_at && (
                  <DataListItem>
                    <DataListLabel>Cancel date</DataListLabel>
                    <DataListValue>
                      {formatDate(subscription.canceled_at)}
                    </DataListValue>
                  </DataListItem>
                )}
                {subscription?.ended_at && (
                  <DataListItem>
                    <DataListLabel>End date</DataListLabel>
                    <DataListValue>
                      {formatDate(subscription.ended_at)}
                    </DataListValue>
                  </DataListItem>
                )}
                {subscription?.ended_at &&
                  subscription?.status === "trialing" && (
                    <DataListItem>
                      <DataListLabel>Trial end date</DataListLabel>
                      <DataListValue>
                        {formatDate(subscription?.ended_at)}
                      </DataListValue>
                    </DataListItem>
                  )}
              </DataList>
            </FormCardContent>
            <FormCardSeparator />
            <FormCardContent>
              <div className="flex flex-col gap-2">
                <BillingProgress
                  label="Invoices"
                  value={invoices.count}
                  max={currentPlan?.limits?.invoices || 0}
                />
                <BillingProgress
                  label="Customers"
                  value={customers.count}
                  max={currentPlan?.limits?.customers || 0}
                />
                <BillingProgress
                  label="Products"
                  value={products.count}
                  max={currentPlan?.limits?.products || 0}
                />
              </div>
            </FormCardContent>
            <FormCardFooter>
              <FormCardFooterInfo>
                Access your{" "}
                <span className="font-medium">billing information</span>,{" "}
                <span className="font-medium">invoices</span> and{" "}
                <span className="font-medium">payment methods</span> via Stripe.
              </FormCardFooterInfo>
              <Button
                size="sm"
                onClick={() => createStripeBillingPortal.mutateAsync()}
                disabled={createStripeBillingPortal.isPending}
              >
                {createStripeBillingPortal.isPending && <Spinner />}
                Customer Portal
              </Button>
            </FormCardFooter>
          </FormCard>
          <FormCard>
            <FormCardHeader>
              <FormCardTitle>Plans</FormCardTitle>
              <FormCardDescription>
                Choose a plan that fits your needs.
              </FormCardDescription>
            </FormCardHeader>
            <FormCardSeparator />
            <FormCardContent className="pb-4">
              <Table className="relative table-fixed">
                <TableCaption>
                  A list to compare the different features by plan.
                </TableCaption>
                <TableHeader>
                  <TableRow className="hover:bg-background">
                    <TableHead className="bg-background p-2 align-bottom">
                      Features comparison
                    </TableHead>
                    {plans.map(({ id, ...plan }) => {
                      return (
                        <TableHead
                          key={id}
                          className={cn(
                            "text-foreground h-px p-2 align-top",
                            id === recommendedPlanId
                              ? "bg-muted/30"
                              : "bg-background",
                          )}
                        >
                          <div className="flex h-full flex-col justify-between gap-1">
                            <div className="flex flex-1 flex-col gap-1">
                              <p className="text-lg">{plan.title}</p>
                              <p className="text-muted-foreground text-xs font-normal text-wrap">
                                {plan.description}
                              </p>
                            </div>
                            <p className="text-right">
                              <span className="text-lg">{plan.price}€</span>{" "}
                              <span className="text-muted-foreground text-sm font-normal">
                                /month
                              </span>
                            </p>
                            <Button
                              size="sm"
                              variant={
                                id === recommendedPlanId ? "default" : "outline"
                              }
                              onClick={async () => {
                                if (id === currentPlan?.id) return;
                                await createStripeCheckout.mutateAsync({
                                  data: { price_id: plan.priceId || "" },
                                });
                              }}
                              disabled={createStripeCheckout.isPending}
                            >
                              {createStripeCheckout.isPending && <Spinner />}
                              Choose
                            </Button>
                          </div>
                        </TableHead>
                      );
                    })}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Object.keys(plans[0].limits).map((key) => {
                    return (
                      <TableRow key={key}>
                        <TableCell>{key}</TableCell>
                        {plans.map((plan) => {
                          const limitValue =
                            plan.limits[key as keyof typeof plan.limits];

                          return (
                            <TableCell
                              key={plan.id}
                              className={cn(
                                "font-mono",
                                plan.id === recommendedPlanId && "bg-muted/30",
                              )}
                            >
                              {renderLimit(limitValue)}
                            </TableCell>
                          );
                        })}
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </FormCardContent>
          </FormCard>
        </FormCardGroup>
      </Section>
    </SectionGroup>
  );
}
