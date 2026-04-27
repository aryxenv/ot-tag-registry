import {
  Button,
  Dropdown,
  Input,
  Option,
  Tooltip,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { ArrowClockwiseRegular, SearchRegular } from "@fluentui/react-icons";
import { useEffect, useRef, useState } from "react";
import { aperamTokens } from "../theme/aperamTheme";
import type { Asset } from "../types/asset";
import type { TagStatus } from "../types/tag";

const ALL_SENTINEL = "__all__";

export interface TagFilterValues {
  search: string;
  status: TagStatus | "";
  site: string;
  line: string;
  equipment: string;
}

interface TagFiltersProps {
  filters: TagFilterValues;
  onFiltersChange: (filters: TagFilterValues) => void;
  onRefresh: () => void;
  assets: Asset[];
}

const useStyles = makeStyles({
  root: {
    display: "grid",
    gridTemplateColumns:
      "minmax(220px, 1fr) repeat(4, minmax(148px, 216px)) auto",
    alignItems: "center",
    gap: tokens.spacingHorizontalM,
    backgroundColor: aperamTokens.white,
    ...shorthands.border("1px", "solid", aperamTokens.steel200),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    paddingTop: tokens.spacingVerticalM,
    paddingBottom: tokens.spacingVerticalM,
    paddingLeft: tokens.spacingHorizontalL,
    paddingRight: tokens.spacingHorizontalL,
    marginBottom: tokens.spacingVerticalL,
    boxShadow:
      "0 1px 2px rgba(15, 42, 92, 0.04), 0 8px 24px -18px rgba(15, 42, 92, 0.18)",
    position: "relative",
    "::before": {
      content: '""',
      position: "absolute",
      left: 0,
      top: "16px",
      bottom: "16px",
      width: "3px",
      borderRadius: "0 2px 2px 0",
      backgroundColor: aperamTokens.orange500,
      opacity: 0.85,
    },
    "@media (max-width: 1280px)": {
      gridTemplateColumns: "repeat(4, minmax(0, 1fr)) auto",
    },
    "@media (max-width: 760px)": {
      gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    },
    "@media (max-width: 520px)": {
      gridTemplateColumns: "1fr",
    },
  },
  field: {
    width: "100%",
    minWidth: 0,
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  searchField: {
    width: "100%",
    minWidth: 0,
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
    "@media (max-width: 1280px)": {
      gridColumnStart: 1,
      gridColumnEnd: -1,
    },
  },
  refreshButton: {
    justifySelf: "start",
    "@media (max-width: 760px)": {
      gridColumnStart: 1,
      gridColumnEnd: -1,
    },
  },
  noWrapOption: {
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
});

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: ALL_SENTINEL, label: "All statuses" },
  { value: "active", label: "Active" },
  { value: "draft", label: "Draft" },
  { value: "retired", label: "Retired" },
];

export default function TagFilters({
  filters,
  onFiltersChange,
  onRefresh,
  assets,
}: TagFiltersProps) {
  const styles = useStyles();
  const [searchInput, setSearchInput] = useState(filters.search);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      if (searchInput !== filters.search) {
        onFiltersChange({ ...filters, search: searchInput });
      }
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchInput, filters, onFiltersChange]);

  const uniqueSites = [...new Set(assets.map((a) => a.site))].sort();
  const uniqueLines = filters.site
    ? [
        ...new Set(
          assets.filter((a) => a.site === filters.site).map((a) => a.line),
        ),
      ].sort()
    : [];
  const uniqueEquipment =
    filters.site && filters.line
      ? [
          ...new Set(
            assets
              .filter((a) => a.site === filters.site && a.line === filters.line)
              .map((a) => a.equipment),
          ),
        ].sort()
      : [];

  return (
    <div className={styles.root}>
      <Input
        className={styles.searchField}
        contentBefore={<SearchRegular />}
        placeholder="Search tags..."
        value={searchInput}
        onChange={(_e, data) => setSearchInput(data.value)}
      />

      <Dropdown
        className={styles.field}
        placeholder="All statuses"
        selectedOptions={[filters.status || ALL_SENTINEL]}
        onOptionSelect={(_e, data) => {
          const val =
            data.optionValue === ALL_SENTINEL
              ? ""
              : (data.optionValue as TagStatus | "");
          onFiltersChange({ ...filters, status: val ?? "" });
        }}
      >
        {STATUS_OPTIONS.map((opt) => (
          <Option key={opt.value} value={opt.value} className={styles.noWrapOption}>
            {opt.label}
          </Option>
        ))}
      </Dropdown>

      <Dropdown
        className={styles.field}
        placeholder="All sites"
        selectedOptions={[filters.site || ALL_SENTINEL]}
        onOptionSelect={(_e, data) =>
          onFiltersChange({
            ...filters,
            site:
              data.optionValue === ALL_SENTINEL ? "" : (data.optionValue ?? ""),
            line: "",
            equipment: "",
          })
        }
      >
        <Option value={ALL_SENTINEL} className={styles.noWrapOption}>All sites</Option>
        {uniqueSites.map((site) => (
          <Option key={site} value={site} className={styles.noWrapOption}>
            {site}
          </Option>
        ))}
      </Dropdown>

      <Dropdown
        className={styles.field}
        placeholder="All lines"
        disabled={!filters.site}
        selectedOptions={[filters.line || ALL_SENTINEL]}
        onOptionSelect={(_e, data) =>
          onFiltersChange({
            ...filters,
            line:
              data.optionValue === ALL_SENTINEL ? "" : (data.optionValue ?? ""),
            equipment: "",
          })
        }
      >
        <Option value={ALL_SENTINEL} className={styles.noWrapOption}>All lines</Option>
        {uniqueLines.map((line) => (
          <Option key={line} value={line} className={styles.noWrapOption}>
            {line}
          </Option>
        ))}
      </Dropdown>

      <Dropdown
        className={styles.field}
        placeholder="All equipment"
        disabled={!filters.line}
        selectedOptions={[filters.equipment || ALL_SENTINEL]}
        onOptionSelect={(_e, data) =>
          onFiltersChange({
            ...filters,
            equipment:
              data.optionValue === ALL_SENTINEL ? "" : (data.optionValue ?? ""),
          })
        }
      >
        <Option value={ALL_SENTINEL} className={styles.noWrapOption}>All equipment</Option>
        {uniqueEquipment.map((eq) => (
          <Option key={eq} value={eq} className={styles.noWrapOption}>
            {eq}
          </Option>
        ))}
      </Dropdown>

      <Tooltip content="Refresh" relationship="label">
        <Button
          className={styles.refreshButton}
          appearance="secondary"
          icon={<ArrowClockwiseRegular />}
          onClick={onRefresh}
        />
      </Tooltip>
    </div>
  );
}
