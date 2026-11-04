# Runs every evaluation script one after another and prints a pass/fail summary.
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Scripts to run, in order. Pass names to run a subset: python evalall.py task_completion
EVALUATIONS = [
    "task_completion",
    "answer_correctness",
    "tool_correctness",
    "argument_correctness",
    "plan_quality",
    "plan_adherence",
    "step_effiiciency",
]


def main(selected: list[str]) -> int:
    names = selected or EVALUATIONS
    unknown = [n for n in names if n not in EVALUATIONS]
    if unknown:
        print(f"Unknown evaluation(s): {', '.join(unknown)}")
        print(f"Available: {', '.join(EVALUATIONS)}")
        return 2

    results: dict[str, tuple[int, float]] = {}
    for name in names:
        print(f"\n{'=' * 80}\n▶ {name}\n{'=' * 80}", flush=True)
        start = time.time()
        # A separate process per script: each one runs its evaluation at import time.
        # The default 180s per-task budget is too short for a slow local judge model.
        env = {"DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE": "900", **os.environ}
        proc = subprocess.run(
            [sys.executable, str(HERE / f"{name}.py")], cwd=HERE.parent, env=env
        )
        results[name] = (proc.returncode, time.time() - start)

    print(f"\n{'=' * 80}\nSummary\n{'=' * 80}")
    for name, (code, seconds) in results.items():
        status = "ok" if code == 0 else f"crashed (exit {code})"
        print(f"  {name:<22} {status:<20} {seconds:6.1f}s")
    print("\n'ok' means the script finished. Check each table above for metric pass/fail.")
    return 0 if all(code == 0 for code, _ in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
