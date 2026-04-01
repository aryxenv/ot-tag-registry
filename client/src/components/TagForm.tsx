import { useState, useEffect } from "react";
import {
  makeStyles,
  tokens,
  Field,
  Input,
  Textarea,
  Dropdown,
  Option,
  Button,
  Tooltip,
  MessageBar,
  MessageBarBody,
} from "@fluentui/react-components";
import { SparkleRegular } from "@fluentui/react-icons";
import { useAssets } from "../hooks/useAssets";
import type {
  Tag,
  CreateTag,
  Criticality,
  NameValidationError,
  ValidateNameResponse,
} from "../types/tag";

export interface TagFormProps {
  mode: "create" | "edit";
  initialData?: Tag;
  onSubmit: (data: CreateTag) => Promise<void>;
  onCancel: () => void;
  onRetire?: () => void;
}

interface FormState {
  name: string;
  description: string;
  unit: string;
  customUnit: string;
  criticality: Criticality;
  site: string;
  line: string;
  equipment: string;
}

const INITIAL_FORM: FormState = {
  name: "",
  description: "",
  unit: "",
  customUnit: "",
  criticality: "medium",
  site: "",
  line: "",
  equipment: "",
};

const CRITICALITY_OPTIONS: { value: Criticality; label: string }[] = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "critical", label: "Critical" },
];

const UNIT_OPTIONS = [
  "bar",
  "°C",
  "°F",
  "RPM",
  "L/min",
  "m/s",
  "kW",
  "A",
  "V",
  "%",
  "mm/s",
  "kg",
  "Hz",
  "Pa",
  "m³/h",
  "—",
];

const OTHER_UNIT_VALUE = "__other__";

const useStyles = makeStyles({
  form: {
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacingVerticalL,
    maxWidth: "720px",
    paddingTop: tokens.spacingVerticalL,
  },
  row: {
    display: "flex",
    gap: tokens.spacingHorizontalL,
  },
  halfField: {
    flex: 1,
    minWidth: 0,
  },
  suggestButton: {
    alignSelf: "flex-start",
  },
  actions: {
    display: "flex",
    gap: tokens.spacingHorizontalM,
    paddingTop: tokens.spacingVerticalL,
  },
  retireButton: {
    marginLeft: "auto",
  },
});

