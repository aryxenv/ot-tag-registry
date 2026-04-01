import {
  makeStyles,
  tokens,
  Field,
  Input,
  Dropdown,
  Option,
  Button,
  Text,
  Divider,
} from "@fluentui/react-components";
import { AddRegular, DismissRegular } from "@fluentui/react-icons";
import type { OperationalState, ConditionOperator, StateMapping } from "../types/rule";

/* eslint-disable react-refresh/only-export-components */

export const STATE_OPTIONS: { value: OperationalState; label: string }[] = [
  { value: "Running", label: "Running" },
  { value: "Idle", label: "Idle" },
  { value: "Stop", label: "Stop" },
];

export const OPERATOR_OPTIONS: { value: ConditionOperator; label: string }[] = [
  { value: ">", label: ">" },
  { value: ">=", label: "≥" },
  { value: "<", label: "<" },
  { value: "<=", label: "≤" },
  { value: "==", label: "==" },
  { value: "!=", label: "!=" },
  { value: "between", label: "Between" },
];

export interface RowState {
  state: OperationalState;
  conditionField: string;
  conditionOperator: ConditionOperator;
  conditionValue: string;
  conditionValueHigh: string;
  rangeMin: string;
  rangeMax: string;
}

export const EMPTY_ROW: RowState = {
  state: "Running",
  conditionField: "",
  conditionOperator: ">",
  conditionValue: "",
  conditionValueHigh: "",
  rangeMin: "",
  rangeMax: "",
};

export function rowFromMapping(m: StateMapping): RowState {
  const isBetween = m.conditionOperator === "between";
  return {
    state: m.state,
    conditionField: m.conditionField,
    conditionOperator: m.conditionOperator,
    conditionValue: isBetween
      ? String((m.conditionValue as [number, number])[0])
      : String(m.conditionValue),
    conditionValueHigh: isBetween
      ? String((m.conditionValue as [number, number])[1])
      : "",
    rangeMin: m.rangeMin != null ? String(m.rangeMin) : "",
    rangeMax: m.rangeMax != null ? String(m.rangeMax) : "",
  };
}

export function rowToMapping(r: RowState): StateMapping | null {
  if (!r.conditionField.trim()) return null;
  const val = Number(r.conditionValue);
  if (isNaN(val) && r.conditionOperator !== "between") return null;

  let conditionValue: number | [number, number];
  if (r.conditionOperator === "between") {
    const low = Number(r.conditionValue);
    const high = Number(r.conditionValueHigh);
    if (isNaN(low) || isNaN(high)) return null;
    conditionValue = [low, high];
  } else {
    conditionValue = val;
  }

  return {
    state: r.state,
    conditionField: r.conditionField.trim(),
    conditionOperator: r.conditionOperator,
    conditionValue,
    rangeMin: r.rangeMin.trim() !== "" ? Number(r.rangeMin) : null,
    rangeMax: r.rangeMax.trim() !== "" ? Number(r.rangeMax) : null,
  };
}

export interface L2RuleFieldsProps {
  rows: RowState[];
  onRowsChange: (rows: RowState[]) => void;
  attempted?: boolean;
}

const useStyles = makeStyles({
  mappingCard: {
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacingVerticalS,
    padding: tokens.spacingHorizontalM,
    borderRadius: tokens.borderRadiusMedium,
    backgroundColor: tokens.colorNeutralBackground2,
  },
  mappingHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  row: {
    display: "flex",
    gap: tokens.spacingHorizontalM,
  },
  field: {
    flex: 1,
    minWidth: 0,
  },
  narrowField: {
    flex: 0,
    minWidth: "120px",
  },
});

