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
  EditRegular,
} from "@fluentui/react-icons";
import type { Tag } from "../types/tag";
import type { Asset } from "../types/asset";
import StatusBadge from "./StatusBadge";
import CriticalityBadge from "./CriticalityBadge";
import ApprovalBadge from "./ApprovalBadge";

const PAGE_SIZE = 15;

const useStyles = makeStyles({
  row: {
    cursor: "pointer",
    ":hover": {
      backgroundColor: tokens.colorNeutralBackground1Hover,
    },
  },
  truncateCell: {
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    display: "block",
  },
  nameCell: {
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    display: "block",
    fontWeight: tokens.fontWeightSemibold,
  },
  pagination: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: tokens.spacingHorizontalM,
    paddingTop: tokens.spacingVerticalM,
    paddingBottom: tokens.spacingVerticalM,
  },
});

interface TagTableProps {
  tags: Tag[];
  assets: Asset[];
  onTagClick: (tagId: string) => void;
  onEditClick?: (tagId: string) => void;
}

export default function TagTable({ tags, assets, onTagClick, onEditClick }: TagTableProps) {
  const styles = useStyles();
  const [page, setPage] = useState(0);

  const assetMap = new Map(assets.map((a) => [a.id, a]));

  const columns: TableColumnDefinition<Tag>[] = [
    createTableColumn<Tag>({
      columnId: "name",
      compare: (a, b) => a.name.localeCompare(b.name),
      renderHeaderCell: () => "Name",
      renderCell: (item) => (
        <span className={styles.nameCell} title={item.name}>{item.name}</span>
      ),
    }),
    createTableColumn<Tag>({
      columnId: "description",
      renderHeaderCell: () => "Description",
      renderCell: (item) => (
        <span className={styles.truncateCell} title={item.description}>
          {item.description}
        </span>
      ),
    }),
    createTableColumn<Tag>({
      columnId: "asset",
      renderHeaderCell: () => "Asset",
      renderCell: (item) => {
        const asset = assetMap.get(item.assetId);
        const text = asset ? asset.hierarchy : item.assetId;
        return <span className={styles.truncateCell} title={text}>{text}</span>;
      },
    }),
    createTableColumn<Tag>({
      columnId: "status",
      compare: (a, b) => a.status.localeCompare(b.status),
      renderHeaderCell: () => "Status",
      renderCell: (item) => <StatusBadge status={item.status} />,
    }),
    createTableColumn<Tag>({
      columnId: "approval",
      compare: (a, b) =>
        (a.approvalStatus ?? "none").localeCompare(b.approvalStatus ?? "none"),
      renderHeaderCell: () => "Approval",
      renderCell: (item) => (
        <ApprovalBadge approvalStatus={item.approvalStatus ?? "none"} />
      ),
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
    ...(onEditClick
      ? [
          createTableColumn<Tag>({
            columnId: "actions",
            renderHeaderCell: () => "",
            renderCell: (item) => (
              <Button
                appearance="subtle"
                icon={<EditRegular />}
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  onEditClick(item.id);
                }}
              />
            ),
          }),
        ]
      : []),
  ];

  const columnSizingOptions = {
    name: { idealWidth: 240, minWidth: 150 },
    description: { idealWidth: 280, minWidth: 150 },
    asset: { idealWidth: 200, minWidth: 120 },
    status: { idealWidth: 90, minWidth: 80 },
    approval: { idealWidth: 100, minWidth: 80 },
    criticality: { idealWidth: 100, minWidth: 80 },
    actions: { idealWidth: 48, minWidth: 48 },
  };

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
        resizableColumns
        columnSizingOptions={columnSizingOptions}
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
