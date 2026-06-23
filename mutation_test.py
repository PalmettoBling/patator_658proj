#!/usr/bin/env python3
"""Mutation testing for tests/test_patator.py against src/patator/patator.py."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import subprocess
import sys


@dataclass(frozen=True)
class Mutation:
    mid: str
    description: str
    target: str
    replacement: str


MUTATIONS = [
    Mutation(
        "M01",
        "Change bytes encoding from ISO-8859-1 to UTF-8",
        "return x.encode('ISO-8859-1', errors='ignore')",
        "return x.encode('utf-8', errors='ignore')",
    ),
    Mutation(
        "M02",
        "Change bytes decoding from ISO-8859-1 to UTF-8",
        "return x.decode('ISO-8859-1', errors='ignore')",
        "return x.decode('utf-8', errors='ignore')",
    ),
    Mutation(
        "M03",
        "Disable escaping behavior in repr23",
        "return repr(s.encode('latin1'))[1:]",
        "return s",
    ),
    Mutation(
        "M04",
        "Replace md5 helper with sha1",
        "return hashlib.md5(plain).hexdigest()",
        "return hashlib.sha1(plain).hexdigest()",
    ),
    Mutation(
        "M05",
        "Replace sha1 helper with md5",
        "return hashlib.sha1(plain).hexdigest()",
        "return hashlib.md5(plain).hexdigest()",
    ),
    Mutation(
        "M06",
        "Break time formatting divisor constants",
        "[(seconds,), 60, 60]",
        "[(seconds,), 24, 60]",
    ),
    Mutation(
        "M07",
        "Disable random mode branch in RangeIter",
        "if random:",
        "if False and random:",
    ),
    Mutation(
        "M08",
        "Return maxint instead of computed RangeIter length",
        "return self.size",
        "return maxint",
    ),
    Mutation(
        "M09",
        "Stop stripping CRLF in ppstr",
        "return s.rstrip('\\r\\n')",
        "return s",
    ),
    Mutation(
        "M10",
        "Break query splitting behavior",
        "pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]",
        "pairs = [s2 for s1 in qs.split(';') for s2 in s1.split('&')]",
    ),
    Mutation(
        "M11",
        "Relax FILE key matcher",
        "return map(int, re.findall(r'FILE(\\d)', value))",
        "return map(int, re.findall(r'FILE(\\w)', value))",
    ),
    Mutation(
        "M12",
        "Relax NET key matcher",
        "return map(int, re.findall(r'NET(\\d)', value))",
        "return map(int, re.findall(r'NET(\\w)', value))",
    ),
    Mutation(
        "M13",
        "Break COMBO key second capture matcher",
        "return [map(int, t) for t in re.findall(r'COMBO(\\d)(\\d)', value)]",
        "return [map(int, t) for t in re.findall(r'COMBO(\\d)(\\w)', value)]",
    ),
]


def run_tests(repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-q", "tests/test_patator.py"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=180,
    )


def summarize_output(stdout: str, stderr: str) -> str:
    lines = [line.strip() for line in (stdout + "\n" + stderr).splitlines() if line.strip()]
    if not lines:
        return "(no output)"
    if len(lines) == 1:
        return lines[0]
    return f"{lines[-2]} | {lines[-1]}"


def apply_mutation(source: str, mutation: Mutation) -> tuple[str, str | None]:
    count = source.count(mutation.target)
    if count != 1:
        return source, f"target occurrence count is {count}, expected 1"
    return source.replace(mutation.target, mutation.replacement, 1), None


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    target_file = repo_root / "src" / "patator" / "patator.py"
    report_file = repo_root / "mutation_report_test_patator.txt"

    original = target_file.read_text(encoding="utf-8")

    report_lines: list[str] = []
    report_lines.append("Mutation Testing Report")
    report_lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    report_lines.append(f"Target code: {target_file.relative_to(repo_root)}")
    report_lines.append("Target tests: tests/test_patator.py")
    report_lines.append("")

    baseline = run_tests(repo_root)
    baseline_summary = summarize_output(baseline.stdout, baseline.stderr)
    report_lines.append(f"Baseline return code: {baseline.returncode}")
    report_lines.append(f"Baseline summary: {baseline_summary}")
    report_lines.append("")

    if baseline.returncode != 0:
        report_lines.append("Baseline test run failed. Mutation run aborted.")
        report_file.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
        print(f"Baseline failed. See {report_file}")
        return 1

    killed = 0
    survived = 0
    errors = 0

    try:
        for m in MUTATIONS:
            mutated, apply_error = apply_mutation(original, m)
            if apply_error:
                errors += 1
                report_lines.append(f"{m.mid} ERROR   {m.description}")
                report_lines.append(f"  reason: {apply_error}")
                continue

            target_file.write_text(mutated, encoding="utf-8")
            result = run_tests(repo_root)
            summary = summarize_output(result.stdout, result.stderr)

            if result.returncode == 0:
                survived += 1
                status = "SURVIVED"
            else:
                killed += 1
                status = "KILLED"

            report_lines.append(f"{m.mid} {status:<8} {m.description}")
            report_lines.append(f"  return code: {result.returncode}")
            report_lines.append(f"  summary: {summary}")
    finally:
        target_file.write_text(original, encoding="utf-8")

    total = killed + survived + errors
    score = (killed / (killed + survived) * 100.0) if (killed + survived) else 0.0

    report_lines.append("")
    report_lines.append("Totals")
    report_lines.append(f"  total mutants: {total}")
    report_lines.append(f"  killed: {killed}")
    report_lines.append(f"  survived: {survived}")
    report_lines.append(f"  errors: {errors}")
    report_lines.append(f"  mutation score: {score:.1f}%")

    report_file.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Wrote report: {report_file}")
    print(f"Mutation score: {score:.1f}% ({killed} killed / {killed + survived} executed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
