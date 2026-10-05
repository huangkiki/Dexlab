"""Reproduce solver-tolerance diagnostics without running an engine."""

import argparse
import json
from pathlib import Path

from dexlab.contact_refinement import compare_archives
from report_refinement import run_details


def report(directory):
    pairs = []
    scores = {}
    for control in ("forward", "frictionless"):
        comparisons = []
        for grid in ("h2", "h8"):
            for left, right in (("base", "tight"), ("tight", "tighter")):
                comparisons.append((grid, left, grid, right, True))
        for level in ("base", "tight", "tighter"):
            comparisons.append(("h2", level, "h8", level, False))
        for first_grid, first_level, second_grid, second_level, varying in comparisons:
            first = f"superdex-dev-solver-{control}-{first_grid}-{first_level}"
            second = f"superdex-dev-solver-{control}-{second_grid}-{second_level}"
            comparison = compare_archives(
                directory / first, directory / second, varying_solver=varying
            )
            pairs.append({
                "control": control,
                "variable": "solver_tolerance" if varying else "timestep",
                "first": first,
                "second": second,
                **comparison,
            })
            for name, score in zip((first, second), comparison["physical_scores"]):
                scores[name] = score
    runs = []
    for name, score in sorted(scores.items()):
        try:
            runs.append(run_details(directory / name, score))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            runs.append({"id": name, "physical_score": score, "details_error": type(exc).__name__})
    return {
        "scope": "Native stopping-tolerance sensitivity; no physical-accuracy pass",
        "expected_pairs": 14,
        "comparable_pairs": sum(pair["comparable"] for pair in pairs),
        "complete_run_details": len(runs) == 12 and all("details_error" not in row for row in runs),
        "pairs": pairs,
        "runs": runs,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.directory.resolve()):
        parser.error("Report must be outside the original evidence directory")
    result = report(args.directory)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    complete = result["complete_run_details"] and result["comparable_pairs"] == 14
    raise SystemExit(0 if complete else 1)


if __name__ == "__main__":
    main()
