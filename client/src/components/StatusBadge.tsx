import { Badge, makeStyles } from "@fluentui/react-components";
import type { TagStatus } from "../types/tag";
import { aperamTokens } from "../theme/aperamTheme";

const statusConfig: Record<TagStatus, { color: "success" | "warning" | "informative"; label: string }> = {
  active: { color: "success", label: "Active" },
  draft: { color: "warning", label: "Draft" },
  retired: { color: "informative", label: "Retired" },
};

const useStyles = makeStyles({
  active: {
    backgroundColor: aperamTokens.microsoftBlue,
    color: aperamTokens.white,
    boxShadow: "0 0 0 1px rgba(0, 120, 212, 0.12)",
  },
});

export default function StatusBadge({ status }: { status: TagStatus }) {
  const styles = useStyles();
  const config = statusConfig[status];
  return (
    <Badge
      appearance="filled"
      color={config.color}
      className={status === "active" ? styles.active : undefined}
    >
      {config.label}
    </Badge>
  );
}
