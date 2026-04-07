import { useMutation } from "@tanstack/react-query";
import { autoFillTag } from "../api/mutations";

export function useAutoFill() {
  return useMutation({
    mutationFn: (query: string) => autoFillTag(query),
  });
}
