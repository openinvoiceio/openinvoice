import { useCallback, useTransition } from "react";
import { toast } from "sonner";

export function useDownload() {
  const [isPending, startTransition] = useTransition();

  const download = useCallback((url?: string, filename?: string) => {
    if (!url) return;

    startTransition(async () => {
      try {
        const response = await fetch(url);
        const blob = await response.blob();
        const anchor = document.createElement("a");
        anchor.href = window.URL.createObjectURL(new Blob([blob]));
        anchor.setAttribute("download", filename || "");
        anchor.target = "_blank";
        document.body.appendChild(anchor);

        anchor.click();
        anchor?.parentNode?.removeChild(anchor);
      } catch (e) {
        console.error(e);
        toast.error("Failed to download file");
      }
    });
  }, []);

  return { isDownloading: isPending, download };
}
