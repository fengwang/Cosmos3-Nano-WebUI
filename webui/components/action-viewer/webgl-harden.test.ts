import { describe, expect, it } from "vitest";

import { hardenWebGLContext } from "./webgl-harden";

// Real WebGL constant values three.js queries — so the fake context behaves like a real one.
const E = {
  VERSION: 0x1f02,
  SHADING_LANGUAGE_VERSION: 0x8b8c,
  VENDOR: 0x1f00,
  RENDERER: 0x1f01,
  SCISSOR_BOX: 0x0c10,
  VIEWPORT: 0x0ba2,
  MAX_TEXTURE_SIZE: 0x0d33,
  MAX_CUBE_MAP_TEXTURE_SIZE: 0x851c,
  MAX_COMBINED_TEXTURE_IMAGE_UNITS: 0x8b4d,
  MAX_TEXTURE_IMAGE_UNITS: 0x8872,
  MAX_VERTEX_TEXTURE_IMAGE_UNITS: 0x8b4c,
  MAX_VERTEX_ATTRIBS: 0x8869,
  MAX_VERTEX_UNIFORM_VECTORS: 0x8dfb,
  MAX_FRAGMENT_UNIFORM_VECTORS: 0x8dfd,
  MAX_VARYING_VECTORS: 0x8dfc,
  MAX_UNIFORM_BUFFER_BINDINGS: 0x8a2f,
  MAX_SAMPLES: 0x8d57,
  SAMPLES: 0x80a9,
  IMPLEMENTATION_COLOR_READ_FORMAT: 0x8b9b,
  IMPLEMENTATION_COLOR_READ_TYPE: 0x8b9a,
  RGBA: 0x1908,
  UNSIGNED_BYTE: 0x1401,
};

/** A fake context whose queries return null — the observed Mesa/AMD (real hardware) + software-WebGL bug. */
function makeNullGl(getParam: (pname: number) => unknown = () => null): WebGL2RenderingContext {
  const gl = {
    ...E,
    drawingBufferWidth: 800,
    drawingBufferHeight: 600,
    getShaderPrecisionFormat: () => null,
    getProgramInfoLog: () => null,
    getShaderInfoLog: () => null,
    getContextAttributes: () => null,
    getParameter: getParam,
  };
  return gl as unknown as WebGL2RenderingContext;
}

describe("hardenWebGLContext (FA-1: drivers — incl. real Mesa/AMD hardware — that null GL queries)", () => {
  it("substitutes a non-null shader-precision format (the '.precision' crash)", () => {
    const gl = makeNullGl();
    hardenWebGLContext(gl);
    const p = gl.getShaderPrecisionFormat(35633, 36338);
    expect(p).not.toBeNull();
    expect(typeof p?.precision).toBe("number");
  });

  it("substitutes context attributes carrying alpha (the '.alpha' crash)", () => {
    const gl = makeNullGl();
    hardenWebGLContext(gl);
    expect(gl.getContextAttributes()?.alpha).toBe(true);
  });

  it("substitutes a parseable VERSION string (the '.indexOf' crash)", () => {
    const gl = makeNullGl();
    hardenWebGLContext(gl);
    const version = gl.getParameter(E.VERSION) as string;
    expect(typeof version).toBe("string");
    expect(version).toMatch(/WebGL/);
  });

  it("substitutes 4-length SCISSOR_BOX/VIEWPORT arrays (the Vector4.fromArray '[0]' crash)", () => {
    const gl = makeNullGl();
    hardenWebGLContext(gl);
    expect(gl.getParameter(E.SCISSOR_BOX)).toHaveLength(4);
    expect(gl.getParameter(E.VIEWPORT)).toHaveLength(4);
  });

  it("substitutes non-null info logs", () => {
    const gl = makeNullGl();
    hardenWebGLContext(gl);
    expect(gl.getProgramInfoLog({} as WebGLProgram)).toBe("");
    expect(gl.getShaderInfoLog({} as WebGLShader)).toBe("");
  });

  it("passes REAL (non-null) values through untouched — a no-op on conformant drivers", () => {
    const real = makeNullGl((pname) =>
      pname === E.VERSION ? "WebGL 2.0 (real driver)" : pname === E.MAX_TEXTURE_SIZE ? 16384 : 42,
    );
    hardenWebGLContext(real);
    expect(real.getParameter(E.VERSION)).toBe("WebGL 2.0 (real driver)");
    expect(real.getParameter(E.MAX_TEXTURE_SIZE)).toBe(16384);
    expect(real.getParameter(0x9999)).toBe(42); // unknown pname, real value → passthrough
  });
});
