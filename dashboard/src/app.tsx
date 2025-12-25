import { useAccountsRetrieve } from "@/api/endpoints/accounts/accounts.ts";
import { useGetSession } from "@/api/endpoints/authentication-current-session/authentication-current-session";
import { Spinner } from "@/components/ui/spinner.tsx";
import { router } from "@/router";
import { RouterProvider } from "@tanstack/react-router";

export function App() {
  const session = useGetSession("browser");
  const account = useAccountsRetrieve(
    session.data?.data?.user.active_account_id || "",
    { query: { enabled: !!session?.data } },
  );
  const isLoading = session.isLoading || account.isLoading;

  if (isLoading) {
    return (
      <div className="flex min-h-svh w-full items-center justify-center p-6 md:p-10">
        <div className="w-full max-w-lg">
          <Spinner variant="background" />
        </div>
      </div>
    );
  }

  return (
    <RouterProvider
      router={router}
      context={{ auth: session.data?.data, account: account.data }}
    />
  );
}
