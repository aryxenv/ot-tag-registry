import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Title2,
  Accordion,
  AccordionItem,
  AccordionHeader,
  AccordionPanel,
  makeStyles,
  tokens,
} from "@fluentui/react-components";
import {
  ShieldCheckmarkRegular,
  DataUsageRegular,
} from "@fluentui/react-icons";
import TagForm from "../components/TagForm";
import L1RuleFields from "../components/L1RuleFields";
import L2RuleFields, {
  type RowState,
  EMPTY_ROW,
  rowToMapping,
} from "../components/L2RuleFields";
import { useCreateTag } from "../hooks/useCreateTag";
import { useSaveL1Rule } from "../hooks/useSaveL1Rule";
import { useSaveL2Rule } from "../hooks/useSaveL2Rule";
import type { CreateTag } from "../types/tag";
import type { MissingDataPolicy } from "../types/rule";

const useStyles = makeStyles({
  header: {
    marginBottom: tokens.spacingVerticalS,
  },
  rulePanel: {
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacingVerticalM,
    paddingTop: tokens.spacingVerticalM,
    paddingBottom: tokens.spacingVerticalM,
  },
});

interface L1FormState {
  min: string;
  max: string;
  spikeThreshold: string;
  missingDataPolicy: MissingDataPolicy;
}

const INITIAL_L1: L1FormState = {
  min: "",
  max: "",
  spikeThreshold: "",
  missingDataPolicy: "alert",
};

export default function TagCreatePage() {
  const styles = useStyles();
  const navigate = useNavigate();
  const createTag = useCreateTag();
  const saveL1Rule = useSaveL1Rule();
  const saveL2Rule = useSaveL2Rule();

  const [l1, setL1] = useState<L1FormState>(INITIAL_L1);
  const [l2Rows, setL2Rows] = useState<RowState[]>([{ ...EMPTY_ROW }]);

  const handleSubmit = async (data: CreateTag) => {
    const newTag = await createTag.mutateAsync(data);

    // Save L1 rule if any threshold was configured
    const hasL1 =
      l1.min.trim() !== "" ||
      l1.max.trim() !== "" ||
      l1.spikeThreshold.trim() !== "";
    if (hasL1) {
      const parseNum = (v: string): number | null => {
        const n = Number(v.trim());
        return v.trim() === "" || isNaN(n) ? null : n;
      };
      await saveL1Rule.mutateAsync({
        tagId: newTag.id,
        data: {
          min: parseNum(l1.min) ?? undefined,
          max: parseNum(l1.max) ?? undefined,
          spikeThreshold: parseNum(l1.spikeThreshold) ?? undefined,
          missingDataPolicy: l1.missingDataPolicy,
        },
      });
    }

    // Save L2 rule if any valid rows were configured
    const l2Mappings = l2Rows
      .map(rowToMapping)
      .filter((m): m is NonNullable<typeof m> => m !== null);
    if (l2Mappings.length > 0) {
      await saveL2Rule.mutateAsync({
        tagId: newTag.id,
        data: { stateMapping: l2Mappings },
      });
    }

    navigate("/tags");
  };

  const rulesAccordion = (
    <Accordion collapsible>
      <AccordionItem value="l1">
        <AccordionHeader icon={<ShieldCheckmarkRegular />}>
          L1 — Range Rules
        </AccordionHeader>
        <AccordionPanel>
          <div className={styles.rulePanel}>
            <L1RuleFields
              min={l1.min}
              max={l1.max}
              spikeThreshold={l1.spikeThreshold}
              missingDataPolicy={l1.missingDataPolicy}
              onMinChange={(v) => setL1((s) => ({ ...s, min: v }))}
              onMaxChange={(v) => setL1((s) => ({ ...s, max: v }))}
              onSpikeThresholdChange={(v) =>
                setL1((s) => ({ ...s, spikeThreshold: v }))
              }
              onMissingDataPolicyChange={(v) =>
                setL1((s) => ({ ...s, missingDataPolicy: v }))
              }
            />
          </div>
        </AccordionPanel>
      </AccordionItem>

      <AccordionItem value="l2">
        <AccordionHeader icon={<DataUsageRegular />}>
          L2 — State Profiles
        </AccordionHeader>
        <AccordionPanel>
          <div className={styles.rulePanel}>
            <L2RuleFields rows={l2Rows} onRowsChange={setL2Rows} />
          </div>
        </AccordionPanel>
      </AccordionItem>
    </Accordion>
  );

  return (
    <div>
      <Title2 className={styles.header}>Create Tag</Title2>
      <TagForm
        mode="create"
        onSubmit={handleSubmit}
        onCancel={() => navigate("/tags")}
        advancedContent={rulesAccordion}
      />
    </div>
  );
}
