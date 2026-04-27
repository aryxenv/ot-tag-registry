import { Badge, makeStyles } from "@fluentui/react-components";
import type { TagStatus } from "../types/tag";
import { aperamTokens } from "../theme/aperamTheme";

const statusConfig: Record<
  TagStatus,
  {
    appearance: "outline" | "tint";
    color: "informative" | "subtle" | "warning";
    label: string;
  }
> = {
  active: { appearance: "tint", color: "informative", label: "Active" },
  draft: { appearance: "tint", color: "warning", label: "Draft" },
  retired: { appearance: "outline", color: "subtle", label: "Retired" },
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

export default function StatusBadge({ status }: { status: TagStatus }) {
  const styles = useStyles();
  const config = statusConfig[status];
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
