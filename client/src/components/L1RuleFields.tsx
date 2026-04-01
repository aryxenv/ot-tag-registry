import {
  makeStyles,
  tokens,
  Field,
  Input,
  Dropdown,
  Option,
} from "@fluentui/react-components";
import type { MissingDataPolicy } from "../types/rule";

// eslint-disable-next-line react-refresh/only-export-components
export const MISSING_DATA_OPTIONS: { value: MissingDataPolicy; label: string }[] = [
  { value: "alert", label: "Alert" },
  { value: "ignore", label: "Ignore" },
  { value: "interpolate", label: "Interpolate" },
  { value: "last-known", label: "Last Known" },
];

export interface L1RuleFieldsProps {
  min: string;
  max: string;
  spikeThreshold: string;
  missingDataPolicy: MissingDataPolicy;
  onMinChange: (val: string) => void;
  onMaxChange: (val: string) => void;
  onSpikeThresholdChange: (val: string) => void;
  onMissingDataPolicyChange: (val: MissingDataPolicy) => void;
  attempted?: boolean;
}

const useStyles = makeStyles({
  row: {
    display: "flex",
    gap: tokens.spacingHorizontalL,
  },
  halfField: {
    flex: 1,
    minWidth: 0,
  },
});

export default function L1RuleFields({
  min,
  max,
  spikeThreshold,
  missingDataPolicy,
  onMinChange,
  onMaxChange,
  onSpikeThresholdChange,
  onMissingDataPolicyChange,
  attempted,
}: L1RuleFieldsProps) {
  const styles = useStyles();

  const hasAtLeastOneThreshold =
    min.trim() !== "" || max.trim() !== "" || spikeThreshold.trim() !== "";

  return (
    <>
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
            onChange={(_e, data) => onMinChange(data.value)}
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
            onChange={(_e, data) => onMaxChange(data.value)}
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
            onChange={(_e, data) => onSpikeThresholdChange(data.value)}
            placeholder="e.g. 10"
          />
        </Field>
        <Field className={styles.halfField} label="Missing data policy">
          <Dropdown
            value={
              MISSING_DATA_OPTIONS.find((o) => o.value === missingDataPolicy)
                ?.label ?? "Alert"
            }
            selectedOptions={[missingDataPolicy]}
            onOptionSelect={(_e, data) =>
              onMissingDataPolicyChange(
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
    </>
  );
}
