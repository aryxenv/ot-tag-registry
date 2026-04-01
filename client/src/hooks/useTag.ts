import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "../api/client";
import { tagKeys } from "../api/queryKeys";
import type { Tag } from "../types/tag";

export function useTag(id: string | undefined) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: tagKeys.detail(id!),
    queryFn: ({ signal }) => fetchApi<Tag>(`/api/tags/${id}`, { signal }),
    enabled: !!id,
    staleTime: 30_000,
  });

  return {
    tag: data ?? null,
    loading: isPending && !!id,
    error: error?.message ?? null,
    refetch,
  };
}
