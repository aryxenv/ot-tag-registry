import { useState, useEffect, useRef } from "react";
import {
  Input,
  Dropdown,
  Option,
  makeStyles,
  tokens,
} from "@fluentui/react-components";
import { SearchRegular } from "@fluentui/react-icons";
import type { TagStatus } from "../types/tag";
import type { Asset } from "../types/asset";

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

const STATUS_OPTIONS: { value: TagStatus | ""; label: string }[] = [
  { value: "", label: "All statuses" },
  { value: "active", label: "Active" },
  { value: "draft", label: "Draft" },
  { value: "retired", label: "Retired" },
];

export default function TagFilters({ filters, onFiltersChange, assets }: TagFiltersProps) {
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
        value={STATUS_OPTIONS.find((o) => o.value === filters.status)?.label ?? "All statuses"}
        selectedOptions={[filters.status]}
        onOptionSelect={(_e, data) =>
          onFiltersChange({ ...filters, status: (data.optionValue as TagStatus | "") ?? "" })
        }
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
        value={filters.site || "All sites"}
        selectedOptions={[filters.site]}
        onOptionSelect={(_e, data) =>
          onFiltersChange({
            ...filters,
            site: data.optionValue ?? "",
            line: "",
            equipment: "",
          })
        }
      >
        <Option value="">All sites</Option>
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
        value={filters.line || "All lines"}
        selectedOptions={[filters.line]}
        onOptionSelect={(_e, data) =>
          onFiltersChange({
            ...filters,
            line: data.optionValue ?? "",
            equipment: "",
          })
        }
      >
        <Option value="">All lines</Option>
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
        value={filters.equipment || "All equipment"}
        selectedOptions={[filters.equipment]}
        onOptionSelect={(_e, data) =>
          onFiltersChange({
            ...filters,
            equipment: data.optionValue ?? "",
          })
        }
      >
        <Option value="">All equipment</Option>
        {uniqueEquipment.map((eq) => (
          <Option key={eq} value={eq}>
            {eq}
          </Option>
        ))}
      </Dropdown>
    </div>
  );
}
