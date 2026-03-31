import { useState } from "react";
import {
  Title2,
  Spinner,
  Text,
  makeStyles,
  tokens,
} from "@fluentui/react-components";
import { useNavigate } from "react-router-dom";
import { useTags } from "../hooks/useTags";
import { useAssets } from "../hooks/useAssets";
import TagFilters from "../components/TagFilters";
import TagTable from "../components/TagTable";
import type { TagFilterValues } from "../components/TagFilters";
import type { TagStatus } from "../types/tag";

const useStyles = makeStyles({
  header: {
    display: "block",
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
  const [filters, setFilters] = useState<TagFilterValues>(initialFilters);

  const { assets, loading: assetsLoading } = useAssets();

  // Derive assetId from site/line/equipment selection
  const matchedAsset =
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
  if (matchedAsset) apiFilters.assetId = matchedAsset.id;
  if (filters.search) apiFilters.search = filters.search;

  const { tags, loading: tagsLoading } = useTags(apiFilters);

  const handleTagClick = (tagId: string) => {
    navigate(`/tags/${tagId}`);
  };

  return (
    <div>
      <Title2 className={styles.header}>Tags</Title2>
      <TagFilters filters={filters} onFiltersChange={setFilters} assets={assets} />

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
