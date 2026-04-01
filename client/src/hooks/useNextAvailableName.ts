import { useQuery } from "@tanstack/react-query";
import { fetchNextAvailableName } from "../api/mutations";

/**
 * Debounced query that resolves the next available tag name for a given base.
 * Returns empty string when baseName is empty (query disabled).
 */
export function useNextAvailableName(baseName: string) {
  const { data, isFetching } = useQuery({
    queryKey: ["tag-names", "next", baseName],
    queryFn: () => fetchNextAvailableName(baseName),
    enabled: baseName.length > 0,
    staleTime: 10_000,
  });

  return {
    name: baseName ? (data?.name ?? "") : "",
    resolving: isFetching,
  };
}
