import { NoteVisibilityEnum } from "@/api/models";
import type { Note } from "@/api/models";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { Spinner } from "@/components/ui/spinner";
import { formatDatetime } from "@/lib/formatters";
import { Trash2Icon, UserIcon } from "lucide-react";
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
    <div className="space-y-4">
      {notes.map((note) => (
        <div key={note.id} className="flex gap-3">
          <Avatar className="mt-1 size-8 rounded-md">
            <AvatarImage src={note.author.avatar_url || undefined} />
            <AvatarFallback className="rounded-md">
              <UserIcon className="size-4" />
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 space-y-2">
            <div className="flex items-start justify-between gap-3">
              <div className="text-muted-foreground flex flex-wrap items-center gap-2 text-sm">
                <span className="text-foreground font-medium">
                  {note.author.name}
                </span>
                <span>{formatDatetime(note.created_at)}</span>
                {note.visibility === NoteVisibilityEnum.internal && (
                  <Badge variant="secondary">Internal</Badge>
                )}
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => handleDelete(note.id)}
                disabled={deletingId === note.id}
                className="h-8 w-8"
              >
                {deletingId === note.id ? (
                  <Spinner className="h-4 w-4" />
                ) : (
                  <Trash2Icon className="h-4 w-4" />
                )}
              </Button>
            </div>
            <div className="bg-muted/40 rounded-lg border px-3 py-2 text-sm">
              {note.content}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
