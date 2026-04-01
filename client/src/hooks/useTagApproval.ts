import { useMutation, useQueryClient } from "@tanstack/react-query";
import { requestApproval, approveTag, rejectTag } from "../api/mutations";
import { tagKeys } from "../api/queryKeys";

export function useRequestApproval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: requestApproval,
    onSuccess: (_data, tagId) => {
      queryClient.invalidateQueries({ queryKey: tagKeys.detail(tagId) });
    },
  });
}

export function useApproveTag() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: approveTag,
    onSuccess: (_data, tagId) => {
      queryClient.invalidateQueries({ queryKey: tagKeys.detail(tagId) });
      queryClient.invalidateQueries({ queryKey: tagKeys.lists() });
    },
  });
}

export function useRejectTag() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: rejectTag,
    onSuccess: (_data, { tagId }) => {
      queryClient.invalidateQueries({ queryKey: tagKeys.detail(tagId) });
    },
  });
}
