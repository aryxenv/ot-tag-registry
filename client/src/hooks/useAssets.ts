import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "../api/client";
import { assetKeys } from "../api/queryKeys";
import type { Asset } from "../types/asset";

/**
 * Fetches the list of assets from the API.
 * Assets rarely change so we use a long staleTime.
 */
export function useAssets() {
  const { data, isPending, isFetching, error, refetch } = useQuery({
    queryKey: assetKeys.list(),
    queryFn: ({ signal }) => fetchApi<Asset[]>("/api/assets", { signal }),
    staleTime: 5 * 60_000,
  });

  return {
    assets: data ?? [],
    loading: isPending,
    refreshing: isFetching && !isPending,
    error: error?.message ?? null,
    refetch,
  };
}
