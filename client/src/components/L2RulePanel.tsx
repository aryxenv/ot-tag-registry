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
  DataUsageRegular,
} from "@fluentui/react-icons";
import { useL2Rule } from "../hooks/useL2Rule";
import { useSaveL2Rule, useDeleteL2Rule } from "../hooks/useSaveL2Rule";
import type { CreateL2Rule, StateMapping } from "../types/rule";
import L2RuleFields, {
  type RowState,
  EMPTY_ROW,
  rowFromMapping,
  rowToMapping,
} from "./L2RuleFields";
import { aperamTokens } from "../theme/aperamTheme";

interface L2RulePanelProps {
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
    borderLeft: `3px solid ${aperamTokens.azureCyan}`,
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

export default function L2RulePanel({ tagId }: L2RulePanelProps) {
  const styles = useStyles();
  const { rule, loading, error } = useL2Rule(tagId);
  const saveL2Rule = useSaveL2Rule();
  const deleteL2Rule = useDeleteL2Rule();

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
      await saveL2Rule.mutateAsync({ tagId, data: body });
      setFeedback({ intent: "success", message: "L2 rule saved." });
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
      await deleteL2Rule.mutateAsync(tagId);
      setRows([{ ...EMPTY_ROW }]);
      setAttempted(false);
      setFeedback({ intent: "success", message: "L2 rule deleted." });
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

              <L2RuleFields
                rows={rows}
                onRowsChange={setRows}
                attempted={attempted}
              />

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
