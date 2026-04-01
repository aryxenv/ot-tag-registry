import type { TagFilters } from "../hooks/useTags";

export const tagKeys = {
  all: ["tags"] as const,
  lists: () => [...tagKeys.all, "list"] as const,
  list: (filters: TagFilters) => [...tagKeys.lists(), filters] as const,
  details: () => [...tagKeys.all, "detail"] as const,
  detail: (id: string) => [...tagKeys.details(), id] as const,
};

export const assetKeys = {
  all: ["assets"] as const,
  list: () => [...assetKeys.all, "list"] as const,
};

export const sourceKeys = {
  all: ["sources"] as const,
  list: () => [...sourceKeys.all, "list"] as const,
};

export const l1RuleKeys = {
  all: (tagId: string) => ["tags", tagId, "rules", "l1"] as const,
};

export const l2RuleKeys = {
  all: (tagId: string) => ["tags", tagId, "rules", "l2"] as const,
};
