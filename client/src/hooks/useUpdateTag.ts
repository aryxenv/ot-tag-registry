import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateTag } from "../api/mutations";
import { tagKeys } from "../api/queryKeys";

export function useUpdateTag() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateTag,
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: tagKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tagKeys.detail(variables.id) });
    },
  });
}
