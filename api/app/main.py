"""App shell — Actions: assembly, lifespan, the startup hook. Mutation confined here.

The readiness gate is wired from the pure ``app.readiness`` Calculations; the only
mutable state (``ReadinessHolder``) lives at this edge. The startup hook is injectable
so tests drive the 503->200 transition deterministically. The api process holds zero
GPU tensors at steady state (INV-P2-2) — all GPU work is in subprocess workers.
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import FastAPI

from app.errors import install_error_handlers
from app.health import build_health_router
from app.jobs_router import build_jobs_router
from app.observability import build_metrics, register_collectors, render
from app.observability.instruments import MeteredOrchestrator, metered_work
from app.observability.middleware import MetricsMiddleware
from app.openapi_export import install_custom_openapi
from app.routes.action import build_action_router
from app.routes.generation import build_generation_router
from app.routes.metrics import build_metrics_router
from app.routes.reasoning import VllmReasonerStream, build_reasoning_router
from app.readiness import WarmupState, mark_warmed
from engines.vllm_omni.work import vllm_omni_work
from jobs.gen_client import work as gen_plane_work
from jobs.runner import JobRunner, Work, default_stub_work
from jobs.store import JobStore
from orchestrator.manager import Orchestrator
from orchestrator.planes import Plane
from orchestrator.residency import ResidencyId
from orchestrator.worker import PlaneWorker


class ReadinessHolder:
    """Edge-only mutable holder for the immutable WarmupState (the Action boundary)."""

    def __init__(self) -> None:
        self.state = WarmupState()


StartupFn = Callable[["ReadinessHolder"], Coroutine[Any, Any, None]]

_log = logging.getLogger("cosmos3.startup")


def configure_logging() -> None:
    """Route the ``cosmos3.*`` loggers to the container stdout at INFO (idempotent).

    uvicorn configures only its OWN loggers, so without this the plane-swap evict/load lines
    (`cosmos3.orchestrator` — the INV-P5-2 mutual-exclusion evidence required for AC-S4-3) and the
    job-lifecycle lines (`cosmos3.jobs`) never surface. Level is tunable via ``COSMOS3_LOG_LEVEL``.
    """
    logger = logging.getLogger("cosmos3")
    if not logger.handlers:
        handler = logging.StreamHandler()  # → stdout → `docker logs`
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.propagate = False  # avoid double emission via the root logger
    logger.setLevel(os.environ.get("COSMOS3_LOG_LEVEL", "INFO").upper())


async def default_warmup(holder: ReadinessHolder) -> None:
    """Mark the api process ready immediately — no model load, no VRAM (INV-P2-2)."""
    await asyncio.sleep(0)  # yield once; deterministic, no real work
    holder.state = mark_warmed(holder.state)


def load_edge_tokenizer():
    """Action: a CPU-only tokenizer from the trusted reasoner mount for the context-cap count (INV-6/D-8).

    Guarded: when ``transformers`` / the mount is unavailable (the torch-free host loop) or disabled via
    ``COSMOS3_REASONER_TOKENIZER=0``, returns ``None`` → the reasoning route falls back to a conservative
    char-based heuristic (vLLM's ``max_model_len`` is the defense-in-depth backstop). No VRAM is used.
    """
    if os.environ.get("COSMOS3_REASONER_TOKENIZER", "1") == "0":
        return None
    try:
        from engines.vllm.loader import ReasonerConfig
        from transformers import AutoTokenizer

        return AutoTokenizer.from_pretrained(ReasonerConfig.from_env().model_dir)
    except Exception as exc:  # noqa: BLE001 — mask at the shell; the heuristic keeps the cap gate working
        _log.info("edge tokenizer unavailable, using the char heuristic: %s", exc)
        return None


_GEN_ENGINES = frozenset({"vllm_omni", "diffusers"})


def _gen_engine() -> str:
    """The active generation engine: ``vllm_omni`` (S4 default, container) or ``diffusers`` (dormant).

    An unknown value fails fast — a typo must not silently boot the dormant subprocess plane (which
    would then error at runtime with no gen_worker socket)."""
    engine = os.environ.get("COSMOS3_GEN_ENGINE", "vllm_omni")
    if engine not in _GEN_ENGINES:
        raise ValueError(f"COSMOS3_GEN_ENGINE={engine!r} must be one of {sorted(_GEN_ENGINES)}")
    return engine


def _select_gen_work() -> Work:
    """The runner's generation ``work``, matched to ``_gen_engine()`` so the two seams stay consistent."""
    return vllm_omni_work if _gen_engine() == "vllm_omni" else gen_plane_work


def default_worker_factory(target: ResidencyId) -> PlaneWorker:
    """Action: the production plane-worker factory — reasoning subprocess / generation plane from env.

    Heavy-ish imports are deferred so ``app.main`` imports torch-free; the worker is only *constructed*
    here (it starts its subprocess/container on the orchestrator's first ``acquire``). Everything comes
    ONLY from operator-set env (INV-8) — never a request field. Tests inject a stub factory instead.

    S4: for GENERATION, ``COSMOS3_GEN_ENGINE=vllm_omni`` (default) returns a `ContainerPlaneWorker`
    (the vllm-omni container; ``evict``=stop → INV-P5-2); ``=diffusers`` returns the dormant
    subprocess `gen_worker`. The REASONING branch is unchanged (R-11).
    """
    from engines.vllm.loader import ReasonerConfig
    from orchestrator.planes import generation_spec, reasoning_spec
    from orchestrator.worker import SubprocessPlaneWorker

    if target.plane is Plane.REASONING:
        spec = reasoning_spec(
            ReasonerConfig.from_env(),
            vllm_bin=os.environ.get("COSMOS3_VLLM_BIN", "vllm"),
            port=int(os.environ.get("COSMOS3_VLLM_PORT", "8765")),
        )
        return SubprocessPlaneWorker(spec)

    if _gen_engine() == "vllm_omni":  # GENERATION via the single deployed vllm-omni container (S6)
        from engines.vllm_omni.endpoints import endpoint_for
        from orchestrator.container import ContainerPlaneWorker, DockerCliController
        from orchestrator.planes import container_generation_spec

        # A standalone deployment serves exactly one generation checkpoint (INV-3); the endpoint is fixed
        # from operator env, not a request label. The residency FSM still evicts generation before the
        # reasoner loads (INV-4) — that eviction is unchanged.
        ep = endpoint_for()
        return ContainerPlaneWorker(
            container_generation_spec(base_url=ep.base_url), DockerCliController(ep.container)
        )

    # GENERATION via the dormant diffusers subprocess worker (COSMOS3_GEN_ENGINE=diffusers): the single
    # deployed checkpoint dir (COSMOS3_MODEL_DIR), no per-label selection (INV-3).
    model_dir = os.environ.get("COSMOS3_MODEL_DIR", "/data/models/Cosmos3-Nano-FP8-Blockwise")
    spec = generation_spec(
        ready_file=os.environ.get("COSMOS3_GEN_READY_FILE", "/tmp/cosmos3_gen_ready"),
        model_dir=model_dir,
    )
    return SubprocessPlaneWorker(spec)


def create_app(
    warmup: StartupFn = default_warmup,
    *,
    store: JobStore | None = None,
    orchestrator: Orchestrator | None = None,
    job_work: Work = default_stub_work,
) -> FastAPI:
    """Build the FastAPI app. ``warmup``/``store``/``orchestrator``/``job_work`` are injectable for tests."""
    holder = ReadinessHolder()
    store = store or JobStore()
    # S11 observability: a per-app private registry (injected, no globals — mirrors the edge-state discipline).
    # The orchestrator is wrapped to time plane acquisition (model-load + swap); the job-work to time/count
    # each job; both delegate verbatim so the frozen FSM/runner behavior (INV-4/INV-5) is unchanged.
    metrics, registry = build_metrics()
    # Idle keep-warm: keep the resident plane warm 30 min (LX-S1) so a think-and-iterate pause
    # survives instead of paying a cold reload; COSMOS3_IDLE_TIMEOUT_SECONDS overrides, 0 = never evict.
    idle_timeout = float(os.environ.get("COSMOS3_IDLE_TIMEOUT_SECONDS", "1800"))
    # Generous plane-readiness ceiling for the vllm-omni container cold start (matches --init-timeout;
    # R-07). Harmless for the fast reasoning subprocess — wait_ready returns as soon as it is ready or
    # its process dies, never waiting out the ceiling.
    ready_timeout = float(os.environ.get("COSMOS3_PLANE_READY_TIMEOUT", "1800"))
    orchestrator = MeteredOrchestrator(
        orchestrator
        or Orchestrator(default_worker_factory, idle_timeout=idle_timeout, ready_timeout=ready_timeout),
        metrics,
    )
    register_collectors(registry, store, orchestrator)  # scrape-time gauges: job state + resident plane + GPU
    # One shared GPU lease (S7): the runner holds it per job, the reasoning stream for its duration —
    # so neither evicts the other's plane mid-flight (INV-4 serialization across the sync + async paths).
    gpu_lease = asyncio.Lock()
    runner = JobRunner(store, orchestrator, work=metered_work(job_work, metrics), gpu_lease=gpu_lease)

    @contextlib.asynccontextmanager
    async def lifespan(_app: FastAPI):
        task = asyncio.create_task(warmup(holder))
        runner.start()
        try:
            yield
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            await runner.stop()
            await orchestrator.evict_all()  # free the GPU slot on shutdown (INV-4)

    app = FastAPI(title="Cosmos3-Nano Serving API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(MetricsMiddleware, metrics=metrics)  # S11: outermost — times the full request (SSE-safe)
    app.state.readiness = holder
    app.state.jobs = store
    app.state.runner = runner
    app.state.orchestrator = orchestrator
    app.state.gpu_lease = gpu_lease
    app.state.metrics = metrics
    app.include_router(build_health_router(holder))
    # /v1/metrics: unauth like /v1/health/* (private-net only per INV-1); include_in_schema=False (no drift).
    app.include_router(build_metrics_router(lambda: render(registry)))
    app.include_router(build_jobs_router(store, runner, metrics))
    app.include_router(build_generation_router(store, runner, metrics))
    app.include_router(build_action_router(store, runner, metrics))
    from engines.vllm.context_cap import ContextCapConfig  # noqa: PLC0415 — torch-free; local for tidy imports

    app.include_router(
        build_reasoning_router(
            orchestrator, gpu_lease, stream=VllmReasonerStream(),
            cap=ContextCapConfig.from_env(), tokenizer=load_edge_tokenizer(),
        ),
    )
    install_error_handlers(app)
    install_custom_openapi(app)
    return app


# Production app: the runner's generation work is selected by COSMOS3_GEN_ENGINE — the vllm-omni
# async HTTP client (default) or the dormant diffusers IPC client. The resident plane does the
# inference (INV-4). Tests use create_app()'s default stub work or inject their own.
configure_logging()  # surface the cosmos3.* orchestrator/job logs in the container (AC-S4-3 swap evidence)
app = create_app(job_work=_select_gen_work())
