import { NoteVisibilityEnum } from "@/api/models";
import type { Note, NoteCreate } from "@/api/models";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { Section, SectionHeader, SectionTitle } from "@/components/ui/section";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { formatDatetime } from "@/lib/formatters";
import { Trash2Icon, UserIcon } from "lucide-react";
import { useState } from "react";

type NotesSectionProps = {
  notes: Note[];
  isLoading?: boolean;
  isPending?: boolean;
  onCreate: (data: NoteCreate) => Promise<Note> | void;
  onDelete: (noteId: string) => Promise<void> | void;
};

export function NotesSection({
  notes,
  isLoading = false,
  isPending = false,
  onCreate,
  onDelete,
}: NotesSectionProps) {
  const [content, setContent] = useState("");
  const [visibility, setVisibility] = useState<NoteVisibilityEnum>(
    NoteVisibilityEnum.internal,
  );
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const canSubmit = content.trim().length > 0 && !isPending;

  async function handleCreate() {
    if (!canSubmit) return;
    try {
      await onCreate({ content: content.trim(), visibility });
      setContent("");
    } catch (_error) {
      return;
    }
  }

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

  return (
    <Section>
      <SectionHeader>
        <SectionTitle>Notes</SectionTitle>
      </SectionHeader>
      <div className="space-y-4">
        <div className="bg-muted/30 space-y-3 rounded-lg border p-4">
          <Textarea
            className="text-foreground min-h-[96px]"
            placeholder="Write a note..."
            value={content}
            onChange={(event) => setContent(event.target.value)}
            maxLength={2048}
          />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Select
              value={visibility}
              onValueChange={(value) =>
                setVisibility(value as NoteVisibilityEnum)
              }
            >
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Visibility" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NoteVisibilityEnum.internal}>
                  Internal
                </SelectItem>
                <SelectItem value={NoteVisibilityEnum.public}>
                  Public
                </SelectItem>
              </SelectContent>
            </Select>
            <Button
              type="button"
              size="sm"
              onClick={handleCreate}
              disabled={!canSubmit}
            >
              {isPending ? <Spinner /> : "Add note"}
            </Button>
          </div>
        </div>
        {isLoading ? (
          <div className="text-muted-foreground flex items-center gap-2 text-sm">
            <Spinner className="h-4 w-4" />
            <span>Loading notes...</span>
          </div>
        ) : notes.length === 0 ? (
          <Empty className="border">
            <EmptyHeader>
              <EmptyTitle>No notes yet</EmptyTitle>
              <EmptyDescription>
                Add the first note to start the conversation.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        ) : (
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
        )}
      </div>
    </Section>
  );
}
