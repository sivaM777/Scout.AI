import { NativeModules } from "react-native";

const DEFAULT_API_BASE_URL = "http://10.0.2.2:4000";

function normalizeUrl(value: string | undefined): string {
  if (!value) {
    return DEFAULT_API_BASE_URL;
  }

  return value.endsWith("/") ? value.slice(0, -1) : value;
}

export const API_BASE_URL = normalizeUrl(
  (NativeModules.AppConfig?.apiBaseUrl as string | undefined) ?? DEFAULT_API_BASE_URL,
);
