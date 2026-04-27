import { Badge, makeStyles } from "@fluentui/react-components";
import type { Criticality } from "../types/tag";
import { aperamTokens } from "../theme/aperamTheme";

const criticalityConfig: Record<
  Criticality,
  {
    appearance: "outline" | "tint";
    color: "danger" | "severe" | "subtle" | "warning";
    label: string;
  }
> = {
  critical: { appearance: "tint", color: "danger", label: "Critical" },
  high: { appearance: "tint", color: "severe", label: "High" },
  medium: { appearance: "tint", color: "warning", label: "Medium" },
  low: { appearance: "outline", color: "subtle", label: "Low" },
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
    textTransform: "none",
  },
});

export default function CriticalityBadge({ criticality }: { criticality: Criticality }) {
  const styles = useStyles();
  const config = criticalityConfig[criticality];
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
