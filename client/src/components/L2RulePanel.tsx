import { useState, useEffect } from "react";
import {
  makeStyles,
  tokens,
  Field,
  Input,
  Dropdown,
  Option,
  Button,
  Accordion,
  AccordionItem,
  AccordionHeader,
  AccordionPanel,
  Spinner,
  Text,
  MessageBar,
  MessageBarBody,
  Dialog,
  DialogSurface,
  DialogBody,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
} from "@fluentui/react-components";
import {
  AddRegular,
  DeleteRegular,
  DismissRegular,
  SaveRegular,
  DataUsageRegular,
} from "@fluentui/react-icons";
import { useL2Rule } from "../hooks/useL2Rule";
import type {
  OperationalState,
  ConditionOperator,
  StateMapping,
  CreateL2Rule,
} from "../types/rule";

interface L2RulePanelProps {
  tagId: string;
}

const STATE_OPTIONS: { value: OperationalState; label: string }[] = [
  { value: "Running", label: "Running" },
  { value: "Idle", label: "Idle" },
  { value: "Stop", label: "Stop" },
];

const OPERATOR_OPTIONS: { value: ConditionOperator; label: string }[] = [
  { value: ">", label: ">" },
  { value: ">=", label: "≥" },
  { value: "<", label: "<" },
  { value: "<=", label: "≤" },
  { value: "==", label: "==" },
  { value: "!=", label: "!=" },
  { value: "between", label: "Between" },
];

interface RowState {
  state: OperationalState;
  conditionField: string;
  conditionOperator: ConditionOperator;
  conditionValue: string;
  conditionValueHigh: string; // second value for "between"
  rangeMin: string;
  rangeMax: string;
}

const EMPTY_ROW: RowState = {
  state: "Running",
  conditionField: "",
  conditionOperator: ">",
  conditionValue: "",
  conditionValueHigh: "",
  rangeMin: "",
  rangeMax: "",
};

const useStyles = makeStyles({
  panel: {
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacingVerticalM,
    paddingTop: tokens.spacingVerticalM,
    paddingBottom: tokens.spacingVerticalM,
  },
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
  actions: {
    display: "flex",
    gap: tokens.spacingHorizontalM,
    paddingTop: tokens.spacingVerticalS,
  },
  deleteButton: {
    marginLeft: "auto",
  },
  center: {
    display: "flex",
    justifyContent: "center",
    paddingTop: tokens.spacingVerticalM,
  },
  emptyText: {
    color: tokens.colorNeutralForeground3,
  },
});

