import { useApi } from "./useApi";
import type { Tag } from "../types/tag";

export function useTag(id: string | undefined) {
  const { data, loading, error, refetch } = useApi<Tag>(
    id ? `/api/tags/${id}` : "",
    !!id
  );
  return { tag: data ?? null, loading, error, refetch };
}
