# Capability: vllm-omni-docker-build

Source: `docs/session_1/proposal.md` (Modified Capabilities)

## MODIFIED Requirements

### Requirement: Public-Input Build
`deploy/vllm-omni.Dockerfile` MUST build a working vLLM-Omni image using
only publicly resolvable inputs. It MUST NOT depend on
`vllm/vllm-omni:cosmos3`, or any other private/prebuilt Cosmos3 image, as
its base or as a source of any layer.

#### Scenario: Build from a clean Docker state
WHEN `docker compose -f deploy/docker-compose.fp8.yml build vllm-omni` is
run
THEN the build exits 0
AND the resulting image's base layer IDs do not match any layer ID present
in the locally cached `vllm/vllm-omni:cosmos3` image.

#### Scenario: No cosmos3 prebuilt reference anywhere in the recipe
WHEN `deploy/vllm-omni.Dockerfile` and `deploy/docker-compose*.yml` are
inspected
THEN no `FROM`, `image:`, or `COPY --from=` line references
`vllm/vllm-omni:cosmos3` or any other cosmos3-branded prebuilt tag.

### Requirement: Build Toolchain Availability
The base image declared in `deploy/vllm-omni.Dockerfile` MUST provide (or be
given, via public apt packages) a working build toolchain sufficient to
install the vLLM-Omni fork from source. A `-runtime`-only CUDA base MUST NOT
be used for this purpose.

#### Scenario: Fork install step completes without a toolchain error
WHEN the fork's install step runs against the declared base image
THEN it completes without a missing-compiler, missing-`nvcc`, or
missing-build-toolchain error.

### Requirement: Immutable Fork Pin
`deploy/vllm-omni.Dockerfile` MUST install the `fengwang/vllm-omni` fork by
the immutable commit SHA `697035018b70cef76b974a909d23371a9984c3f2`, never
by a mutable branch or floating tag (INV-3).

#### Scenario: Install reference is a commit SHA
WHEN the Dockerfile's fork-install instruction is inspected
THEN the git reference used is the literal 40-character commit SHA
`697035018b70cef76b974a909d23371a9984c3f2`
AND no branch name (e.g. `main`) or tag name is used in its place.

### Requirement: No Baked Weights
The image built from `deploy/vllm-omni.Dockerfile` MUST NOT contain any
Cosmos3 checkpoint weight file. Checkpoints are mounted at runtime only
(INV-2).

#### Scenario: No Cosmos3 checkpoint files in the image
WHEN the built image's filesystem is scanned outside of the runtime mount
point (`/models/checkpoint`)
THEN no file matching the checkpoints' known weight file names
(`*.safetensors`, `diffusion_pytorch_model*`) is present.
