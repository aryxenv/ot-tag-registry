import { Badge } from "@fluentui/react-components";
import type { Criticality } from "../types/tag";

const criticalityConfig: Record<
  Criticality,
  { appearance: "filled" | "tint"; color: "danger" | "severe" | "warning" | "informative"; label: string }
> = {
  critical: { appearance: "filled", color: "danger", label: "Critical" },
  high: { appearance: "filled", color: "severe", label: "High" },
  medium: { appearance: "filled", color: "warning", label: "Medium" },
  low: { appearance: "tint", color: "informative", label: "Low" },
};

export default function CriticalityBadge({ criticality }: { criticality: Criticality }) {
  const config = criticalityConfig[criticality];
  return (
    <Badge appearance={config.appearance} color={config.color}>
      {config.label}
    </Badge>
  );
}
