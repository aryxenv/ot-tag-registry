import { Badge } from "@fluentui/react-components";
import type { TagStatus } from "../types/tag";

const statusConfig: Record<TagStatus, { color: "success" | "warning" | "informative"; label: string }> = {
  active: { color: "success", label: "Active" },
  draft: { color: "warning", label: "Draft" },
  retired: { color: "informative", label: "Retired" },
};

export default function StatusBadge({ status }: { status: TagStatus }) {
  const config = statusConfig[status];
  return (
    <Badge appearance="filled" color={config.color}>
      {config.label}
    </Badge>
  );
}
