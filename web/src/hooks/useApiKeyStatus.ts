import { useQuery } from "@tanstack/react-query";
import { API_KEY_QUERY_KEY, settingsApi } from "@/lib/api-client";

export function useApiKeyStatus() {
  return useQuery({ queryKey: API_KEY_QUERY_KEY, queryFn: settingsApi.getApiKeyStatus });
}

/** True only once an Anthropic API key is configured AND connected -- the
 * precondition for any AI-assisted (Stage 3/4) processing. */
export function useApiKeyConfigured(): boolean {
  const { data } = useApiKeyStatus();
  return Boolean(data?.configured && data?.connected);
}
