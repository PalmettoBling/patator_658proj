#!/usr/bin/env python3
"""Simple mutation testing runner for tests/test_patator.py against src/patator/patator.py.

This intentionally uses a small set of text mutations and reports whether each
mutation is killed (tests fail) or survives (tests still pass).
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable


@dataclasses.dataclass
class Mutation:
    line_no: int
    original_line: str
    mutated_line: str
    rule: str


@dataclasses.dataclass
class MutationResult:
    mutation: Mutation
    status: str  # KILLED | SURVIVED | ERROR
    exit_code: int
    output: str
    timed_out: bool


MUTATION_RULES: list[tuple[str, str, str]] = [
    (" is not ", " is ", "replace is not -> is"),
    (" is ", " is not ", "replace is -> is not"),
    (" == ", " != ", "replace == -> !="),
    (" != ", " == ", "replace != -> =="),
    (" <= ", " < ", "replace <= -> <"),
    (" >= ", " > ", "replace >= -> >"),
    (" and ", " or ", "replace and -> or"),
    (" or ", " and ", "replace or -> and"),
    (" True", " False", "replace True -> False"),
    (" False", " True", "replace False -> True"),
]


def fail(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def ensure_pytest(python_exe: str) -> None:
    """Fail fast when pytest is unavailable.

    This avoids misclassifying infrastructure failures as killed mutants.
    """
    check = subprocess.run(
        [python_exe, "-c", "import pytest"],
        capture_output=True,
        text=True,
    )
    if check.returncode != 0:
        fail("pytest is required but not available in the selected Python environment.")


def gather_mutations(source_lines: list[str], limit: int) -> list[Mutation]:
    mutations: list[Mutation] = []

    for idx, line in enumerate(source_lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        for needle, replacement, rule in MUTATION_RULES:
            if needle in line:
                mutated = line.replace(needle, replacement, 1)
                if mutated != line:
                    mutations.append(
                        Mutation(
                            line_no=idx,
                            original_line=line,
                            mutated_line=mutated,
                            rule=rule,
                        )
                    )
                    if len(mutations) >= limit:
                        return mutations
                break

    return mutations


def run_cmd(cmd: list[str], cwd: Path, timeout_seconds: int) -> tuple[int, str, bool]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        return proc.returncode, output.strip(), False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        output = (stdout or "") + ("\n" + stderr if stderr else "")
        output = (output + "\n\n[mutation runner] timed out").strip()
        return 124, output, True


def prepare_workspace(src_root: Path, dst_root: Path) -> None:
    shutil.copytree(src_root / "src", dst_root / "src")
    shutil.copytree(src_root / "tests", dst_root / "tests")


def apply_mutation(path: Path, mutation: Mutation) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    lines[mutation.line_no - 1] = mutation.mutated_line
    path.write_text("".join(lines), encoding="utf-8")


def run_mutations(
    repo_root: Path,
    python_exe: str,
    mutations: Iterable[Mutation],
    timeout_seconds: int,
) -> list[MutationResult]:
    results: list[MutationResult] = []

    mutation_list = list(mutations)
    total = len(mutation_list)

    for i, mutation in enumerate(mutation_list, start=1):
        print(
            f"[{i}/{total}] line={mutation.line_no} rule={mutation.rule}",
            flush=True,
        )
        with tempfile.TemporaryDirectory(prefix="patator_mut_") as temp_dir:
            temp_root = Path(temp_dir)
            prepare_workspace(repo_root, temp_root)

            mut_file = temp_root / "src" / "patator" / "patator.py"
            apply_mutation(mut_file, mutation)

            code, output, timed_out = run_cmd(
                [python_exe, "-m", "pytest", "tests/test_patator.py", "-q"],
                cwd=temp_root,
                timeout_seconds=timeout_seconds,
            )

            if code == 0:
                status = "SURVIVED"
            else:
                status = "KILLED"

            results.append(
                MutationResult(
                    mutation=mutation,
                    status=status,
                    exit_code=code,
                    output=output,
                    timed_out=timed_out,
                )
            )

    return results


def build_report(results: list[MutationResult], limit: int, baseline_ok: bool, timeout_seconds: int) -> str:
    total = len(results)
    killed = sum(1 for r in results if r.status == "KILLED")
    survived = sum(1 for r in results if r.status == "SURVIVED")
    timeouts = sum(1 for r in results if r.timed_out)
    score = (killed / total * 100.0) if total else 0.0

    lines: list[str] = []
    lines.append("# Simple Mutation Testing Report")
    lines.append("")
    lines.append(f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"Baseline tests pass: {'yes' if baseline_ok else 'no'}")
    lines.append(f"Mutation limit: {limit}")
    lines.append(f"Per-mutant timeout: {timeout_seconds}s")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total mutants: {total}")
    lines.append(f"- Killed: {killed}")
    lines.append(f"- Survived: {survived}")
    lines.append(f"- Timed out (counted as killed): {timeouts}")
    lines.append(f"- Mutation score: {score:.2f}%")
    lines.append("")

    lines.append("## Detailed Results")
    lines.append("")
    lines.append("| # | Status | Line | Rule |")
    lines.append("|---:|---|---:|---|")
    for i, r in enumerate(results, start=1):
        lines.append(
            f"| {i} | {r.status} | {r.mutation.line_no} | {r.mutation.rule} |"
        )

    lines.append("")
    lines.append("## Survived Mutants")
    lines.append("")
    survivor_rows = [r for r in results if r.status == "SURVIVED"]
    if not survivor_rows:
        lines.append("None")
    else:
        for i, r in enumerate(survivor_rows, start=1):
            lines.append(f"{i}. Line {r.mutation.line_no} ({r.mutation.rule})")
            lines.append(f"   - Original: {r.mutation.original_line.rstrip()}")
            lines.append(f"   - Mutated:  {r.mutation.mutated_line.rstrip()}")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This is a simple text-mutation approach; it does not parse Python AST.")
    lines.append("- Surviving mutants indicate potential test blind spots or equivalent mutants.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run simple mutation testing.")
    parser.add_argument(
        "--limit",
        type=int,
        default=60,
        help="Maximum number of mutants to test (default: 60).",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable to use for test runs.",
    )
    parser.add_argument(
        "--report",
        default="mutation_report.md",
        help="Path to write the markdown report.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Per-mutant timeout in seconds (default: 20).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    source_path = repo_root / "src" / "patator" / "patator.py"

    if not source_path.exists():
        fail(f"Source file not found: {source_path}")

    ensure_pytest(args.python)

    with tempfile.TemporaryDirectory(prefix="patator_mut_base_") as temp_dir:
        temp_root = Path(temp_dir)
        prepare_workspace(repo_root, temp_root)
        baseline_code, baseline_output, _ = run_cmd(
            [args.python, "-m", "pytest", "tests/test_patator.py", "-q"],
            cwd=temp_root,
            timeout_seconds=max(args.timeout, 20),
        )

    if baseline_code != 0:
        fail(
            "Baseline test run failed. Mutation testing aborted.\n"
            + baseline_output
        )

    source_lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)
    mutations = gather_mutations(source_lines, max(args.limit, 1))

    if not mutations:
        fail("No mutation points found with the current simple rules.")

    results = run_mutations(repo_root, args.python, mutations, timeout_seconds=max(args.timeout, 1))
    report_text = build_report(results, args.limit, baseline_ok=True, timeout_seconds=max(args.timeout, 1))

    report_path = (repo_root / args.report).resolve()
    report_path.write_text(report_text, encoding="utf-8")

    total = len(results)
    killed = sum(1 for r in results if r.status == "KILLED")
    survived = sum(1 for r in results if r.status == "SURVIVED")
    score = (killed / total * 100.0) if total else 0.0

    print(f"Mutation testing complete. Total={total}, Killed={killed}, Survived={survived}, Score={score:.2f}%")
    print(f"Report written to: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
