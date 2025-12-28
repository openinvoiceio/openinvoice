import { useGetConfig } from "@/api/endpoints/config/config.ts";

export function usePlan() {
  const { data } = useGetConfig();
  const currentPlan = data?.plans.find(
    (plan) => plan.code === data.current_plan_code,
  );

  function hasFeature(code: string): boolean {
    if (!currentPlan) return false;
    return currentPlan.features.some((feature) => feature.code === code);
  }

  function withinLimit(code: string, usage: number): boolean {
    if (!currentPlan) return false;
    const limit = currentPlan.limits.find((limit) => limit.code === code);
    if (!limit || limit.limit === null) return true; // Unlimited
    return usage < limit.limit;
  }

  function getLimit(code: string): number | null {
    if (!currentPlan) return null;
    const limit = currentPlan.limits.find((limit) => limit.code === code);
    return limit ? limit.limit : null;
  }

  return {
    currentPlan,
    isBillingEnabled: data?.is_billing_enabled,
    hasFeature,
    withinLimit,
    getLimit,
  };
}