function rowFromMapping(m: StateMapping): RowState {
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

function rowToMapping(r: RowState): StateMapping | null {
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

export default function L2RulePanel({ tagId }: L2RulePanelProps) {
  const styles = useStyles();
  const { rule, loading, error, refetch } = useL2Rule(tagId);

  const [rows, setRows] = useState<RowState[]>([{ ...EMPTY_ROW }]);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<{
    intent: "success" | "error";
    message: string;
  } | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [attempted, setAttempted] = useState(false);

  // Sync form with loaded rule
  useEffect(() => {
    if (rule && rule.stateMapping.length > 0) {
      setRows(rule.stateMapping.map(rowFromMapping));
      setAttempted(false);
    }
  }, [rule]);

  const updateRow = (
    index: number,
    field: keyof RowState,
    value: string,
  ) => {
    setRows((prev) =>
      prev.map((r, i) => (i === index ? { ...r, [field]: value } : r)),
    );
  };

  const addRow = () => setRows((prev) => [...prev, { ...EMPTY_ROW }]);

  const removeRow = (index: number) => {
    setRows((prev) => prev.filter((_, i) => i !== index));
  };

  const validateRows = (): StateMapping[] | null => {
    const mappings: StateMapping[] = [];
    for (const row of rows) {
      const m = rowToMapping(row);
      if (!m) return null;
      mappings.push(m);
    }
    return mappings.length > 0 ? mappings : null;
  };

  const handleSave = async () => {
    setAttempted(true);
    setFeedback(null);

    const mappings = validateRows();
    if (!mappings) {
      setFeedback({
        intent: "error",
        message:
          "All state mappings must have valid values. Ensure condition field and values are filled.",
      });
      return;
    }

    const body: CreateL2Rule = { stateMapping: mappings };

    setSaving(true);
    try {
      const res = await fetch(`/api/tags/${tagId}/rules/l2`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const errBody = await res.json().catch(() => null);
        throw new Error(
          errBody?.detail?.error ?? errBody?.detail ?? "Failed to save L2 rule",
        );
      }
      setFeedback({ intent: "success", message: "L2 rule saved." });
      refetch();
    } catch (err: unknown) {
      setFeedback({
        intent: "error",
        message: err instanceof Error ? err.message : "Failed to save L2 rule",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setDeleteOpen(false);
    setFeedback(null);
    setSaving(true);
    try {
      const res = await fetch(`/api/tags/${tagId}/rules/l2`, {
        method: "DELETE",
      });
      if (!res.ok && res.status !== 204) {
        throw new Error("Failed to delete L2 rule");
      }
      setRows([{ ...EMPTY_ROW }]);
      setAttempted(false);
      setFeedback({ intent: "success", message: "L2 rule deleted." });
      refetch();
    } catch (err: unknown) {
      setFeedback({
        intent: "error",
        message:
          err instanceof Error ? err.message : "Failed to delete L2 rule",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Accordion collapsible>
      <AccordionItem value="l2">
        <AccordionHeader icon={<DataUsageRegular />}>
          L2 — State Profiles
        </AccordionHeader>
        <AccordionPanel>
          {loading && (
            <div className={styles.center}>
              <Spinner size="small" label="Loading rule..." />
            </div>
          )}

          {error && (
            <MessageBar intent="error">
              <MessageBarBody>{error}</MessageBarBody>
            </MessageBar>
          )}

          {!loading && !error && (
            <div className={styles.panel}>
              {feedback && (
                <MessageBar intent={feedback.intent}>
                  <MessageBarBody>{feedback.message}</MessageBarBody>
                </MessageBar>
              )}

              {!rule && !attempted && (
                <Text className={styles.emptyText}>
                  No L2 rule configured. Add state mappings below to create one.
                </Text>
              )}

              {rows.map((row, index) => (
                <div key={index}>
                  {index > 0 && <Divider />}
                  <div className={styles.mappingCard}>
                    <div className={styles.mappingHeader}>
                      <Text weight="semibold">
                        State mapping {index + 1}
                      </Text>
                      {rows.length > 1 && (
                        <Button
                          appearance="subtle"
                          icon={<DismissRegular />}
                          size="small"
                          onClick={() => removeRow(index)}
                        />
                      )}
                    </div>

                    {/* Row 1: State + Condition field */}
                    <div className={styles.row}>
                      <Field className={styles.narrowField} label="State">
                        <Dropdown
                          value={
                            STATE_OPTIONS.find((o) => o.value === row.state)
                              ?.label ?? "Running"
                          }
                          selectedOptions={[row.state]}
                          onOptionSelect={(_e, data) =>
                            updateRow(
                              index,
                              "state",
                              data.optionValue ?? "Running",
                            )
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

                    {/* Row 2: Operator + Condition value(s) */}
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
                          row.conditionOperator === "between"
                            ? "Low value"
                            : "Value"
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
                              updateRow(
                                index,
                                "conditionValueHigh",
                                data.value,
                              )
                            }
                            placeholder="e.g. 1500"
                          />
                        </Field>
                      )}
                    </div>

                    {/* Row 3: Range min + Range max */}
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

              <Button
                appearance="outline"
                icon={<AddRegular />}
                onClick={addRow}
              >
                Add State Mapping
              </Button>

              <div className={styles.actions}>
                <Button
                  appearance="primary"
                  icon={<SaveRegular />}
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? "Saving..." : "Save L2 Rule"}
                </Button>
                {rule && (
                  <Button
                    className={styles.deleteButton}
                    appearance="subtle"
                    icon={<DeleteRegular />}
                    onClick={() => setDeleteOpen(true)}
                    disabled={saving}
                  >
                    Delete Rule
                  </Button>
                )}
              </div>
            </div>
          )}

          <Dialog
            open={deleteOpen}
            onOpenChange={(_e, data) => setDeleteOpen(data.open)}
          >
            <DialogSurface>
              <DialogBody>
                <DialogTitle>Delete L2 Rule</DialogTitle>
                <DialogContent>
                  Are you sure you want to delete this state profile rule? All
                  state mappings will be removed. This action cannot be undone.
                </DialogContent>
                <DialogActions>
                  <Button
                    appearance="secondary"
                    onClick={() => setDeleteOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button appearance="primary" onClick={handleDelete}>
                    Delete
                  </Button>
                </DialogActions>
              </DialogBody>
            </DialogSurface>
          </Dialog>
        </AccordionPanel>
      </AccordionItem>
    </Accordion>
  );
}
