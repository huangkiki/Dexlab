"""Independent checks for small Genesis CUDA probe records."""
import argparse
import json
import math
from pathlib import Path


def vector(values):
    return isinstance(values, list) and len(values) == 3 and all(
        isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
        for value in values)


def score(record):
    case = record.get("case")
    if case not in ("reset", "isolation", "capacity", "overflow"):
        return {"passed": False, "reason": "Unknown case"}
    if case == "overflow":
        return {"passed": record.get("completed") is False and
                "Exceeding max number of candidate contact points" in record.get("expected_overflow", "")
                and "error" not in record}
    episodes = record.get("episodes", [])
    count = 1 if case == "reset" else 2
    bodies = 4 if case == "capacity" else 1
    complete = (record.get("completed") is True and record.get("num_envs") == count
                and len(episodes) == 2 and all(len(rows) == 20 for rows in episodes))
    if not complete:
        return {"passed": False, "complete": False}
    valid = True
    try:
        for rows in episodes:
            for row in rows:
                valid &= row["error_mask"] == [False] * count
                for field in ("pos", "force"):
                    valid &= len(row[field]) == bodies
                    for body in row[field]:
                        valid &= len(body) == count
                        for values in body:
                            if field == "force":
                                valid &= len(values) == 1
                                values = values[0]
                            valid &= vector(values)
        if not valid:
            return {"passed": False, "valid_observations": False}
        compared_envs = range(1) if case == "isolation" else range(count)
        unchanged = all(a[field][body][env] == b[field][body][env]
                        for a, b in zip(*episodes) for field in ("pos", "force")
                        for body in range(bodies) for env in compared_envs)
        targeted = case != "isolation" or (
            all(abs(row["pos"][0][1][0]) < 1e-10 for row in episodes[0]) and
            all(abs(row["pos"][0][1][0] - .1) < 1e-10 for row in episodes[1]))
    except (KeyError, IndexError, TypeError):
        return {"passed": False, "valid_observations": False}
    return {"passed": unchanged and targeted, "complete": True,
            "valid_observations": True, "unchanged": unchanged, "targeted": targeted}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    result = score(json.loads(args.record.read_text()))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
