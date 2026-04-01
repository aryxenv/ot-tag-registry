import { useState, useEffect, useRef } from "react";
import {
  Input,
  Dropdown,
  Option,
  Button,
  Tooltip,
  makeStyles,
  tokens,
} from "@fluentui/react-components";
import { SearchRegular, ArrowClockwiseRegular } from "@fluentui/react-icons";
import type { TagStatus } from "../types/tag";
import type { Asset } from "../types/asset";

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
    display: "flex",
    flexWrap: "wrap",
    alignItems: "end",
    gap: tokens.spacingHorizontalM,
    paddingBottom: tokens.spacingVerticalL,
  },
  field: {
    minWidth: "160px",
  },
});

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: ALL_SENTINEL, label: "All statuses" },
  { value: "active", label: "Active" },
  { value: "draft", label: "Draft" },
  { value: "retired", label: "Retired" },
];

export default function TagFilters({ filters, onFiltersChange, onRefresh, assets }: TagFiltersProps) {
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
    ? [...new Set(assets.filter((a) => a.site === filters.site).map((a) => a.line))].sort()
    : [];
  const uniqueEquipment =
    filters.site && filters.line
      ? [...new Set(
          assets
            .filter((a) => a.site === filters.site && a.line === filters.line)
            .map((a) => a.equipment),
        )].sort()
      : [];

  return (
    <div className={styles.root}>
      <Input
        className={styles.field}
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
          const val = data.optionValue === ALL_SENTINEL ? "" : (data.optionValue as TagStatus | "");
          onFiltersChange({ ...filters, status: val ?? "" });
        }}
      >
        {STATUS_OPTIONS.map((opt) => (
          <Option key={opt.value} value={opt.value}>
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
            site: data.optionValue === ALL_SENTINEL ? "" : (data.optionValue ?? ""),
            line: "",
            equipment: "",
          })
        }
      >
        <Option value={ALL_SENTINEL}>All sites</Option>
        {uniqueSites.map((site) => (
          <Option key={site} value={site}>
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
            line: data.optionValue === ALL_SENTINEL ? "" : (data.optionValue ?? ""),
            equipment: "",
          })
        }
      >
        <Option value={ALL_SENTINEL}>All lines</Option>
        {uniqueLines.map((line) => (
          <Option key={line} value={line}>
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
            equipment: data.optionValue === ALL_SENTINEL ? "" : (data.optionValue ?? ""),
          })
        }
      >
        <Option value={ALL_SENTINEL}>All equipment</Option>
        {uniqueEquipment.map((eq) => (
          <Option key={eq} value={eq}>
            {eq}
          </Option>
        ))}
      </Dropdown>

      <Tooltip content="Refresh" relationship="label">
        <Button
          appearance="subtle"
          icon={<ArrowClockwiseRegular />}
          onClick={onRefresh}
        />
      </Tooltip>
    </div>
  );
}
