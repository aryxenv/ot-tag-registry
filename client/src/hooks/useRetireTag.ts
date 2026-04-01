import { useMutation, useQueryClient } from "@tanstack/react-query";
import { retireTag } from "../api/mutations";
import { tagKeys } from "../api/queryKeys";

export function useRetireTag() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: retireTag,
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: tagKeys.all });
      queryClient.invalidateQueries({ queryKey: tagKeys.detail(id) });
    },
  });
}
