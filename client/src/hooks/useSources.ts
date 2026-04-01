import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "../api/client";
import { sourceKeys } from "../api/queryKeys";
import type { Source } from "../types/source";

export function useSources() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: sourceKeys.list(),
    queryFn: ({ signal }) => fetchApi<Source[]>("/api/sources", { signal }),
    staleTime: 5 * 60_000,
  });

  return {
    sources: data ?? [],
    loading: isPending,
    error: error?.message ?? null,
    refetch,
  };
}
