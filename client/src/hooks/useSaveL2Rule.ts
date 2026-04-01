import { useMutation, useQueryClient } from "@tanstack/react-query";
import { saveL2Rule, deleteL2Rule } from "../api/mutations";
import { l2RuleKeys } from "../api/queryKeys";

export function useSaveL2Rule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: saveL2Rule,
    onSuccess: (_data, { tagId }) => {
      queryClient.invalidateQueries({ queryKey: l2RuleKeys.all(tagId) });
    },
  });
}

export function useDeleteL2Rule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteL2Rule,
    onSuccess: (_data, tagId) => {
      queryClient.invalidateQueries({ queryKey: l2RuleKeys.all(tagId) });
    },
  });
}
