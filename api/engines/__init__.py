"""Engine plane adapters. `base` defines the EngineAdapter contract the equivalence
harness drives (INV-3); `diffusers_oracle` is the reference oracle (INV-2). Kept import-light
(no torch at package import) so the torch-free server/test loop can import the interface."""
