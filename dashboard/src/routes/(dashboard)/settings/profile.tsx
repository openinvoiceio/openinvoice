import { useListSessions } from "@/api/endpoints/sessions/sessions";
import { ProfileGeneralCard } from "@/components/profile-general-card";
import { ProfilePasswordCard } from "@/components/profile-password-card";
import { Badge } from "@/components/ui/badge";
import {
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardGroup,
  FormCardHeader,
  FormCardTitle,
} from "@/components/ui/form-card";
import {
  Section,
  SectionGroup,
  SectionHeader,
  SectionTitle,
} from "@/components/ui/section";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDatetime } from "@/lib/formatters";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/(dashboard)/settings/profile")({
  component: RouteComponent,
});

function RouteComponent() {
  const { auth } = Route.useRouteContext();
  const { data: sessions } = useListSessions("browser");

  if (!auth) return null;

  return (
    <SectionGroup>
      <Section>
        <SectionHeader>
          <SectionTitle>Profile</SectionTitle>
        </SectionHeader>
        <FormCardGroup>
          <ProfileGeneralCard user={auth.user} />
          <ProfilePasswordCard
            hasUsablePassword={auth.user.has_usable_password}
          />
          <FormCard>
            <FormCardHeader>
              <FormCardTitle>Active sessions</FormCardTitle>
              <FormCardDescription>
                Manage your active sessions. You can end any session to log out
                from that device.
              </FormCardDescription>
            </FormCardHeader>
            <FormCardContent className="pb-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>IP</TableHead>
                    <TableHead className="max-w-60">User agent</TableHead>
                    <TableHead>Last seen</TableHead>
                    <TableHead>
                      <span className="sr-only">Actions</span>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sessions?.data.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <div className="flex gap-2">
                          <div>{item.ip}</div>
                          {item.is_current && <Badge>Current</Badge>}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-60 whitespace-break-spaces">
                        {item.user_agent}
                      </TableCell>
                      <TableCell>
                        {item.last_seen_at
                          ? formatDatetime(item.last_seen_at)
                          : "-"}
                      </TableCell>
                      <TableCell>
                        <div className="flex justify-end"></div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </FormCardContent>
          </FormCard>
        </FormCardGroup>
      </Section>
    </SectionGroup>
  );
}
