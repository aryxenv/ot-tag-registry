import { useState } from "react";
import {
  makeStyles,
  tokens,
  OverlayDrawer,
  DrawerHeader,
  DrawerHeaderTitle,
  DrawerBody,
  Field,
  Textarea,
  Button,
  Spinner,
  Text,
  Caption1,
  Card,
  CardHeader,
  Divider,
} from "@fluentui/react-components";
import {
  DismissRegular,
  SparkleRegular,
  TranslateRegular,
  CheckmarkCircleRegular,
  ErrorCircleRegular,
  SubtractCircleRegular,
  ArrowRightRegular,
} from "@fluentui/react-icons";
import { Link } from "react-router-dom";
import { translateText } from "../api/mutations";
import { useAgentCreateTag, type StepStatus } from "../hooks/useAgentCreateTag";

export interface AgentPanelProps {
  open: boolean;
  onClose: () => void;
}

const useStyles = makeStyles({
  body: {
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacingVerticalL,
  },
  inputRow: {
    display: "flex",
    gap: tokens.spacingHorizontalS,
    alignItems: "flex-end",
  },
  inputField: {
    flex: 1,
    minWidth: 0,
  },
  buttonColumn: {
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacingVerticalXS,
  },
  stepsList: {
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacingVerticalS,
  },
  stepRow: {
    display: "flex",
    alignItems: "flex-start",
    gap: tokens.spacingHorizontalS,
  },
  stepIcon: {
    flexShrink: 0,
    marginTop: "2px",
  },
  stepContent: {
    display: "flex",
    flexDirection: "column",
    minWidth: 0,
  },
  approvalCard: {
    marginTop: tokens.spacingVerticalS,
    marginBottom: tokens.spacingVerticalS,
  },
  approvalGrid: {
    display: "grid",
    gridTemplateColumns: "auto 1fr",
    gap: `${tokens.spacingVerticalXS} ${tokens.spacingHorizontalM}`,
    paddingTop: tokens.spacingVerticalS,
    paddingBottom: tokens.spacingVerticalS,
  },
  approvalLabel: {
    fontWeight: tokens.fontWeightSemibold,
    whiteSpace: "nowrap",
  },
  approvalActions: {
    display: "flex",
    gap: tokens.spacingHorizontalS,
    paddingTop: tokens.spacingVerticalS,
  },
  resultCard: {
    marginTop: tokens.spacingVerticalS,
  },
  resultLink: {
    display: "inline-flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalXS,
    marginTop: tokens.spacingVerticalXS,
  },
});

function StepIcon({ status }: { status: StepStatus }) {
  switch (status) {
    case "running":
      return <Spinner size="tiny" />;
    case "done":
      return <CheckmarkCircleRegular primaryFill={tokens.colorPaletteGreenForeground1} />;
    case "error":
      return <ErrorCircleRegular primaryFill={tokens.colorPaletteRedForeground1} />;
    case "skipped":
      return <SubtractCircleRegular primaryFill={tokens.colorNeutralForeground3} />;
    case "awaiting-approval":
      return <Spinner size="tiny" />;
    default:
      return <SubtractCircleRegular primaryFill={tokens.colorNeutralForeground4} />;
  }
}

