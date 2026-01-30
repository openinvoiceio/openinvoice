import { CommentVisibilityEnum } from "@/api/models";
import type { Comment } from "@/api/models";
import { CommentDropdown } from "@/components/comment-dropdown";
import { Avatar, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { Spinner } from "@/components/ui/spinner";
import { formatRelativeDatetime } from "@/lib/formatters";
import { useState } from "react";

type CommentsListProps = {
  comments: Comment[];
  isLoading?: boolean;
  onDelete: (commentId: string) => Promise<void> | void;
};

export function CommentsList({
  comments,
  isLoading = false,
  onDelete,
}: CommentsListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleDelete(commentId: string) {
    setDeletingId(commentId);
    try {
      await onDelete(commentId);
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
        <span>Loading comments...</span>
      </div>
    );
  }

  if (comments.length === 0) {
    return (
      <Empty className="border">
        <EmptyHeader>
          <EmptyTitle>No comments yet</EmptyTitle>
          <EmptyDescription>
            Add the first comment to start the conversation.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="flex flex-col">
      {comments.map((comment) => (
        <div key={comment.id} className="group">
          <div className="border-input bg-card rounded-md border px-3 py-2">
            <div className="flex items-center justify-between gap-3 rounded-t-md">
              <div className="flex flex-1 items-start gap-3">
                {comment.author.avatar_url && (
                  <Avatar className="size-5 rounded-full">
                    <AvatarImage src={comment.author.avatar_url || undefined} />
                  </Avatar>
                )}
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="text-foreground font-medium">
                    {comment.author.name}
                  </span>
                  <span className="text-muted-foreground">
                    {formatRelativeDatetime(comment.created_at)}
                  </span>
                  {comment.visibility === CommentVisibilityEnum.internal && (
                    <Badge variant="secondary" className="text-xs">
                      Internal
                    </Badge>
                  )}
                </div>
              </div>
              <CommentDropdown
                onDelete={() => handleDelete(comment.id)}
                isDeleting={deletingId === comment.id}
              />
            </div>
            <div className="text-foreground mt-2 whitespace-pre-wrap">
              {comment.content}
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
