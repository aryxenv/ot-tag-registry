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
} from "@fluentui/react-components";
import {
  DeleteRegular,
  SaveRegular,
  ShieldCheckmarkRegular,
} from "@fluentui/react-icons";
import { useL1Rule } from "../hooks/useL1Rule";
import type { MissingDataPolicy, CreateL1Rule } from "../types/rule";

interface L1RulePanelProps {
  tagId: string;
}

const MISSING_DATA_OPTIONS: { value: MissingDataPolicy; label: string }[] = [
  { value: "alert", label: "Alert" },
  { value: "ignore", label: "Ignore" },
  { value: "interpolate", label: "Interpolate" },
  { value: "last-known", label: "Last Known" },
];

const useStyles = makeStyles({
  panel: {
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacingVerticalM,
    paddingTop: tokens.spacingVerticalM,
    paddingBottom: tokens.spacingVerticalM,
  },
  row: {
    display: "flex",
    gap: tokens.spacingHorizontalL,
  },
  halfField: {
    flex: 1,
    minWidth: 0,
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

export default function L1RulePanel({ tagId }: L1RulePanelProps) {
  const styles = useStyles();
  const { rule, loading, error, refetch } = useL1Rule(tagId);

  const [min, setMin] = useState("");
  const [max, setMax] = useState("");
  const [spikeThreshold, setSpikeThreshold] = useState("");
  const [missingDataPolicy, setMissingDataPolicy] =
    useState<MissingDataPolicy>("alert");

  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<{
    intent: "success" | "error";
    message: string;
  } | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [attempted, setAttempted] = useState(false);

  // Sync form with loaded rule
  useEffect(() => {
    if (rule) {
      setMin(rule.min != null ? String(rule.min) : "");
      setMax(rule.max != null ? String(rule.max) : "");
      setSpikeThreshold(
        rule.spikeThreshold != null ? String(rule.spikeThreshold) : "",
      );
      setMissingDataPolicy(rule.missingDataPolicy);
      setAttempted(false);
    }
  }, [rule]);

  const parseNum = (v: string): number | null => {
    const trimmed = v.trim();
    if (trimmed === "") return null;
    const n = Number(trimmed);
    return isNaN(n) ? null : n;
  };

  const hasAtLeastOneThreshold =
    min.trim() !== "" || max.trim() !== "" || spikeThreshold.trim() !== "";

  const handleSave = async () => {
    setAttempted(true);
    setFeedback(null);

    if (!hasAtLeastOneThreshold) {
      setFeedback({
        intent: "error",
        message: "At least one of min, max, or spike threshold must be set.",
      });
      return;
    }

    const body: CreateL1Rule = {
      missingDataPolicy,
    };
    const parsedMin = parseNum(min);
    const parsedMax = parseNum(max);
    const parsedSpike = parseNum(spikeThreshold);

    if (parsedMin != null) body.min = parsedMin;
    if (parsedMax != null) body.max = parsedMax;
    if (parsedSpike != null) body.spikeThreshold = parsedSpike;

    setSaving(true);
    try {
      const res = await fetch(`/api/tags/${tagId}/rules/l1`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const errBody = await res.json().catch(() => null);
        throw new Error(
          errBody?.detail?.error ?? errBody?.detail ?? "Failed to save L1 rule",
        );
      }
      setFeedback({ intent: "success", message: "L1 rule saved." });
      refetch();
    } catch (err: unknown) {
      setFeedback({
        intent: "error",
        message: err instanceof Error ? err.message : "Failed to save L1 rule",
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
      const res = await fetch(`/api/tags/${tagId}/rules/l1`, {
        method: "DELETE",
      });
      if (!res.ok && res.status !== 204) {
        throw new Error("Failed to delete L1 rule");
      }
      setMin("");
      setMax("");
      setSpikeThreshold("");
      setMissingDataPolicy("alert");
      setAttempted(false);
      setFeedback({ intent: "success", message: "L1 rule deleted." });
      refetch();
    } catch (err: unknown) {
      setFeedback({
        intent: "error",
        message:
          err instanceof Error ? err.message : "Failed to delete L1 rule",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Accordion collapsible>
      <AccordionItem value="l1">
        <AccordionHeader icon={<ShieldCheckmarkRegular />}>
          L1 — Range Rules
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
                  No L1 rule configured. Fill in values below to create one.
                </Text>
              )}

              <div className={styles.row}>
                <Field
                  className={styles.halfField}
                  label="Min value"
                  validationState={
                    attempted && !hasAtLeastOneThreshold ? "error" : undefined
                  }
                >
                  <Input
                    type="number"
                    value={min}
                    onChange={(_e, data) => setMin(data.value)}
                    placeholder="e.g. 0"
                  />
                </Field>
                <Field
                  className={styles.halfField}
                  label="Max value"
                  validationState={
                    attempted && !hasAtLeastOneThreshold ? "error" : undefined
                  }
                >
                  <Input
                    type="number"
                    value={max}
                    onChange={(_e, data) => setMax(data.value)}
                    placeholder="e.g. 100"
                  />
                </Field>
              </div>

              <div className={styles.row}>
                <Field
                  className={styles.halfField}
                  label="Spike threshold"
                  validationState={
                    attempted && !hasAtLeastOneThreshold ? "error" : undefined
                  }
                  validationMessage={
                    attempted && !hasAtLeastOneThreshold
                      ? "Set at least one threshold"
                      : undefined
                  }
                >
                  <Input
                    type="number"
                    value={spikeThreshold}
                    onChange={(_e, data) => setSpikeThreshold(data.value)}
                    placeholder="e.g. 10"
                  />
                </Field>
                <Field
                  className={styles.halfField}
                  label="Missing data policy"
                >
                  <Dropdown
                    value={
                      MISSING_DATA_OPTIONS.find(
                        (o) => o.value === missingDataPolicy,
                      )?.label ?? "Alert"
                    }
                    selectedOptions={[missingDataPolicy]}
                    onOptionSelect={(_e, data) =>
                      setMissingDataPolicy(
                        (data.optionValue as MissingDataPolicy) ?? "alert",
                      )
                    }
                  >
                    {MISSING_DATA_OPTIONS.map((opt) => (
                      <Option key={opt.value} value={opt.value}>
                        {opt.label}
                      </Option>
                    ))}
                  </Dropdown>
                </Field>
              </div>

              <div className={styles.actions}>
                <Button
                  appearance="primary"
                  icon={<SaveRegular />}
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? "Saving..." : "Save L1 Rule"}
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
                <DialogTitle>Delete L1 Rule</DialogTitle>
                <DialogContent>
                  Are you sure you want to delete this range rule? This action
                  cannot be undone.
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
