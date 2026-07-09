import { describe, expect, it } from "vitest";

import { DEMO_CHUNK, demoActionBody } from "./demoBody";

describe("demoActionBody (action-viewer demo body)", () => {
  it("builds the demo body shape the /v1/action route expects, with no checkpoint field (S6/FR-12)", () => {
    const body = demoActionBody("agibotworld");
    expect(body.domain_name).toBe("agibotworld");
    expect(body.chunk_size).toBe(DEMO_CHUNK);
    expect(body.resolution_tier).toBe(480);
    expect(body.view_point).toBe("ego_view");
    expect(body.seed).toBe(123);
    expect("checkpoint" in body).toBe(false);
  });
});