export default function TagForm({
  mode,
  initialData,
  onSubmit,
  onCancel,
  onRetire,
}: TagFormProps) {
  const styles = useStyles();
  const { assets } = useAssets();

  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [nameErrors, setNameErrors] = useState<NameValidationError[]>([]);
  const [nameValidating, setNameValidating] = useState(false);
  const [nameValid, setNameValid] = useState<boolean | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [attempted, setAttempted] = useState(false);

  // Pre-populate form in edit mode once assets load
  useEffect(() => {
    if (mode === "edit" && initialData && assets.length > 0) {
      const asset = assets.find((a) => a.id === initialData.assetId);
      const isPresetUnit = UNIT_OPTIONS.includes(initialData.unit);
      setForm({
        name: initialData.name,
        description: initialData.description,
        unit: isPresetUnit ? initialData.unit : OTHER_UNIT_VALUE,
        customUnit: isPresetUnit ? "" : initialData.unit,
        criticality: initialData.criticality,
        site: asset?.site ?? "",
        line: asset?.line ?? "",
        equipment: asset?.equipment ?? "",
      });
      setNameValid(true);
    }
  }, [mode, initialData, assets]);

  // --- Asset cascade ---
  const uniqueSites = [...new Set(assets.map((a) => a.site))].sort();
  const uniqueLines = form.site
    ? [
        ...new Set(
          assets.filter((a) => a.site === form.site).map((a) => a.line),
        ),
      ].sort()
    : [];
  const uniqueEquipment =
    form.site && form.line
      ? [
          ...new Set(
            assets
              .filter(
                (a) => a.site === form.site && a.line === form.line,
              )
              .map((a) => a.equipment),
          ),
        ].sort()
      : [];

  const resolvedAsset =
    form.site && form.line && form.equipment
      ? assets.find(
          (a) =>
            a.site === form.site &&
            a.line === form.line &&
            a.equipment === form.equipment,
        )
      : undefined;

  // --- Resolved unit value ---
  const resolvedUnit =
    form.unit === OTHER_UNIT_VALUE ? form.customUnit : form.unit;

  // --- Field helpers ---
  const updateField = <K extends keyof FormState>(
    field: K,
    value: FormState[K],
  ) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSiteChange = (value: string) => {
    setForm((prev) => ({ ...prev, site: value, line: "", equipment: "" }));
  };

  const handleLineChange = (value: string) => {
    setForm((prev) => ({ ...prev, line: value, equipment: "" }));
  };

  // --- Name validation on blur ---
  const validateName = async () => {
    const name = form.name.trim();
    if (!name) {
      setNameErrors([]);
      setNameValid(null);
      return;
    }
    setNameValidating(true);
    try {
      const res = await fetch("/api/tags/validate-name", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      const data: ValidateNameResponse = await res.json();
      setNameValid(data.valid);
      setNameErrors(data.errors);
    } catch {
      setNameErrors([
        {
          segment: "api",
          message: "Failed to validate name",
          received: name,
          expected: null,
        },
      ]);
      setNameValid(false);
    } finally {
      setNameValidating(false);
    }
  };

  // --- Submit ---
  const handleSubmit = async () => {
    setAttempted(true);

    if (
      !form.name ||
      !form.description ||
      !resolvedUnit ||
      !form.equipment ||
      !form.criticality
    ) {
      setSubmitError("Please fill in all required fields.");
      return;
    }
    if (nameValid === false) {
      setSubmitError("Please fix the tag name errors before submitting.");
      return;
    }
    if (mode === "create" && !resolvedAsset) {
      setSubmitError(
        "Please select a valid asset (site, line, and equipment).",
      );
      return;
    }

    const assetId =
      mode === "edit" ? initialData!.assetId : resolvedAsset!.id;

    setSubmitting(true);
    setSubmitError(null);
    try {
      await onSubmit({
        name: form.name,
        description: form.description,
        unit: resolvedUnit,
        datatype: "float",
        samplingFrequency: 1.0,
        criticality: form.criticality,
        assetId,
        sourceId: null,
      });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to save tag.";
      setSubmitError(message);
    } finally {
      setSubmitting(false);
    }
  };

  // --- Validation helpers ---
  const requiredError = (value: string) =>
    attempted && !value ? "This field is required" : undefined;

  const nameValidationState = nameValidating
    ? undefined
    : nameValid === true
      ? ("success" as const)
      : nameValid === false
        ? ("error" as const)
        : attempted && !form.name
          ? ("error" as const)
          : undefined;

  const nameMessage = nameValidating
    ? "Validating..."
    : nameValid === true
      ? "Valid name"
      : nameErrors.length > 0
        ? nameErrors.map((e) => `[${e.segment}] ${e.message}`).join("; ")
        : requiredError(form.name);

  const unitError = requiredError(resolvedUnit);

  const isAssetDisabled = mode === "edit";

  return (
    <div className={styles.form}>
      {submitError && (
        <MessageBar intent="error">
          <MessageBarBody>{submitError}</MessageBarBody>
        </MessageBar>
      )}

      {/* Row 1: Site + Line (side by side) */}
      <div className={styles.row}>
        <Field
          className={styles.halfField}
          label="Site"
          required
          hint={isAssetDisabled ? "Cannot change after creation" : undefined}
          validationState={
            attempted && !form.site ? "error" : undefined
          }
          validationMessage={requiredError(form.site)}
        >
          <Dropdown
            disabled={isAssetDisabled}
            placeholder="Select site"
            value={form.site}
            selectedOptions={form.site ? [form.site] : []}
            onOptionSelect={(_e, data) =>
              handleSiteChange(data.optionValue ?? "")
            }
          >
            {uniqueSites.map((site) => (
              <Option key={site} value={site}>
                {site}
              </Option>
            ))}
          </Dropdown>
        </Field>
        <Field
          className={styles.halfField}
          label="Line"
          required
          validationState={
            attempted && !form.line ? "error" : undefined
          }
          validationMessage={requiredError(form.line)}
        >
          <Dropdown
            disabled={isAssetDisabled || !form.site}
            placeholder="Select line"
            value={form.line}
            selectedOptions={form.line ? [form.line] : []}
            onOptionSelect={(_e, data) =>
              handleLineChange(data.optionValue ?? "")
            }
          >
            {uniqueLines.map((line) => (
              <Option key={line} value={line}>
                {line}
              </Option>
            ))}
          </Dropdown>
        </Field>
      </div>

      {/* Row 2: Description (full width) */}
      <Field
        label="Describe the sensor"
        required
        validationState={
          attempted && !form.description ? "error" : undefined
        }
        validationMessage={requiredError(form.description)}
      >
        <Textarea
          value={form.description}
          onChange={(_e, data) => updateField("description", data.value)}
          placeholder="e.g. outlet pressure sensor on the main cooling pump"
          rows={3}
          resize="vertical"
        />
      </Field>

      {/* Row 3: Criticality */}
      <Field label="How critical is this?" required>
        <Dropdown
          value={
            CRITICALITY_OPTIONS.find((o) => o.value === form.criticality)
              ?.label ?? ""
          }
          selectedOptions={[form.criticality]}
          onOptionSelect={(_e, data) =>
            updateField(
              "criticality",
              (data.optionValue as Criticality) ?? "medium",
            )
          }
        >
          {CRITICALITY_OPTIONS.map((opt) => (
            <Option key={opt.value} value={opt.value}>
              {opt.label}
            </Option>
          ))}
        </Dropdown>
      </Field>

      {/* Row 4: Suggest a Name button (stub) */}
      <Tooltip
        content="AI-powered suggestions coming soon"
        relationship="description"
      >
        <Button
          className={styles.suggestButton}
          appearance="outline"
          icon={<SparkleRegular />}
          disabled
        >
          Suggest a Name
        </Button>
      </Tooltip>

      {/* Row 5: Equipment + Unit (side by side) */}
      <div className={styles.row}>
        <Field
          className={styles.halfField}
          label="Equipment"
          required
          validationState={
            attempted && !form.equipment ? "error" : undefined
          }
          validationMessage={requiredError(form.equipment)}
        >
          <Dropdown
            disabled={isAssetDisabled || !form.line}
            placeholder="Select equipment"
            value={form.equipment}
            selectedOptions={form.equipment ? [form.equipment] : []}
            onOptionSelect={(_e, data) =>
              updateField("equipment", data.optionValue ?? "")
            }
          >
            {uniqueEquipment.map((eq) => (
              <Option key={eq} value={eq}>
                {eq}
              </Option>
            ))}
          </Dropdown>
        </Field>
        <Field
          className={styles.halfField}
          label="Unit"
          required
          validationState={unitError ? "error" : undefined}
          validationMessage={unitError}
        >
          <Dropdown
            placeholder="Select unit"
            value={
              form.unit === OTHER_UNIT_VALUE
                ? "Other..."
                : form.unit
            }
            selectedOptions={form.unit ? [form.unit] : []}
            onOptionSelect={(_e, data) => {
              const val = data.optionValue ?? "";
              setForm((prev) => ({
                ...prev,
                unit: val,
                customUnit: val === OTHER_UNIT_VALUE ? prev.customUnit : "",
              }));
            }}
          >
            {UNIT_OPTIONS.map((u) => (
              <Option key={u} value={u}>
                {u}
              </Option>
            ))}
            <Option key={OTHER_UNIT_VALUE} value={OTHER_UNIT_VALUE}>
              Other...
            </Option>
          </Dropdown>
        </Field>
      </div>

      {/* Custom unit input (shown when "Other..." is selected) */}
      {form.unit === OTHER_UNIT_VALUE && (
        <Field
          label="Custom unit"
          required
          validationState={
            attempted && !form.customUnit ? "error" : undefined
          }
          validationMessage={requiredError(form.customUnit)}
        >
          <Input
            value={form.customUnit}
            onChange={(_e, data) => updateField("customUnit", data.value)}
            placeholder="Enter custom unit"
          />
        </Field>
      )}

      {/* Row 6: Tag Name (with validation on blur) */}
      <Field
        label="Tag Name"
        required
        validationState={nameValidationState}
        validationMessage={nameMessage}
      >
        <Input
          value={form.name}
          onChange={(_e, data) => updateField("name", data.value)}
          onBlur={validateName}
          placeholder="e.g. Plant.Line2.Pump001.Temperature"
        />
      </Field>

      {/* Actions */}
      <div className={styles.actions}>
        <Button
          appearance="primary"
          onClick={handleSubmit}
          disabled={submitting}
        >
          {submitting
            ? "Saving..."
            : mode === "create"
              ? "Create Tag"
              : "Save Changes"}
        </Button>
        <Button
          appearance="secondary"
          onClick={onCancel}
          disabled={submitting}
        >
          Cancel
        </Button>
        {mode === "edit" && onRetire && (
          <Button
            className={styles.retireButton}
            appearance="subtle"
            onClick={onRetire}
            disabled={submitting}
          >
            Retire Tag
          </Button>
        )}
      </div>
    </div>
  );
}
