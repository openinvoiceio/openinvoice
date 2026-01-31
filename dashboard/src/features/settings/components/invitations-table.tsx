import { useInvitationsList } from "@/api/endpoints/invitations/invitations";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty.tsx";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export function InvitationsTable() {
  const { data } = useInvitationsList();

  if (data?.results.length === 0) {
    return (
      <Empty className="border border-dashed">
        <EmptyHeader>
          <EmptyTitle>No pending invitations</EmptyTitle>
          <EmptyDescription>
            Only active invitations are shown here.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Email</TableHead>
          <TableHead>Role</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Created</TableHead>
          <TableHead>Accepted</TableHead>
          <TableHead>
            <span className="sr-only">Actions</span>
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data?.results.map((item) => (
          <TableRow key={item.id}>
            <TableCell>{item.email}</TableCell>
            <TableCell>Owner</TableCell>
            <TableCell className="capitalize">{item.status}</TableCell>
            <TableCell>{item.created_at}</TableCell>
            <TableCell>{item.accepted_at}</TableCell>
            <TableCell>
              <div className="flex justify-end">
                {/*TODO: add invitation dropdown*/}
                {/*<QuickActions deleteAction={{ title: "Invitation" }} />*/}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
