import { useMutation } from "@tanstack/react-query";
import { translateText } from "../api/mutations";

export function useTranslate() {
  return useMutation({
    mutationFn: (text: string) => translateText(text),
  });
}
