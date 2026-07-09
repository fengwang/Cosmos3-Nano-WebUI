import type { paths } from "./schema";

/** Every path the api exposes, from the frozen OpenAPI schema (schemas/openapi.json). */
export type ApiPath = keyof paths;

/** The same-origin BFF prefix. The browser never addresses the api directly (INV-1). */
export const API_PREFIX = "/api";

/** Build a same-origin URL for an api path (the path is type-checked against the schema). */
export function apiUrl(path: ApiPath, search = ""): string {
  return `${API_PREFIX}${path}${search}`;
}

/** Typed fetch over the BFF proxy; `path` is constrained to known api paths. */
export function apiFetch(path: ApiPath, init?: RequestInit, search = ""): Promise<Response> {
  return fetch(apiUrl(path, search), init);
}
