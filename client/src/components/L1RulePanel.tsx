import { useState, useEffect } from "react";
import {
  makeStyles,
  tokens,
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
import { useSaveL1Rule, useDeleteL1Rule } from "../hooks/useSaveL1Rule";
import type { MissingDataPolicy, CreateL1Rule } from "../types/rule";
import L1RuleFields from "./L1RuleFields";
import { aperamTokens } from "../theme/aperamTheme";

interface L1RulePanelProps {
  tagId: string;
}

const useStyles = makeStyles({
  panel: {
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacingVerticalM,
    paddingTop: tokens.spacingVerticalL,
    paddingBottom: tokens.spacingVerticalL,
    paddingLeft: tokens.spacingHorizontalL,
    paddingRight: tokens.spacingHorizontalL,
    backgroundColor: aperamTokens.white,
    border: `1px solid ${aperamTokens.steel200}`,
    borderRadius: tokens.borderRadiusLarge,
    boxShadow: aperamTokens.shadowPanel,
    borderLeft: `3px solid ${aperamTokens.microsoftBlue}`,
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
  const { rule, loading, error } = useL1Rule(tagId);
  const saveL1Rule = useSaveL1Rule();
  const deleteL1Rule = useDeleteL1Rule();

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
      await saveL1Rule.mutateAsync({ tagId, data: body });
      setFeedback({ intent: "success", message: "L1 rule saved." });
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
      await deleteL1Rule.mutateAsync(tagId);
      setMin("");
      setMax("");
      setSpikeThreshold("");
      setMissingDataPolicy("alert");
      setAttempted(false);
      setFeedback({ intent: "success", message: "L1 rule deleted." });
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

              <L1RuleFields
                min={min}
                max={max}
                spikeThreshold={spikeThreshold}
                missingDataPolicy={missingDataPolicy}
                onMinChange={setMin}
                onMaxChange={setMax}
                onSpikeThresholdChange={setSpikeThreshold}
                onMissingDataPolicyChange={setMissingDataPolicy}
                attempted={attempted}
              />

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
