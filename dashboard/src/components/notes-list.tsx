import { NoteVisibilityEnum } from "@/api/models";
import type { Note } from "@/api/models";
import { NoteDropdown } from "@/components/note-dropdown";
import { Avatar, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { Separator } from "@/components/ui/separator.tsx";
import { Spinner } from "@/components/ui/spinner";
import { formatRelativeDatetime } from "@/lib/formatters";
import { useState } from "react";

type NotesListProps = {
  notes: Note[];
  isLoading?: boolean;
  onDelete: (noteId: string) => Promise<void> | void;
};

export function NotesList({
  notes,
  isLoading = false,
  onDelete,
}: NotesListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleDelete(noteId: string) {
    setDeletingId(noteId);
    try {
      await onDelete(noteId);
    } catch (_error) {
      return;
    } finally {
      setDeletingId(null);
    }
  }

  if (isLoading) {
    return (
      <div className="text-muted-foreground flex items-center gap-2 text-sm">
        <Spinner className="h-4 w-4" />
        <span>Loading notes...</span>
      </div>
    );
  }

  if (notes.length === 0) {
    return (
      <Empty className="border">
        <EmptyHeader>
          <EmptyTitle>No notes yet</EmptyTitle>
          <EmptyDescription>
            Add the first note to start the conversation.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="flex flex-col">
      {notes.map((note) => (
        <div key={note.id} className="group">
          <div className="border-input bg-card rounded-md border px-3 py-2">
            <div className="flex items-center justify-between gap-3 rounded-t-md">
              <div className="flex flex-1 items-start gap-3">
                {note.author.avatar_url && (
                  <Avatar className="size-5 rounded-full">
                    <AvatarImage src={note.author.avatar_url || undefined} />
                  </Avatar>
                )}
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="text-foreground font-medium">
                    {note.author.name}
                  </span>
                  <span className="text-muted-foreground">
                    {formatRelativeDatetime(note.created_at)}
                  </span>
                  {note.visibility === NoteVisibilityEnum.internal && (
                    <Badge variant="secondary" className="text-xs">
                      Internal
                    </Badge>
                  )}
                </div>
              </div>
              <NoteDropdown
                onDelete={() => handleDelete(note.id)}
                isDeleting={deletingId === note.id}
              />
            </div>
            <div className="text-foreground mt-2 whitespace-pre-wrap">
              {note.content}
            </div>
          </div>
          <div className="relative h-4 group-last:hidden">
            <span className="bg-border absolute top-0 bottom-0 left-3 w-px" />
          </div>
        </div>
      ))}
    </div>
  );
}
