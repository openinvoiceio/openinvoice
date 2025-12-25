import type { Tag } from "emblor";
import { z } from "zod";

export const recipientTagStyleClasses = {
  inlineTagsContainer:
    "border border-input rounded-md dark:bg-input/30 bg-transparent shadow-xs focus-within:ring-ring/50 focus-within:border-ring focus-within:ring-[3px] p-1 gap-1 transition-[color,box-shadow]",
  input: "px-2 h-7",
  tag: {
    body: "h-7 relative dark:bg-input/30 border border-input rounded-md font-medium text-xs ps-2 pe-7",
    closeButton:
      "absolute -inset-y-px -end-px p-0 rounded-e-lg flex size-7 transition-colors outline-0 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring text-muted-foreground hover:text-foreground",
  },
} as const;

const recipientEmailSchema = z.string().email();

export const recipientTagSchema = z.object({
  id: z.string(),
  text: recipientEmailSchema,
});

export type RecipientTag = z.infer<typeof recipientTagSchema>;

export function validateRecipientTag(tag: string) {
  return recipientEmailSchema.safeParse(tag).success;
}

export function emailsToRecipientTags(emails: string[]): RecipientTag[] {
  return emails.map((email) => ({ id: email, text: email }));
}

export function recipientTagsToEmails(tags: Tag[]): string[] {
  return tags.map(({ text }) => text);
}