export default function L2RuleFields({
  rows,
  onRowsChange,
  attempted,
}: L2RuleFieldsProps) {
  const styles = useStyles();

  const updateRow = (index: number, field: keyof RowState, value: string) => {
    onRowsChange(
      rows.map((r, i) => (i === index ? { ...r, [field]: value } : r)),
    );
  };

  const addRow = () => onRowsChange([...rows, { ...EMPTY_ROW }]);

  const removeRow = (index: number) => {
    onRowsChange(rows.filter((_, i) => i !== index));
  };

  return (
    <>
      {rows.map((row, index) => (
        <div key={index}>
          {index > 0 && <Divider />}
          <div className={styles.mappingCard}>
            <div className={styles.mappingHeader}>
              <Text weight="semibold">State mapping {index + 1}</Text>
              {rows.length > 1 && (
                <Button
                  appearance="subtle"
                  icon={<DismissRegular />}
                  size="small"
                  onClick={() => removeRow(index)}
                />
              )}
            </div>

            <div className={styles.row}>
              <Field className={styles.narrowField} label="State">
                <Dropdown
                  value={
                    STATE_OPTIONS.find((o) => o.value === row.state)?.label ??
                    "Running"
                  }
                  selectedOptions={[row.state]}
                  onOptionSelect={(_e, data) =>
                    updateRow(index, "state", data.optionValue ?? "Running")
                  }
                >
                  {STATE_OPTIONS.map((opt) => (
                    <Option key={opt.value} value={opt.value}>
                      {opt.label}
                    </Option>
                  ))}
                </Dropdown>
              </Field>
              <Field
                className={styles.field}
                label="Condition field"
                validationState={
                  attempted && !row.conditionField.trim()
                    ? "error"
                    : undefined
                }
                validationMessage={
                  attempted && !row.conditionField.trim()
                    ? "Required"
                    : undefined
                }
              >
                <Input
                  value={row.conditionField}
                  onChange={(_e, data) =>
                    updateRow(index, "conditionField", data.value)
                  }
                  placeholder="e.g. SpindleSpeed"
                />
              </Field>
            </div>

            <div className={styles.row}>
              <Field className={styles.narrowField} label="Operator">
                <Dropdown
                  value={
                    OPERATOR_OPTIONS.find(
                      (o) => o.value === row.conditionOperator,
                    )?.label ?? ">"
                  }
                  selectedOptions={[row.conditionOperator]}
                  onOptionSelect={(_e, data) =>
                    updateRow(
                      index,
                      "conditionOperator",
                      data.optionValue ?? ">",
                    )
                  }
                >
                  {OPERATOR_OPTIONS.map((opt) => (
                    <Option key={opt.value} value={opt.value}>
                      {opt.label}
                    </Option>
                  ))}
                </Dropdown>
              </Field>
              <Field
                className={styles.field}
                label={
                  row.conditionOperator === "between" ? "Low value" : "Value"
                }
                validationState={
                  attempted && !row.conditionValue.trim()
                    ? "error"
                    : undefined
                }
                validationMessage={
                  attempted && !row.conditionValue.trim()
                    ? "Required"
                    : undefined
                }
              >
                <Input
                  type="number"
                  value={row.conditionValue}
                  onChange={(_e, data) =>
                    updateRow(index, "conditionValue", data.value)
                  }
                  placeholder="e.g. 500"
                />
              </Field>
              {row.conditionOperator === "between" && (
                <Field
                  className={styles.field}
                  label="High value"
                  validationState={
                    attempted && !row.conditionValueHigh.trim()
                      ? "error"
                      : undefined
                  }
                  validationMessage={
                    attempted && !row.conditionValueHigh.trim()
                      ? "Required"
                      : undefined
                  }
                >
                  <Input
                    type="number"
                    value={row.conditionValueHigh}
                    onChange={(_e, data) =>
                      updateRow(index, "conditionValueHigh", data.value)
                    }
                    placeholder="e.g. 1500"
                  />
                </Field>
              )}
            </div>

            <div className={styles.row}>
              <Field className={styles.field} label="Range min">
                <Input
                  type="number"
                  value={row.rangeMin}
                  onChange={(_e, data) =>
                    updateRow(index, "rangeMin", data.value)
                  }
                  placeholder="Expected min"
                />
              </Field>
              <Field className={styles.field} label="Range max">
                <Input
                  type="number"
                  value={row.rangeMax}
                  onChange={(_e, data) =>
                    updateRow(index, "rangeMax", data.value)
                  }
                  placeholder="Expected max"
                />
              </Field>
            </div>
          </div>
        </div>
      ))}

      <Button appearance="outline" icon={<AddRegular />} onClick={addRow}>
        Add State Mapping
      </Button>
    </>
  );
}