export default function AgentPanel({ open, onClose }: AgentPanelProps) {
  const styles = useStyles();
  const [query, setQuery] = useState("");
  const [translating, setTranslating] = useState(false);
  const agent = useAgentCreateTag();

  const handleClose = () => {
    agent.reset();
    setQuery("");
    onClose();
  };

  const handleRun = () => {
    if (!query.trim() || agent.running) return;
    agent.run(query.trim());
  };

  const handleTranslate = async () => {
    if (!query.trim() || translating) return;
    setTranslating(true);
    try {
      const result = await translateText(query.trim());
      if (result.wasTranslated) {
        setQuery(result.text);
      }
    } catch {
      // Non-critical — user can still proceed
    } finally {
      setTranslating(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleRun();
    }
  };

  return (
    <OverlayDrawer
      open={open}
      onOpenChange={(_e, data) => { if (!data.open) handleClose(); }}
      position="end"
      size="medium"
    >
      <DrawerHeader>
        <DrawerHeaderTitle
          action={
            <Button
              appearance="subtle"
              icon={<DismissRegular />}
              onClick={handleClose}
              aria-label="Close"
            />
          }
        >
          AI Agent
        </DrawerHeaderTitle>
      </DrawerHeader>

      <DrawerBody className={styles.body}>
        {/* Input section */}
        <div className={styles.inputRow}>
          <Field className={styles.inputField} label="Describe the tag you want to create">
            <Textarea
              value={query}
              onChange={(_e, data) => setQuery(data.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g. outlet pressure sensor on the main cooling pump in Luxembourg Line 1"
              rows={3}
              resize="vertical"
              disabled={agent.running || translating}
            />
          </Field>
          <div className={styles.buttonColumn}>
            <Button
              appearance="subtle"
              icon={translating ? <Spinner size="tiny" /> : <TranslateRegular />}
              onClick={handleTranslate}
              disabled={translating || agent.running || !query.trim()}
              title="Translate to English"
            >
              Translate
            </Button>
            <Button
              appearance="primary"
              icon={agent.running ? <Spinner size="tiny" /> : <SparkleRegular />}
              onClick={handleRun}
              disabled={agent.running || !query.trim()}
            >
              Create Tag
            </Button>
          </div>
        </div>

        {/* Steps */}
        {agent.steps.length > 0 && (
          <div className={styles.stepsList}>
            {agent.steps.map((step) => (
              <div key={step.id} className={styles.stepRow}>
                <span className={styles.stepIcon}>
                  <StepIcon status={step.status} />
                </span>
                <div className={styles.stepContent}>
                  <Text weight="semibold">{step.label}</Text>
                  {step.detail && <Caption1>{step.detail}</Caption1>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Approval card */}
        {agent.pendingPayload && (
          <Card className={styles.approvalCard}>
            <CardHeader header={<Text weight="semibold">Review before creating</Text>} />
            <Divider />
            <div className={styles.approvalGrid}>
              <Text className={styles.approvalLabel}>Tag Name</Text>
              <Text>{agent.pendingPayload.display.tagName}</Text>
              <Text className={styles.approvalLabel}>Description</Text>
              <Text>{agent.pendingPayload.display.description}</Text>
              <Text className={styles.approvalLabel}>Site</Text>
              <Text>{agent.pendingPayload.display.site}</Text>
              <Text className={styles.approvalLabel}>Line</Text>
              <Text>{agent.pendingPayload.display.line}</Text>
              <Text className={styles.approvalLabel}>Equipment</Text>
              <Text>{agent.pendingPayload.display.equipment}</Text>
              <Text className={styles.approvalLabel}>Unit</Text>
              <Text>{agent.pendingPayload.display.unit}</Text>
              <Text className={styles.approvalLabel}>Datatype</Text>
              <Text>{agent.pendingPayload.display.datatype}</Text>
              <Text className={styles.approvalLabel}>Criticality</Text>
              <Text>{agent.pendingPayload.display.criticality}</Text>
              <Text className={styles.approvalLabel}>Asset</Text>
              <Text>{agent.pendingPayload.display.assetHierarchy}</Text>
            </div>
            <div className={styles.approvalActions}>
              <Button appearance="primary" onClick={agent.approve}>
                Approve &amp; Create
              </Button>
              <Button appearance="secondary" onClick={agent.reject}>
                Cancel
              </Button>
            </div>
          </Card>
        )}

        {/* Result card */}
        {agent.result && (
          <Card className={styles.resultCard}>
            <CardHeader
              header={<Text weight="semibold">Tag created successfully</Text>}
            />
            <Text>{agent.result.tag.name}</Text>
            <Caption1>{agent.result.tag.description}</Caption1>
            <Link to={`/tags/${agent.result.tag.id}`} className={styles.resultLink}>
              <Text>View tag</Text>
              <ArrowRightRegular />
            </Link>
          </Card>
        )}
      </DrawerBody>
    </OverlayDrawer>
  );
}
