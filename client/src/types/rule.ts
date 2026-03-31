export type MissingDataPolicy = "ignore" | "alert" | "interpolate" | "last-known";

export type OperationalState = "Running" | "Idle" | "Stop";

export type ConditionOperator = ">" | ">=" | "<" | "<=" | "==" | "!=" | "between";

export interface L1Rule {
  id: string;
  tagId: string;
  min: number | null;
  max: number | null;
  missingDataPolicy: MissingDataPolicy;
  spikeThreshold: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface CreateL1Rule {
  min?: number | null;
  max?: number | null;
  missingDataPolicy?: MissingDataPolicy;
  spikeThreshold?: number | null;
}

export interface StateMapping {
  state: OperationalState;
  conditionField: string;
  conditionOperator: ConditionOperator;
  conditionValue: number | [number, number];
  rangeMin: number | null;
  rangeMax: number | null;
}

export interface L2Rule {
  id: string;
  tagId: string;
  stateMapping: StateMapping[];
  createdAt: string;
  updatedAt: string;
}

export interface CreateL2Rule {
  stateMapping: StateMapping[];
}
