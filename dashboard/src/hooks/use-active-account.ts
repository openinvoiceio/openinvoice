import { useAccountsRetrieveSuspense } from "@/api/endpoints/accounts/accounts";
import { useSessionSuspense } from "@/hooks/use-session";

export function useActiveAccount() {
  const { user } = useSessionSuspense();
  const { data } = useAccountsRetrieveSuspense(user.active_account_id);

  return { account: data };
}
