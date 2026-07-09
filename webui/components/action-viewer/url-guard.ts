// Pure URL guard (ACD: Calculation). Is a URDF/asset path remote (carries any `scheme://`)? INV-1 requires
// assets to be same-origin local; this is extracted so the guard is unit-testable without importing three.js.
const REMOTE_URL = /^[a-z][a-z0-9+.-]*:\/\//i;

/** True if `url` is an absolute remote URL (http(s)://, file://, ws://, …) rather than a local path. */
export function isRemoteUrl(url: string): boolean {
  return REMOTE_URL.test(url);
}
