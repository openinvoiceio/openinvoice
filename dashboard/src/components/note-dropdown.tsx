import {
  ActionDropdown,
  type ActionDropdownProps,
  type DropdownAction,
} from "@/components/ui/action-dropdown";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { MoreHorizontalIcon, Trash2Icon } from "lucide-react";

type NoteDropdownData = {
  onDelete: () => Promise<void> | void;
};

type NoteDropdownProps = Omit<
  ActionDropdownProps<NoteDropdownData>,
  "data" | "sections" | "children"
> & {
  onDelete: () => Promise<void> | void;
  isDeleting?: boolean;
};

export function NoteDropdown({
  onDelete,
  isDeleting = false,
  ...props
}: NoteDropdownProps) {
  const deleteAction: DropdownAction<NoteDropdownData> = {
    key: "delete",
    label: "Delete",
    icon: Trash2Icon,
    onSelect: (data) => data.onDelete(),
  };

  return (
    <ActionDropdown
      data={{ onDelete }}
      sections={[{ items: [deleteAction], danger: true }]}
      {...props}
    >
      <Button
        size="icon"
        variant="ghost"
        className="data-[state=open]:bg-accent size-8"
        disabled={isDeleting}
      >
        {isDeleting ? (
          <Spinner className="size-3.5" />
        ) : (
          <MoreHorizontalIcon className="size-4" />
        )}
      </Button>
    </ActionDropdown>
  );
}
