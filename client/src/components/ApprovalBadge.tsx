import { Badge, makeStyles } from "@fluentui/react-components";
import type { ApprovalStatus } from "../types/tag";
import { aperamTokens } from "../theme/aperamTheme";

const approvalConfig: Record<
  Exclude<ApprovalStatus, "none">,
  { color: "warning" | "success" | "danger"; label: string }
> = {
  pending: { color: "warning", label: "Pending Approval" },
  approved: { color: "success", label: "Approved" },
  rejected: { color: "danger", label: "Rejected" },
};

const useStyles = makeStyles({
  pending: {
    backgroundColor: aperamTokens.azureSurface,
    color: aperamTokens.microsoftBlueDark,
    boxShadow: "0 0 0 1px rgba(0, 120, 212, 0.14)",
  },
});

export default function ApprovalBadge({
  approvalStatus,
}: {
  approvalStatus: ApprovalStatus | undefined;
}) {
  const styles = useStyles();
  const status = approvalStatus ?? "none";
  if (status === "none") {
    return null;
  }

  const config = approvalConfig[status];
  return (
    <Badge
      appearance="filled"
      color={config.color}
      className={status === "pending" ? styles.pending : undefined}
    >
      {config.label}
    </Badge>
  );
}
