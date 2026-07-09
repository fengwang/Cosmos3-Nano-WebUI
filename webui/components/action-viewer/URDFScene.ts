// The ONLY WebGL/three.js module in S10 (the impure ACD seam). An imperative scene object the React shell
// (`ActionViewer`) drives: mount → load(localUrl) → setJointValues/setOrientation per frame → render →
// dispose. All decision logic (pose, interpolation, sync) is pure and lives elsewhere. The URDF is loaded
// LOCAL-ONLY (no remote URL; no external meshes) — INV-1 + the security adversarial case. Refs: design D2.

import * as THREE from "three";
import URDFLoader from "urdf-loader";
import type { URDFRobot } from "urdf-loader";

import type { Quat } from "./interpolate";
import { isRemoteUrl } from "./url-guard";
import { CONTEXT_ATTRS, hardenWebGLContext } from "./webgl-harden";

export interface URDFScene {
  /** Load a LOCAL urdf path; resolves with the robot's joint + link names. Throws on a remote URL. */
  load(url: string): Promise<{ jointNames: string[]; linkNames: string[] }>;
  setJointValues(values: Record<string, number>): void;
  setOrientation(link: string, q: Quat): void;
  setSize(width: number, height: number): void;
  render(): void;
  /** True while a live, non-lost WebGL context is held (the headless render smoke asserts this). */
  hasContext(): boolean;
  dispose(): void;
}

/** Create a scene bound to a canvas. Throws if a WebGL context cannot be created (caller falls back). */
export function createURDFScene(canvas: HTMLCanvasElement): URDFScene {
  // Obtain the context ourselves so we can harden it against software/headless GL BEFORE three.js touches
  // it. preserveDrawingBuffer also lets the render smoke read back a non-blank frame deterministically.
  const gl = (canvas.getContext("webgl2", CONTEXT_ATTRS) ?? canvas.getContext("webgl", CONTEXT_ATTRS)) as
    | WebGL2RenderingContext
    | WebGLRenderingContext
    | null;
  if (!gl) throw new Error("WebGL is unavailable in this browser.");
  hardenWebGLContext(gl);
  const renderer = new THREE.WebGLRenderer({ canvas, context: gl, antialias: true, alpha: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1); // deterministic for headless screenshots
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, 1, 0.01, 100);
  camera.position.set(1.7, 1.3, 1.7);
  camera.lookAt(0, 0.7, 0);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x445566, 1.15));
  const dir = new THREE.DirectionalLight(0xffffff, 0.85);
  dir.position.set(2.5, 4, 3);
  scene.add(dir);
  scene.add(new THREE.GridHelper(2, 8, 0x6688aa, 0x334455));

  let robot: URDFRobot | null = null;
  let disposed = false;

  function setSize(width: number, height: number): void {
    if (disposed || width <= 0 || height <= 0) return;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }

  async function load(url: string): Promise<{ jointNames: string[]; linkNames: string[] }> {
    if (isRemoteUrl(url)) {
      throw new Error(`URDFScene: refusing a non-local URDF url (${url}); assets must be same-origin (INV-1)`);
    }
    const loader = new URDFLoader();
    loader.packages = {};
    // Primitive-only URDF: a mesh reference would be an unexpected external asset → fail loudly.
    loader.loadMeshCb = () => {
      throw new Error("URDFScene: external meshes are not allowed (the authored URDF is primitive-only)");
    };
    const loaded = await loader.loadAsync(url);
    if (disposed) return { jointNames: [], linkNames: [] };
    robot = loaded;
    robot.rotation.x = -Math.PI / 2; // URDF is Z-up; three.js is Y-up
    scene.add(robot);
    return { jointNames: Object.keys(robot.joints), linkNames: Object.keys(robot.links) };
  }

  function setJointValues(values: Record<string, number>): void {
    if (robot) robot.setJointValues(values);
  }

  function setOrientation(link: string, q: Quat): void {
    const obj = robot?.links[link];
    if (obj) obj.quaternion.set(q.x, q.y, q.z, q.w);
  }

  function render(): void {
    if (!disposed) renderer.render(scene, camera);
  }

  function hasContext(): boolean {
    if (disposed) return false;
    const gl = renderer.getContext();
    return gl != null && !gl.isContextLost();
  }

  function dispose(): void {
    if (disposed) return;
    disposed = true;
    scene.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      mesh.geometry?.dispose?.();
      const mat = mesh.material;
      if (Array.isArray(mat)) mat.forEach((m) => m.dispose());
      else (mat as THREE.Material | undefined)?.dispose?.();
    });
    renderer.dispose();
    renderer.forceContextLoss?.();
    robot = null;
  }

  return { load, setJointValues, setOrientation, setSize, render, hasContext, dispose };
}
