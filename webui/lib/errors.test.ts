import { describe, expect, it } from "vitest";

import { friendlyError } from "@/lib/errors";

describe("friendlyError", () => {
  it("maps a FastAPI 422 detail to a fielded message", () => {
    const w = friendlyError(422, { detail: [{ loc: ["body", "resolution"], msg: "value is not a valid resolution", type: "value_error" }] });
    expect(w.severity).toBe("error");
    expect(w.code).toBe("invalid_input");
    expect(w.message).toContain("resolution");
  });

  it("maps a known ErrorModel code to friendly copy", () => {
    expect(friendlyError(422, { code: "untrusted_path", message: "raw" }).message).toMatch(/trusted volume/);
  });

  it("falls back to the server message for an unknown code", () => {
    expect(friendlyError(400, { code: "weird", message: "specific server detail" }).message).toBe("specific server detail");
  });

  it("uses a bare message when there is no code", () => {
    expect(friendlyError(400, { message: "just a message" }).message).toBe("just a message");
  });

  it("falls back by status for null/garbage bodies", () => {
    expect(friendlyError(500, null).message).toMatch(/server had a problem/);
    expect(friendlyError(413, "nonsense").message).toMatch(/too large/);
  });
});
