import { useMutation, useQueryClient } from "@tanstack/react-query";
import { saveL1Rule, deleteL1Rule } from "../api/mutations";
import { l1RuleKeys } from "../api/queryKeys";

export function useSaveL1Rule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: saveL1Rule,
    onSuccess: (_data, { tagId }) => {
      queryClient.invalidateQueries({ queryKey: l1RuleKeys.all(tagId) });
    },
  });
}

export function useDeleteL1Rule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteL1Rule,
    onSuccess: (_data, tagId) => {
      queryClient.invalidateQueries({ queryKey: l1RuleKeys.all(tagId) });
    },
  });
}
