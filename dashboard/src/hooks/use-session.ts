import {
  useGetSession,
  useGetSessionSuspense,
} from "@/api/endpoints/authentication-current-session/authentication-current-session";

export function useSessionSuspense() {
  const { data: session } = useGetSessionSuspense("browser");

  return {
    user: session?.data?.user,
  };
}

export function useSession() {
  const { data, isLoading, isError } = useGetSession("browser");

  return {
    user: data?.data?.user,
    isLoading,
    isError,
  };
}
