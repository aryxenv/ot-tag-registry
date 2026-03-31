import { useState, useEffect } from "react";

export interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Generic data-fetching hook.
 *
 * @param url      Relative URL to fetch (e.g. "/api/tags")
 * @param enabled  When false the fetch is skipped (useful for conditional fetching)
 */
export function useApi<T>(url: string, enabled: boolean = true): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [fetchCount, setFetchCount] = useState(0);

  const refetch = () => {
    setFetchCount((c) => c + 1);
  };

  useEffect(() => {
    if (!enabled) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    const controller = new AbortController();

    const doFetch = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(url, { signal: controller.signal });

        if (!response.ok) {
          const body = await response.text();
          throw new Error(body || `Request failed with status ${response.status}`);
        }

        const json = (await response.json()) as T;

        if (!cancelled) {
          setData(json);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          if (err instanceof DOMException && err.name === "AbortError") {
            return;
          }
          setError(err instanceof Error ? err.message : "An unknown error occurred");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    doFetch();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [url, enabled, fetchCount]);

  return { data, loading, error, refetch };
}
