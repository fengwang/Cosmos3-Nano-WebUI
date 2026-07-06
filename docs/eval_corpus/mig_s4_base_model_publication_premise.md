# Eval Seed - MIG-S4 Base-Model Publication Premise (Verify, Don't Assume)

Session: MIG-S4
Caught by: deterministic probe evidence (refuted a design premise); classified Failure Arbiter FA-1
Severity caught: Medium (would-be: an incorrect "beta-limited, weights unavailable" claim in a public contract)

## Prompt Seed

During brainstorming, a single reachability check of a *guessed* base repo id
(`wfen/Cosmos3-Nano`, which 404s) led to the premise that the reasoner and
action/forward_dynamics modes were **unbacked** (no public BF16 base) and should be
marked beta-limited. A public setup contract that repeats this would tell users those
modes cannot be run and mis-attribute the reason.

## Inputs

- The checkpoint model cards' declared `base_model` field.
- HF reachability/layout of the *declared* base id, not only a convention-name guess.

## Expected Verifier Behavior

The verifier MUST derive the base id from evidence and check it, rather than assuming:

1. Read `HfApi.model_info(<checkpoint>).card_data['base_model']` → `nvidia/Cosmos3-Nano`.
2. Check reachability + gating + layout of that id: reachable, ungated, has `transformer/`
   and `vision_encoder/` → the BF16 base **is** public.
3. Conclude reasoning/action are publicly **backed**; the only residual limit is
   GPU-unverified runtime (`MIG-S8`). A 404 on a *convention* id (`wfen/Cosmos3-Nano`) is a
   naming drift (document the correct id), NOT a missing-weights beta limit.
4. Any doc that marks a mode "beta-limited (non-public base)" without checking the declared
   `base_model` id is wrong.

## Regression Command Shape

```bash
python3 - <<'PY'
from huggingface_hub import HfApi
api=HfApi()
base=api.model_info("wfen/Cosmos3-Nano-FP8-Blockwise").card_data.to_dict()["base_model"][0]
info=api.model_info(base); files=api.list_repo_files(base)
assert getattr(info,"gated",False) in (False,None), "declared base is gated"
assert any(f.startswith("transformer/") for f in files) and any(f.startswith("vision_encoder/") for f in files)
print(base, "public+ungated+has base layout -> reasoning/action are backed")
PY
```
