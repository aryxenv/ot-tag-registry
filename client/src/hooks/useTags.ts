import { useApi } from "./useApi";
import type { Tag, TagStatus } from "../types/tag";

export interface TagFilters {
  status?: TagStatus;
  assetId?: string;
  search?: string;
}

/**
 * Fetches tags from the API with optional filter parameters.
 *
 * Only non-empty filter values are included as query string params.
 */
export function useTags(filters: TagFilters = {}) {
  const params = new URLSearchParams();

  if (filters.status) {
    params.set("status", filters.status);
  }
  if (filters.assetId) {
    params.set("assetId", filters.assetId);
  }
  if (filters.search) {
    params.set("search", filters.search);
  }

  const query = params.toString();
  const url = query ? `/api/tags?${query}` : "/api/tags";

  const { data, loading, error, refetch } = useApi<Tag[]>(url);

  return {
    tags: data ?? [],
    loading,
    error,
    refetch,
  };
}
