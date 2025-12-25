import {
  getNumberingSystemsListQueryKey,
  useNumberingSystemsList,
} from "@/api/endpoints/numbering-systems/numbering-systems";
import { NumberingSystemAppliesToEnum, type Account } from "@/api/models";
import { pushModal } from "@/components/push-modals";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty.tsx";
import {
  FormCard,
  FormCardContent,
  FormCardDescription,
  FormCardFooter,
  FormCardFooterInfo,
  FormCardHeader,
  FormCardTitle,
  FormCardUpgrade,
} from "@/components/ui/form-card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { formatEnum } from "@/lib/formatters.ts";
import { useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { LockIcon } from "lucide-react";
import { useState } from "react";

const tabs = Object.entries(NumberingSystemAppliesToEnum).map(([, value]) => ({
  value,
  label: `${formatEnum(value)}s`,
}));

export function AccountNumberingSystemsCard({ account }: { account: Account }) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<NumberingSystemAppliesToEnum>(
    NumberingSystemAppliesToEnum.invoice,
  );
  const { data } = useNumberingSystemsList({
    applies_to: activeTab,
    ordering: "-created_at",
    page_size: 20,
  });
  const isLocked = !account.subscription;

  const numberingSystems = data?.results ?? [];

  const defaultNumberingSystemId =
    activeTab === NumberingSystemAppliesToEnum.invoice
      ? account.invoice_numbering_system_id
      : account.credit_note_numbering_system_id;

  return (
    <FormCard>
      {isLocked && <FormCardUpgrade />}
      <FormCardHeader>
        <FormCardTitle>Numbering systems</FormCardTitle>
        <FormCardDescription>
          Manage automatic numbering formats for your invoices and credit notes.
        </FormCardDescription>
      </FormCardHeader>
      <FormCardContent>
        <Tabs
          value={activeTab}
          onValueChange={(value) =>
            setActiveTab(value as NumberingSystemAppliesToEnum)
          }
        >
          <TabsList>
            {tabs.map((tab) => (
              <TabsTrigger key={tab.value} value={tab.value}>
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>
          <TabsContent value={activeTab} className="mt-4">
            {numberingSystems.length > 0 ? (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Template</TableHead>
                      <TableHead>Reset interval</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {numberingSystems.map((system) => (
                      <TableRow key={system.id}>
                        <TableCell className="space-x-2 font-medium">
                          <span>{system.description || "Untitled"}</span>
                          {system.id === defaultNumberingSystemId && (
                            <Badge variant="secondary">Default</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <code>{system.template}</code>
                        </TableCell>
                        <TableCell className="capitalize">
                          {system.reset_interval}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <Empty className="border border-dashed">
                <EmptyHeader>
                  <EmptyTitle>No numbering systems</EmptyTitle>
                  <EmptyDescription>
                    You have not added any numbering systems for this document.
                  </EmptyDescription>
                </EmptyHeader>
              </Empty>
            )}
          </TabsContent>
        </Tabs>
      </FormCardContent>
      <FormCardFooter>
        {isLocked ? (
          <>
            <FormCardFooterInfo>
              This feature is available on the{" "}
              <Link to="/settings/billing" className="font-medium">
                Standard plan
              </Link>
              .
            </FormCardFooterInfo>
            <Button type="button" asChild>
              <Link to="/settings/billing">
                <LockIcon />
                Upgrade
              </Link>
            </Button>
          </>
        ) : (
          <Button
            type="button"
            onClick={() =>
              pushModal("NumberingSystemCreateSheet", {
                appliesTo: activeTab,
                onSuccess: async () => {
                  await queryClient.invalidateQueries({
                    queryKey: getNumberingSystemsListQueryKey(),
                  });
                },
              })
            }
          >
            Add
          </Button>
        )}
      </FormCardFooter>
    </FormCard>
  );
}
