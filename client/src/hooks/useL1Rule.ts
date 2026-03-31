import { useState, useEffect } from "react";
import type { L1Rule } from "../types/rule";

export function useL1Rule(tagId: string | undefined) {
  const [rule, setRule] = useState<L1Rule | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fetchCount, setFetchCount] = useState(0);

  const refetch = () => setFetchCount((c) => c + 1);

  useEffect(() => {
    if (!tagId) {
      setRule(null);
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
        const res = await fetch(`/api/tags/${tagId}/rules/l1`, {
          signal: controller.signal,
        });

        if (res.status === 404) {
          if (!cancelled) setRule(null);
          return;
        }

        if (!res.ok) {
          const body = await res.text();
          throw new Error(body || `Request failed with status ${res.status}`);
        }

        const json = (await res.json()) as L1Rule;
        if (!cancelled) setRule(json);
      } catch (err: unknown) {
        if (!cancelled) {
          if (err instanceof DOMException && err.name === "AbortError") return;
          setError(err instanceof Error ? err.message : "Failed to load L1 rule");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    doFetch();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [tagId, fetchCount]);

  return { rule, loading, error, refetch };
}
