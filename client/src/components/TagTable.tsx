import { useState } from "react";
import {
  DataGrid,
  DataGridHeader,
  DataGridHeaderCell,
  DataGridBody,
  DataGridRow,
  DataGridCell,
  createTableColumn,
  makeStyles,
  tokens,
  Button,
  Text,
} from "@fluentui/react-components";
import type { TableColumnDefinition, DataGridProps } from "@fluentui/react-components";
import {
  ChevronLeftRegular,
  ChevronRightRegular,
} from "@fluentui/react-icons";
import type { Tag } from "../types/tag";
import type { Asset } from "../types/asset";
import StatusBadge from "./StatusBadge";
import CriticalityBadge from "./CriticalityBadge";

const PAGE_SIZE = 15;

const useStyles = makeStyles({
  row: {
    cursor: "pointer",
    ":hover": {
      backgroundColor: tokens.colorNeutralBackground1Hover,
    },
  },
  description: {
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    maxWidth: "250px",
  },
  pagination: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: tokens.spacingHorizontalM,
    paddingTop: tokens.spacingVerticalM,
    paddingBottom: tokens.spacingVerticalM,
  },
  nameCell: {
    fontWeight: tokens.fontWeightSemibold,
  },
});

interface TagTableProps {
  tags: Tag[];
  assets: Asset[];
  onTagClick: (tagId: string) => void;
}

export default function TagTable({ tags, assets, onTagClick }: TagTableProps) {
  const styles = useStyles();
  const [page, setPage] = useState(0);

  const assetMap = new Map(assets.map((a) => [a.id, a]));

  const columns: TableColumnDefinition<Tag>[] = [
    createTableColumn<Tag>({
      columnId: "name",
      compare: (a, b) => a.name.localeCompare(b.name),
      renderHeaderCell: () => "Name",
      renderCell: (item) => (
        <span className={styles.nameCell}>{item.name}</span>
      ),
    }),
    createTableColumn<Tag>({
      columnId: "description",
      renderHeaderCell: () => "Description",
      renderCell: (item) => (
        <span className={styles.description} title={item.description}>
          {item.description}
        </span>
      ),
    }),
    createTableColumn<Tag>({
      columnId: "asset",
      renderHeaderCell: () => "Asset",
      renderCell: (item) => {
        const asset = assetMap.get(item.assetId);
        return asset ? asset.hierarchy : item.assetId;
      },
    }),
    createTableColumn<Tag>({
      columnId: "status",
      compare: (a, b) => a.status.localeCompare(b.status),
      renderHeaderCell: () => "Status",
      renderCell: (item) => <StatusBadge status={item.status} />,
    }),
    createTableColumn<Tag>({
      columnId: "criticality",
      compare: (a, b) => {
        const order = { critical: 0, high: 1, medium: 2, low: 3 };
        return order[a.criticality] - order[b.criticality];
      },
      renderHeaderCell: () => "Criticality",
      renderCell: (item) => <CriticalityBadge criticality={item.criticality} />,
    }),
  ];

  const totalPages = Math.max(1, Math.ceil(tags.length / PAGE_SIZE));
  const pagedTags = tags.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const handleSortChange: DataGridProps["onSortChange"] = () => {
    setPage(0);
  };

  return (
    <>
      <DataGrid
        items={pagedTags}
        columns={columns}
        sortable
        onSortChange={handleSortChange}
        getRowId={(item) => item.id}
      >
        <DataGridHeader>
          <DataGridRow>
            {({ renderHeaderCell }) => (
              <DataGridHeaderCell>{renderHeaderCell()}</DataGridHeaderCell>
            )}
          </DataGridRow>
        </DataGridHeader>
        <DataGridBody<Tag>>
          {({ item, rowId }) => (
            <DataGridRow<Tag>
              key={rowId}
              className={styles.row}
              onClick={() => onTagClick(item.id)}
            >
              {({ renderCell }) => (
                <DataGridCell>{renderCell(item)}</DataGridCell>
              )}
            </DataGridRow>
          )}
        </DataGridBody>
      </DataGrid>

      {tags.length > PAGE_SIZE && (
        <div className={styles.pagination}>
          <Button
            appearance="subtle"
            icon={<ChevronLeftRegular />}
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          />
          <Text>
            Page {page + 1} of {totalPages}
          </Text>
          <Button
            appearance="subtle"
            icon={<ChevronRightRegular />}
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
          />
        </div>
      )}
    </>
  );
}
