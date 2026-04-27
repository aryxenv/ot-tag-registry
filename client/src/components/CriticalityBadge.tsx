import { Badge, makeStyles } from "@fluentui/react-components";
import type { Criticality } from "../types/tag";
import { aperamTokens } from "../theme/aperamTheme";

const criticalityConfig: Record<
  Criticality,
  { appearance: "filled" | "tint"; color: "danger" | "severe" | "warning" | "informative"; label: string }
> = {
  critical: { appearance: "filled", color: "danger", label: "Critical" },
  high: { appearance: "filled", color: "severe", label: "High" },
  medium: { appearance: "filled", color: "warning", label: "Medium" },
  low: { appearance: "tint", color: "informative", label: "Low" },
};

const useStyles = makeStyles({
  critical: {
    backgroundColor: aperamTokens.orange500,
    color: aperamTokens.white,
    boxShadow: "0 0 0 1px rgba(241, 81, 27, 0.15), 0 4px 10px -6px rgba(241, 81, 27, 0.6)",
    fontWeight: 600,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
    fontSize: "10px",
  },
});

export default function CriticalityBadge({ criticality }: { criticality: Criticality }) {
  const styles = useStyles();
  const config = criticalityConfig[criticality];
  if (criticality === "critical") {
    return (
      <Badge appearance="filled" color="danger" className={styles.critical}>
        {config.label}
      </Badge>
    );
  }
  return (
    <Badge appearance={config.appearance} color={config.color}>
      {config.label}
    </Badge>
  );
}
