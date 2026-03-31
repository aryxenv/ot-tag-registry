import { useApi } from "./useApi";
import type { Source } from "../types/source";

export function useSources() {
  const { data, loading, error, refetch } = useApi<Source[]>("/api/sources");
  return { sources: data ?? [], loading, error, refetch };
}
