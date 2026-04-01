import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "../api/client";
import { tagKeys } from "../api/queryKeys";
import type { Tag, TagStatus } from "../types/tag";

export interface TagFilters {
  status?: TagStatus;
  assetId?: string;
  search?: string;
}

function buildTagsUrl(filters: TagFilters): string {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.assetId) params.set("assetId", filters.assetId);
  if (filters.search) params.set("search", filters.search);
  const query = params.toString();
  return query ? `/api/tags?${query}` : "/api/tags";
}

/**
 * Fetches tags from the API with optional filter parameters.
 */
export function useTags(filters: TagFilters = {}) {
  const { data, isPending, isFetching, error, refetch } = useQuery({
    queryKey: tagKeys.list(filters),
    queryFn: ({ signal }) => fetchApi<Tag[]>(buildTagsUrl(filters), { signal }),
    staleTime: 30_000,
  });

  return {
    tags: data ?? [],
    loading: isPending,
    refreshing: isFetching && !isPending,
    error: error?.message ?? null,
    refetch,
  };
}
