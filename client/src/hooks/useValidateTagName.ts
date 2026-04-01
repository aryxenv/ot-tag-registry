import { useMutation } from "@tanstack/react-query";
import { validateTagName } from "../api/mutations";

export function useValidateTagName() {
  return useMutation({
    mutationFn: validateTagName,
  });
}
