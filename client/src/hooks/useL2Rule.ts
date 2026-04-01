import { useQuery } from "@tanstack/react-query";
import { l2RuleKeys } from "../api/queryKeys";
import { fetchApi, ApiError } from "../api/client";
import type { L2Rule } from "../types/rule";

/**
 * Fetch an L2 rule for a tag. Returns `null` when none exists (404).
 */
export function useL2Rule(tagId: string | undefined) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: l2RuleKeys.all(tagId!),
    queryFn: async ({ signal }) => {
      try {
        return await fetchApi<L2Rule>(`/api/tags/${tagId}/rules/l2`, { signal });
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
