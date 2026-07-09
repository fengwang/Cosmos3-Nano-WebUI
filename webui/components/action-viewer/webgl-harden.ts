// WebGL context hardening (ACD: a Calculation over a gl object; NO three.js import → unit-testable without
// WebGL). Some drivers — including real GPU hardware (observed: Mesa/AMD Radeon on Linux, Chromium) as well
// as software/headless WebGL — return `null` from otherwise-optional GL queries, which crashes three.js init
// with "Cannot read properties of null (reading 'precision' / 'alpha' / 'indexOf' / '0')". `hardenWebGLContext`
// substitutes safe defaults ONLY when a query returns null (a no-op on conformant drivers), widening the
// viewer's hardware support. Refs: failure_arbiter.md FA-1.

/** The attributes the viewer creates its context with — also the fallback when `getContextAttributes()`
 *  returns null, since three.js reads `.alpha` etc. off it. */
export const CONTEXT_ATTRS: WebGLContextAttributes = {
  alpha: true,
  antialias: true,
  depth: true,
  stencil: true,
  premultipliedAlpha: true,
  preserveDrawingBuffer: true,
  powerPreference: "default",
  failIfMajorPerformanceCaveat: false,
};

/**
 * Patch the queries three.js dereferences without a null guard — `getShaderPrecisionFormat` (`.precision`),
 * `getContextAttributes` (`.alpha`), and the string/array `getParameter` values (VERSION → `.indexOf`,
 * SCISSOR_BOX/VIEWPORT → `Vector4.fromArray`→`[0]`) — plus the info-log queries — so a null result becomes a
 * safe default. Real (incl. numeric) values always pass through untouched; conformant drivers see no change.
 */
export function hardenWebGLContext(gl: WebGLRenderingContext | WebGL2RenderingContext): void {
  const precision = gl.getShaderPrecisionFormat.bind(gl);
  gl.getShaderPrecisionFormat = (shaderType, precisionType) =>
    precision(shaderType, precisionType) ?? ({ rangeMin: 127, rangeMax: 127, precision: 23 } as WebGLShaderPrecisionFormat);
  const programLog = gl.getProgramInfoLog.bind(gl);
  gl.getProgramInfoLog = (program) => programLog(program) ?? "";
  const shaderLog = gl.getShaderInfoLog.bind(gl);
  gl.getShaderInfoLog = (shader) => shaderLog(shader) ?? "";
  const contextAttrs = gl.getContextAttributes.bind(gl);
  gl.getContextAttributes = () => contextAttrs() ?? { ...CONTEXT_ATTRS };

  const isWebGL2 = typeof WebGL2RenderingContext !== "undefined" && gl instanceof WebGL2RenderingContext;
  const gl2 = gl as WebGL2RenderingContext; // for the WebGL2-only param enums (we create a WebGL2 context)
  const getParameter = gl.getParameter.bind(gl);
  gl.getParameter = (pname: GLenum) => {
    const value: unknown = getParameter(pname);
    if (value !== null) return value;
    const viewport = [0, 0, Math.max(gl.drawingBufferWidth, 1), Math.max(gl.drawingBufferHeight, 1)];
    switch (pname) {
      case gl.VERSION:
        return isWebGL2 ? "WebGL 2.0" : "WebGL 1.0";
      case gl.SHADING_LANGUAGE_VERSION:
        return isWebGL2 ? "WebGL GLSL ES 3.00" : "WebGL GLSL ES 1.0";
      case gl.VENDOR:
        return "Generic";
      case gl.RENDERER:
        return "Generic WebGL";
      case gl.SCISSOR_BOX:
      case gl.VIEWPORT:
        return viewport;
      case gl.MAX_TEXTURE_SIZE:
      case gl.MAX_CUBE_MAP_TEXTURE_SIZE:
        return 4096;
      case gl.MAX_COMBINED_TEXTURE_IMAGE_UNITS:
      case gl.MAX_TEXTURE_IMAGE_UNITS:
      case gl.MAX_VERTEX_TEXTURE_IMAGE_UNITS:
      case gl.MAX_VERTEX_ATTRIBS:
        return 16;
      case gl.MAX_VERTEX_UNIFORM_VECTORS:
      case gl.MAX_FRAGMENT_UNIFORM_VECTORS:
        return 1024;
      case gl.MAX_VARYING_VECTORS:
        return 30;
      case gl2.MAX_UNIFORM_BUFFER_BINDINGS:
        return 24;
      case gl2.MAX_SAMPLES:
        return 4;
      case gl.SAMPLES:
        return 0;
      case gl.IMPLEMENTATION_COLOR_READ_FORMAT:
        return gl.RGBA;
      case gl.IMPLEMENTATION_COLOR_READ_TYPE:
        return gl.UNSIGNED_BYTE;
      default:
        return value;
    }
  };
}
