import { useState } from "react";
import {
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
import PageHero from "../components/PageHero";
import type { TagFilterValues } from "../components/TagFilters";
import type { TagStatus } from "../types/tag";
import { aperamTokens } from "../theme/aperamTheme";

const useStyles = makeStyles({
  center: {
    display: "flex",
    justifyContent: "center",
    paddingTop: tokens.spacingVerticalXXL,
  },
  empty: {
    display: "flex",
    justifyContent: "center",
    paddingTop: tokens.spacingVerticalXXL,
    color: aperamTokens.steel500,
  },
  createBtn: {
    fontFamily: aperamTokens.displayFont,
    fontWeight: 600,
    backgroundColor: aperamTokens.orange500,
    color: aperamTokens.white,
    border: `1px solid ${aperamTokens.orange600}`,
    boxShadow: "0 8px 18px -10px rgba(241, 81, 27, 0.7)",
    ":hover": {
      backgroundColor: aperamTokens.orange400,
      color: aperamTokens.white,
      border: `1px solid ${aperamTokens.orange500}`,
    },
    ":hover:active": {
      backgroundColor: aperamTokens.orange600,
      color: aperamTokens.white,
    },
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
      <PageHero
        title="Tags"
        subtitle="Browse, govern, and create industrial sensor tags across every site and line."
        actions={
          <Button
            appearance="primary"
            icon={<AddRegular />}
            className={styles.createBtn}
            onClick={() => navigate("/tags/new")}
          >
            Create Tag
          </Button>
        }
      />

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
