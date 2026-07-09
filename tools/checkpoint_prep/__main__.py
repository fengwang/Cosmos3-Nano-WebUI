"""CLI dispatch for checkpoint_prep.

    python -m checkpoint_prep mutate  --ckpt <dist_dir> --source <bf16_dir> [--no-backup] [--no-verify]
    python -m checkpoint_prep restore --ckpt <dist_dir>
    python -m checkpoint_prep probe   --ckpt <dist_dir> [--backup <path>] [--source <bf16_dir>]
    python -m checkpoint_prep snapshot --ckpt <dist_dir>
    python -m checkpoint_prep self-contained        --ckpt <dist_dir> --source <bf16_dir> [--no-verify]
    python -m checkpoint_prep verify-self-contained --ckpt <dist_dir> --source <bf16_dir>
"""
from __future__ import annotations

import argparse
import json
import sys

from checkpoint_prep.copy_shared import CopyError, make_self_contained, plan_copy, verify_copy
from checkpoint_prep.integrity_probe import probe_checkpoint, snapshot_facts
from checkpoint_prep.mutation import MutationError
from checkpoint_prep.rewrite import apply_mutation, restore_backup


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="checkpoint_prep", description="Cosmos3-Nano FP8 checkpoint prep (P6-S5)")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("mutate", help="append action tensors + restore BF16 lm_head")
    m.add_argument("--ckpt", required=True)
    m.add_argument("--source", required=True)
    m.add_argument("--no-backup", action="store_true")
    m.add_argument("--no-verify", action="store_true")

    r = sub.add_parser("restore", help="restore the pre-mutation checkpoint from *.s5-orig.bak")
    r.add_argument("--ckpt", required=True)

    pr = sub.add_parser("probe", help="run the integrity probe")
    pr.add_argument("--ckpt", required=True)
    pr.add_argument("--backup", default=None)
    pr.add_argument("--source", default=None)

    sn = sub.add_parser("snapshot", help="dump pre-mutation facts + per-tensor sha256")
    sn.add_argument("--ckpt", required=True)

    sc = sub.add_parser("self-contained",
                        help="copy shared serve-time files + BF16 reasoner bundle into the -dist dir")
    sc.add_argument("--ckpt", required=True)
    sc.add_argument("--source", required=True)
    sc.add_argument("--no-verify", action="store_true")

    vsc = sub.add_parser("verify-self-contained",
                         help="verify a -dist dir is self-contained vs the BF16 source (no execute)")
    vsc.add_argument("--ckpt", required=True)
    vsc.add_argument("--source", required=True)

    a = p.parse_args(argv)
    try:
        if a.cmd == "mutate":
            report = apply_mutation(a.ckpt, a.source, backup=not a.no_backup, verify=not a.no_verify)
            print(json.dumps(report, indent=2))
            return 0
        if a.cmd == "restore":
            print(json.dumps({"restored": restore_backup(a.ckpt)}, indent=2))
            return 0
        if a.cmd == "probe":
            rep = probe_checkpoint(a.ckpt, backup_st=a.backup, source_dir=a.source)
            print(json.dumps({"ok": rep.ok, "problems": rep.problems, "facts": rep.facts}, indent=2))
            return 0 if rep.ok else 1
        if a.cmd == "snapshot":
            print(json.dumps(snapshot_facts(a.ckpt), indent=2))
            return 0
        if a.cmd == "self-contained":
            rep = make_self_contained(a.ckpt, a.source, verify=not a.no_verify)
            print(json.dumps({"ok": rep.ok, "problems": rep.problems, "files": rep.files,
                              "facts": rep.facts}, indent=2))
            return 0 if rep.ok else 1
        if a.cmd == "verify-self-contained":
            plan = plan_copy(a.ckpt, a.source)
            rep = verify_copy(plan, write_provenance=False)
            print(json.dumps({"ok": rep.ok, "problems": rep.problems, "files": rep.files}, indent=2))
            return 0 if rep.ok else 1
    except (MutationError, CopyError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
