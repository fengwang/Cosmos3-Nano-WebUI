"""Diffusers action engine (Session 4): enable FD/ID/policy on the quantized checkpoint by grafting the
base-model bf16 action adapters onto the quantized transformer (`action_gen=True`).

Separate from the frozen `diffusers_oracle` (whose generation behavior + equivalence band stay
byte-stable); this module *imports* the oracle's pure helpers and adds the action-specific graft loader
and the FD/ID/policy adapter. Refs: session_4/specs/{action-enablement,action-engine-adapter}.md.
"""
