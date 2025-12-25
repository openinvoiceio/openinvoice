import * as React from "react";

export function useMediaQuery(query: string) {
  const getSnapshot = React.useCallback(() => {
    if (typeof window === "undefined") {
      return false;
    }

    return window.matchMedia(query).matches;
  }, [query]);

  const subscribe = React.useCallback(
    (callback: () => void) => {
      if (typeof window === "undefined") {
        return () => {};
      }

      const mediaQueryList = window.matchMedia(query);
      mediaQueryList.addEventListener("change", callback);

      return () => mediaQueryList.removeEventListener("change", callback);
    },
    [query],
  );

  return React.useSyncExternalStore(subscribe, getSnapshot, () => false);
}
