export type SystemType = "PLC" | "SCADA" | "Historian" | "Other";

export interface Source {
  id: string;
  systemType: SystemType;
  connectorType: string;
  topicOrPath: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}
