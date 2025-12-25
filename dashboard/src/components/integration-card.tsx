import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar.tsx";
import { Button } from "@/components/ui/button.tsx";

export function IntegrationCard({
  name,
  url,
  description,
  connected,
  onClick,
}: {
  name: string;
  url: string;
  description?: string;
  connected?: boolean;
  onClick?: () => void;
}) {
  return (
    <Button
      className="flex h-fit flex-col items-start gap-2 p-3 text-start"
      variant="outline"
      onClick={onClick}
    >
      <div className="flex items-center gap-2 text-sm">
        <Avatar className="size-9 rounded-md">
          <AvatarImage src={url} />
          <AvatarFallback>Stripe</AvatarFallback>
        </Avatar>
        <div className="flex flex-col">
          <div>{name}</div>
          {connected && (
            <div className="text-muted-foreground text-xs">Connected</div>
          )}
        </div>
      </div>
      {description && (
        <div className="text-muted-foreground text-sm font-normal text-wrap">
          {description}
        </div>
      )}
    </Button>
  );
}
