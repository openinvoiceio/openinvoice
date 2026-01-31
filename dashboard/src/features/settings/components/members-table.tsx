import { useAccountsMembersList } from "@/api/endpoints/accounts/accounts";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useSessionSuspense } from "@/hooks/use-session";
import { formatDatetime } from "@/lib/formatters";

export function MembersTable() {
  const { user } = useSessionSuspense();
  const { data } = useAccountsMembersList(user.active_account_id);

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Role</TableHead>
          <TableHead>Joined</TableHead>
          <TableHead>
            <span className="sr-only">Actions</span>
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data?.results.map((item) => (
          <TableRow key={item.id}>
            <TableCell>{item.user.name}</TableCell>
            <TableCell>{item.user.email}</TableCell>
            <TableCell className="capitalize">{item.role}</TableCell>
            <TableCell>{formatDatetime(item.user.joined_at)}</TableCell>
            <TableCell className="flex justify-end">
              {/*TODO: add members dropdown*/}
              {/*<QuickActions*/}
              {/*  deleteAction={{*/}
              {/*    title: "User",*/}
              {/*    confirmationValue: "delete",*/}
              {/*  }}*/}
              {/*/>*/}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
