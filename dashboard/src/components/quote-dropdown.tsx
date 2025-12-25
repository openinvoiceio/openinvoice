import { useFilesRetrieve } from "@/api/endpoints/files/files";
import {
  getPreviewQuoteQueryKey,
  getQuotesListQueryKey,
  getQuotesRetrieveQueryKey,
  useAcceptQuote,
  useCancelQuote,
  useDeleteQuote,
  useFinalizeQuote,
} from "@/api/endpoints/quotes/quotes";
import { QuoteStatusEnum, type Quote } from "@/api/models";
import {
  ActionDropdown,
  type ActionDropdownProps,
  type DropdownAction,
} from "@/components/ui/action-dropdown";
import { useDownload } from "@/hooks/use-download";
import { getErrorSummary } from "@/lib/api/errors";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import {
  ArrowRightIcon,
  BanIcon,
  CheckIcon,
  CopyIcon,
  DownloadIcon,
  PencilIcon,
  Trash2Icon,
} from "lucide-react";
import { toast } from "sonner";

export function useEditQuoteAction(): DropdownAction<Quote> {
  const navigate = useNavigate();
  return {
    key: "edit",
    label: "Edit",
    icon: PencilIcon,
    shortcut: "E",
    hotkey: "e",
    visible: (quote) => quote.status === QuoteStatusEnum.draft,
    onSelect: (quote) =>
      navigate({ to: "/quotes/$id/edit", params: { id: quote.id } }),
  };
}

export function useCopyQuoteIdAction(): DropdownAction<Quote> {
  return {
    key: "copy-id",
    label: "Copy ID",
    icon: CopyIcon,
    shortcut: "C",
    hotkey: "c",
    onSelect: async (quote) => {
      await navigator.clipboard.writeText(quote.id);
      toast.success("Copied to clipboard");
    },
  };
}

export function useFinalizeQuoteAction(): DropdownAction<Quote> {
  const queryClient = useQueryClient();
  const finalizeQuote = useFinalizeQuote({
    mutation: {
      onSuccess: async (quote) => {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: getQuotesListQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getQuotesRetrieveQueryKey(quote.id),
          }),
          queryClient.invalidateQueries({
            queryKey: getPreviewQuoteQueryKey(quote.id),
          }),
        ]);
        toast.success("Quote finalized");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return {
    key: "finalize",
    label: "Finalize",
    icon: CheckIcon,
    visible: (quote) => quote.status === QuoteStatusEnum.draft,
    onSelect: (quote) => void finalizeQuote.mutateAsync({ quoteId: quote.id }),
  };
}

export function useAcceptQuoteAction(): DropdownAction<Quote> {
  const queryClient = useQueryClient();
  const acceptQuote = useAcceptQuote({
    mutation: {
      onSuccess: async (quote) => {
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: getQuotesListQueryKey() }),
          queryClient.invalidateQueries({
            queryKey: getQuotesRetrieveQueryKey(quote.id),
          }),
          queryClient.invalidateQueries({
            queryKey: getPreviewQuoteQueryKey(quote.id),
          }),
        ]);
        toast.success("Quote accepted");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return {
    key: "accept",
    label: "Accept",
    icon: ArrowRightIcon,
    visible: (quote) => quote.status === QuoteStatusEnum.open,
    onSelect: (quote) => void acceptQuote.mutateAsync({ quoteId: quote.id }),
  };
}

export function useCancelQuoteAction(): DropdownAction<Quote> {
  const queryClient = useQueryClient();
  const cancelQuote = useCancelQuote({
    mutation: {
      onSuccess: async (quote) => {
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: getQuotesListQueryKey() }),
          queryClient.invalidateQueries({
            queryKey: getQuotesRetrieveQueryKey(quote.id),
          }),
          queryClient.invalidateQueries({
            queryKey: getPreviewQuoteQueryKey(quote.id),
          }),
        ]);
        toast.success("Quote canceled");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return {
    key: "cancel",
    label: "Cancel",
    icon: BanIcon,
    visible: (quote) => quote.status === QuoteStatusEnum.open,
    onSelect: (quote) => void cancelQuote.mutateAsync({ quoteId: quote.id }),
  };
}

export function useDownloadQuoteAction(quote: Quote): DropdownAction<Quote> {
  const enabled = !!quote.pdf_id;
  const { data: file } = useFilesRetrieve(quote.pdf_id || "", {
    query: { enabled },
  });
  const { isDownloading, download } = useDownload();
  const filename = `${quote.number}.pdf`;

  return {
    key: "download",
    label: "Download",
    icon: DownloadIcon,
    shortcut: "D",
    hotkey: "d",
    visible: () => enabled,
    disabled: () => !file?.url || isDownloading,
    onSelect: () => download(file?.url, filename),
  };
}

export function useDeleteQuoteAction(): DropdownAction<Quote> {
  const queryClient = useQueryClient();
  const deleteQuote = useDeleteQuote({
    mutation: {
      onSuccess: async (_, { id }) => {
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: getQuotesListQueryKey() }),
          queryClient.invalidateQueries({
            queryKey: getQuotesRetrieveQueryKey(),
          }),
          queryClient.invalidateQueries({
            queryKey: getQuotesRetrieveQueryKey(id),
          }),
          queryClient.invalidateQueries({
            queryKey: getPreviewQuoteQueryKey(id),
          }),
        ]);
        toast.success("Quote deleted");
      },
      onError: (error) => {
        const { message, description } = getErrorSummary(error);
        toast.error(message, { description });
      },
    },
  });

  return {
    key: "delete",
    label: "Delete",
    icon: Trash2Icon,
    disabled: (quote) => quote.status !== QuoteStatusEnum.draft,
    onSelect: (quote) =>
      void toast.promise(deleteQuote.mutateAsync({ id: quote.id }), {
        loading: "Deleting quote...",
        success: "Quote deleted",
        error: (error) => getErrorSummary(error).message,
      }),
  };
}

export type QuoteActionKey =
  | "edit"
  | "copy-id"
  | "finalize"
  | "accept"
  | "cancel"
  | "download"
  | "delete";

export function QuoteDropdown({
  quote,
  actions,
  ...props
}: Omit<ActionDropdownProps<Quote>, "data" | "sections" | "actions"> & {
  quote: Quote;
  actions?: QuoteActionKey[] | Partial<Record<QuoteActionKey, boolean>>;
}) {
  return (
    <ActionDropdown
      data={quote}
      actions={actions}
      sections={[
        { items: [useEditQuoteAction(), useCopyQuoteIdAction()] },
        {
          items: [
            useFinalizeQuoteAction(),
            useAcceptQuoteAction(),
            useCancelQuoteAction(),
          ],
        },
        { items: [useDownloadQuoteAction(quote)] },
        { items: [useDeleteQuoteAction()], danger: true },
      ]}
      {...props}
    />
  );
}
