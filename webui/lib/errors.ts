// HTTP/error-body → a friendly Warning (ACD: pure Calculation; compose/run, adversarial #1). Maps the two
// api error shapes — FastAPI 422 `{detail:[{loc,msg,type}]}` (HTTPValidationError) and the ErrorModel
// `{code,message,details}` — to a human, non-crashing flag so a server rejection is surfaced, never thrown.

import type { Warning } from "@/lib/studio/types";

interface ValidationDetail {
  loc?: (string | number)[];
  msg?: string;
  type?: string;
}
interface ErrorBody {
  code?: string;
  message?: string;
  detail?: ValidationDetail[];
}

/** Friendlier copy for known machine codes; falls back to the server message otherwise. */
const CODE_MESSAGES: Record<string, string> = {
  untrusted_path: "That file path isn't allowed — conditioning media must be inside the trusted volume.",
  payload_too_large: "That file is too large for the public limits.",
  unsupported_media_type: "That media type isn't supported.",
  invalid_param: "One of the parameters is invalid for this mode.",
  invalid_input: "The request was invalid.",
  context_over_cap: "The prompt is too long for the current context limit.",
  empty_prompt: "Please enter a prompt.",
  bad_max_tokens: "The requested output length is out of range.",
};

export function friendlyError(status: number, body: unknown): Warning {
  const b = (body && typeof body === "object" ? body : {}) as ErrorBody;

  // FastAPI validation error: { detail: [{ loc, msg, type }] }
  if (Array.isArray(b.detail) && b.detail.length > 0) {
    const first = b.detail[0];
    const field = Array.isArray(first.loc) && first.loc.length > 0 ? first.loc[first.loc.length - 1] : undefined;
    const msg = first.msg ?? "Invalid input.";
    return { severity: "error", code: "invalid_input", message: field ? `${msg} (${field})` : msg };
  }

  // ErrorModel: { code, message, details }
  if (typeof b.code === "string") {
    return { severity: "error", code: b.code, message: CODE_MESSAGES[b.code] ?? b.message ?? "The request failed." };
  }
  if (typeof b.message === "string") {
    return { severity: "error", code: "error", message: b.message };
  }

  // Fallback by status.
  const message =
    status === 422 ? "The request was rejected as invalid."
    : status === 413 ? "The upload is too large."
    : status === 415 ? "That media type isn't supported."
    : status === 429 ? "The service is busy — please retry shortly."
    : status >= 500 ? "The server had a problem. Please try again."
    : "The request failed.";
  return { severity: "error", code: `http_${status}`, message };
}
