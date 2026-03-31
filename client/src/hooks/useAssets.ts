import { useApi } from "./useApi";
import type { Asset } from "../types/asset";

/**
 * Fetches the list of assets from the API.
 */
export function useAssets() {
  const { data, loading, error, refetch } = useApi<Asset[]>("/api/assets");

  return {
    assets: data ?? [],
    loading,
    error,
    refetch,
  };
}
