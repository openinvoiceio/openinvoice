import { NoteVisibilityEnum } from "@/api/models";
import type { Note } from "@/api/models";
import { Avatar, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { Separator } from "@/components/ui/separator.tsx";
import { Spinner } from "@/components/ui/spinner";
import { formatRelativeDatetime } from "@/lib/formatters";
import { Trash2Icon } from "lucide-react";
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
        <div key={note.id} className="border-input rounded-lg border">
          <div className="bg-card flex items-center justify-between gap-3 rounded-t-lg px-3 py-1">
            <div className="flex flex-1 items-start gap-3">
              {note.author.avatar_url && (
                <Avatar className="mt-0.5 size-5 rounded-full">
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
                  <Badge variant="secondary">Internal</Badge>
                )}
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => handleDelete(note.id)}
              disabled={deletingId === note.id}
              className="size-8"
            >
              {deletingId === note.id ? (
                <Spinner className="size-3.5" />
              ) : (
                <Trash2Icon className="size-3.5" />
              )}
            </Button>
          </div>
          <Separator />
          <div className="text-foreground px-3 py-3 text-sm whitespace-pre-wrap">
            {note.content}
          </div>
        </div>
      ))}
    </div>
  );
}
