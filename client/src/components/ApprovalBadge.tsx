import { Badge } from "@fluentui/react-components";
import type { ApprovalStatus } from "../types/tag";

const approvalConfig: Record<
  Exclude<ApprovalStatus, "none">,
  { color: "warning" | "success" | "danger"; label: string }
> = {
  pending: { color: "warning", label: "Pending Approval" },
  approved: { color: "success", label: "Approved" },
  rejected: { color: "danger", label: "Rejected" },
};

export default function ApprovalBadge({
  approvalStatus,
}: {
  approvalStatus: ApprovalStatus | undefined;
}) {
  const status = approvalStatus ?? "none";
  if (status === "none") {
    return null;
  }

  const config = approvalConfig[status];
  return (
    <Badge appearance="filled" color={config.color}>
      {config.label}
    </Badge>
  );
}
