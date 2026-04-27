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
  shorthands,
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
import { aperamTokens } from "../theme/aperamTheme";

const PAGE_SIZE = 15;

const useStyles = makeStyles({
  surface: {
    backgroundColor: aperamTokens.white,
    ...shorthands.border("1px", "solid", aperamTokens.steel200),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    overflow: "hidden",
    boxShadow: "0 1px 2px rgba(15, 42, 92, 0.03)",
  },
  grid: {
    minWidth: "980px",
    "& [role='columnheader']": {
      fontFamily: aperamTokens.displayFont,
      fontWeight: 600,
      fontSize: "11px",
      letterSpacing: "0.12em",
      textTransform: "uppercase",
      color: aperamTokens.steel500,
      backgroundColor: aperamTokens.white,
      borderBottom: `1px solid ${aperamTokens.steel200}`,
    },
    "& [role='gridcell']": {
      minHeight: "50px",
      fontSize: "13px",
      color: aperamTokens.steel700,
      borderBottom: `1px solid ${aperamTokens.steel200}`,
    },
    "& [role='row']:last-child [role='gridcell']": {
      borderBottomColor: "transparent",
    },
  },
  row: {
    cursor: "pointer",
    transitionDuration: "120ms",
    transitionProperty: "background-color, box-shadow",
    transitionTimingFunction: "ease-out",
    ":hover": {
      backgroundColor: "rgba(248, 250, 252, 0.82)",
      boxShadow: `inset 2px 0 0 ${aperamTokens.steel300}`,
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
    fontFamily: aperamTokens.displayFont,
    fontSize: "13px",
    fontWeight: 600,
    color: aperamTokens.navy600,
    fontVariantNumeric: "tabular-nums",
    letterSpacing: "-0.01em",
  },
  assetCell: {
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    display: "block",
    color: aperamTokens.steel500,
  },
  mutedDash: {
    color: aperamTokens.steel300,
    fontFamily: aperamTokens.displayFont,
    fontSize: "13px",
    fontWeight: 600,
  },
  pagination: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: tokens.spacingHorizontalM,
    paddingTop: tokens.spacingVerticalM,
    paddingBottom: tokens.spacingVerticalM,
    color: aperamTokens.steel700,
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
        return <span className={styles.assetCell} title={text}>{text}</span>;
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
      renderCell: (item) =>
        item.approvalStatus && item.approvalStatus !== "none" ? (
          <ApprovalBadge approvalStatus={item.approvalStatus} />
        ) : (
          <span className={styles.mutedDash}>—</span>
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
    name: { idealWidth: 300, minWidth: 180 },
    description: { idealWidth: 340, minWidth: 180 },
    asset: { idealWidth: 250, minWidth: 150 },
    status: { idealWidth: 86, minWidth: 76 },
    approval: { idealWidth: 104, minWidth: 88 },
    criticality: { idealWidth: 112, minWidth: 92 },
    actions: { idealWidth: 48, minWidth: 48 },
  };

  const totalPages = Math.max(1, Math.ceil(tags.length / PAGE_SIZE));
  const pagedTags = tags.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const handleSortChange: DataGridProps["onSortChange"] = () => {
    setPage(0);
  };

  return (
    <>
      <div className={styles.surface}>
        <DataGrid
          className={styles.grid}
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
      </div>

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
