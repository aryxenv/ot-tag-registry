import { useQuery } from "@tanstack/react-query";
import { l1RuleKeys } from "../api/queryKeys";
import { fetchApi, ApiError } from "../api/client";
import type { L1Rule } from "../types/rule";

/**
 * Fetch an L1 rule for a tag. Returns `null` when none exists (404).
 */
export function useL1Rule(tagId: string | undefined) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: l1RuleKeys.all(tagId!),
    queryFn: async ({ signal }) => {
      try {
        return await fetchApi<L1Rule>(`/api/tags/${tagId}/rules/l1`, { signal });
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return null;
        throw err;
      }
    },
    enabled: !!tagId,
    staleTime: 30_000,
  });

  return {
    rule: data ?? null,
    loading: isPending && !!tagId,
    error: error?.message ?? null,
    refetch,
  };
}
