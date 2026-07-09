"""The vLLM reasoning plane (S5): a sibling engine to the generation `EngineAdapter`.

`context_cap` is a pure, torch-free validator (import-safe on the host loop); `loader`/`adapter`
defer all heavy imports (torch/vllm) into functions, and `coresidency` holds the single-GPU
contract the S6 orchestrator must honor. Refs: docs/session_5/.
"""
