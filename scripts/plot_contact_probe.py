"""Plot every development contact configuration, including failures."""

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1] / "docs/evidence/engine-qualification"


def main():
    report = ROOT / "contact-probes.json"
    rows = json.loads(report.read_text())["sweep_gpu"]
    if len(rows) != 6:
        raise ValueError("Expected all six frozen development configurations")
    plt.rcParams.update({"svg.hashsalt": "dexlab-contact-probe-v2", "font.size": 10})
    for zh in (False, True):
        with plt.rc_context({"font.family": "Noto Sans CJK SC" if zh else "DejaVu Sans"}):
            fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")
            depths = [1000 * max(0, .05 - r["metrics"]["minimum_center_height_m"]) for r in rows]
            colors = ["#2c66a4" if r["passed"] else "#b94b3c" for r in rows]
            ax.bar(range(6), depths, color=colors, width=.65)
            ax.axhline(5, color="#666666", linestyle="--", linewidth=1,
                       label="固定检查阈值：5 mm" if zh else "Fixed smoke limit: 5 mm")
            ax.set_xticks(range(6), [f"dt={r['timestep_s']*1000:g} ms\ntc={r['contact_time_constant_s']*1000:g} ms" for r in rows])
            for index, (depth, row) in enumerate(zip(depths, rows)):
                label = ("通过" if row["passed"] else "失败") if zh else ("pass" if row["passed"] else "fail")
                ax.text(index, depth + .5, f"{depth:.2f}\n{label}", ha="center", fontsize=9)
            ax.set_ylim(0, 27)
            ax.set_ylabel("球—平面最大几何侵入 (mm)" if zh else "Maximum sphere–plane intrusion (mm)")
            ax.set_title("接触参数对照：更小步长不保证更小侵入" if zh else "Contact parameter contrast: smaller steps do not guarantee less intrusion")
            ax.spines[["top", "right"]].set_visible(False)
            ax.legend(frameon=False)
            fig.text(.5, -.02,
                     "每组 32 份相同初态，2 秒；开发诊断，不是引擎精度或速度排名。" if zh else
                     "32 identical worlds per configuration, 2 s; development diagnostic, not an accuracy or speed ranking.",
                     ha="center", fontsize=9)
            suffix = ".zh-CN" if zh else ""
            fig.savefig(ROOT / f"contact-parameters{suffix}.svg", metadata={"Date": None}, bbox_inches="tight")
            fig.savefig(ROOT / f"contact-parameters{suffix}.png", dpi=150, bbox_inches="tight")
            svg = ROOT / f"contact-parameters{suffix}.svg"
            svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
            plt.close(fig)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    (ROOT / "plot-provenance.json").write_text(json.dumps({
        "input_sha256": digest(report), "generator_sha256": digest(Path(__file__)),
        "matplotlib": matplotlib.__version__,
        "figures": {p.name: digest(p) for p in sorted(ROOT.glob("contact-parameters.*"))},
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
