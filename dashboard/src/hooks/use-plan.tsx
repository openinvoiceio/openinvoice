import type { Account } from "@/api/models";
import { plans } from "@/config/plans";

export function usePlan(account: Account) {
  const currentPlan = plans.find(
    (v) => v.priceId === account?.subscription?.price_id,
  );

  return { currentPlan, subscription: account.subscription };
}
