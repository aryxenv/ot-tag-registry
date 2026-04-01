import { useState } from "react";
import {
  Title2,
  Spinner,
  Text,
  Button,
  ProgressBar,
  makeStyles,
  tokens,
} from "@fluentui/react-components";
import { AddRegular } from "@fluentui/react-icons";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useTags } from "../hooks/useTags";
import { useAssets } from "../hooks/useAssets";
import TagFilters from "../components/TagFilters";
import TagTable from "../components/TagTable";
import type { TagFilterValues } from "../components/TagFilters";
import type { TagStatus } from "../types/tag";

const useStyles = makeStyles({
  headerRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "16px",
  },
  center: {
    display: "flex",
    justifyContent: "center",
    paddingTop: tokens.spacingVerticalXXL,
  },
  empty: {
    display: "flex",
    justifyContent: "center",
    paddingTop: tokens.spacingVerticalXXL,
    color: tokens.colorNeutralForeground3,
  },
});

const initialFilters: TagFilterValues = {
  search: "",
  status: "",
  site: "",
  line: "",
  equipment: "",
};

export default function TagListPage() {
  const styles = useStyles();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<TagFilterValues>(initialFilters);

  const { assets, loading: assetsLoading, refreshing: assetsRefreshing } = useAssets();

  // Find all assets matching the current site/line/equipment filters
  const matchedAssetIds = new Set(
    assets
      .filter((a) => {
        if (filters.site && a.site !== filters.site) return false;
        if (filters.line && a.line !== filters.line) return false;
        if (filters.equipment && a.equipment !== filters.equipment) return false;
        return true;
      })
      .map((a) => a.id),
  );

  // When all three are selected, pass the single assetId for an efficient partition-scoped query
  const exactAsset =
    filters.site && filters.line && filters.equipment
      ? assets.find(
          (a) =>
            a.site === filters.site &&
            a.line === filters.line &&
            a.equipment === filters.equipment,
        )
      : undefined;

  const apiFilters: { status?: TagStatus; assetId?: string; search?: string } = {};
  if (filters.status) apiFilters.status = filters.status;
  if (exactAsset) apiFilters.assetId = exactAsset.id;
  if (filters.search) apiFilters.search = filters.search;

  const { tags: fetchedTags, loading: tagsLoading, refreshing: tagsRefreshing } = useTags(apiFilters);

  // Client-side filtering for partial site/line/equipment selection
  const hasPartialAssetFilter = !!(filters.site || filters.line || filters.equipment) && !exactAsset;
  const tags = hasPartialAssetFilter
    ? fetchedTags.filter((t) => matchedAssetIds.has(t.assetId))
    : fetchedTags;

  const handleTagClick = (tagId: string) => {
    navigate(`/tags/${tagId}/edit`);
  };

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ["tags"] });
    queryClient.invalidateQueries({ queryKey: ["assets"] });
  };

  return (
    <div>
      <div className={styles.headerRow}>
        <Title2>Tags</Title2>
        <Button
          appearance="primary"
          icon={<AddRegular />}
          onClick={() => navigate("/tags/new")}
        >
          Create Tag
        </Button>
      </div>
      <TagFilters filters={filters} onFiltersChange={setFilters} onRefresh={handleRefresh} assets={assets} />

      {(tagsRefreshing || assetsRefreshing) && <ProgressBar />}

      {tagsLoading || assetsLoading ? (
        <div className={styles.center}>
          <Spinner label="Loading tags..." />
        </div>
      ) : tags.length === 0 ? (
        <div className={styles.empty}>
          <Text>No tags found. Try adjusting your filters.</Text>
        </div>
      ) : (
        <TagTable tags={tags} assets={assets} onTagClick={handleTagClick} />
      )}
    </div>
  );
}
