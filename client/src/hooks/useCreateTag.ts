import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createTag } from "../api/mutations";
import { tagKeys } from "../api/queryKeys";

export function useCreateTag() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createTag,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tagKeys.lists() });
    },
  });
}
