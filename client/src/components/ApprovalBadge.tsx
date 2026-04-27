import { Badge, makeStyles } from "@fluentui/react-components";
import type { ApprovalStatus } from "../types/tag";
import { aperamTokens } from "../theme/aperamTheme";

const approvalConfig: Record<
  Exclude<ApprovalStatus, "none">,
  {
    appearance: "tint";
    color: "danger" | "success" | "warning";
    label: string;
  }
> = {
  pending: { appearance: "tint", color: "warning", label: "Pending" },
  approved: { appearance: "tint", color: "success", label: "Approved" },
  rejected: { appearance: "tint", color: "danger", label: "Rejected" },
};

const useStyles = makeStyles({
  badge: {
    height: "22px",
    minWidth: "auto",
    paddingRight: "9px",
    paddingLeft: "9px",
    fontFamily: aperamTokens.displayFont,
    fontSize: "11px",
    fontWeight: 600,
    letterSpacing: "0.01em",
    boxShadow: "none",
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
      appearance={config.appearance}
      color={config.color}
      shape="rounded"
      size="small"
      className={styles.badge}
    >
      {config.label}
    </Badge>
  );
}
