"""Readable static summaries of original normal plateaus and recorded pinch frames."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from PIL import Image
from visual_research import ROOT, read_bundle


def main():
    with Image.open(ROOT / "demos/cloth-folding/media/compliance-grasp.gif") as cloth:
        cloth.seek(cloth.n_frames // 2)
        cloth.convert("RGB").save(ROOT / "docs/evidence/visual/cloth-poster.png")
    posters = [
        Image.open(ROOT / f"docs/evidence/visual/pinch-dev-cap-{cap}.png")
        for cap in ("0.4", "0.8")
    ]
    combined = Image.new(
        "RGB", (sum(p.width for p in posters), max(p.height for p in posters))
    )
    offset = 0
    for poster in posters:
        combined.paste(poster, (offset, 0))
        offset += poster.width
        poster.close()
    combined.save(ROOT / "docs/evidence/visual/pinch-summary.png")
    data = read_bundle(ROOT / "docs/evidence/visual/normal-calibration.json.gz")
    font = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
    if not font.exists():
        raise RuntimeError("Install Noto Sans CJK for bilingual figure export")
    font_manager.fontManager.addfont(str(font))
    for language in ("zh", "en"):
        zh = language == "zh"
        with plt.rc_context(
            {
                "font.family": "Noto Sans CJK JP" if zh else "DejaVu Sans",
                "font.size": 12,
                "svg.hashsalt": "dexlab-visual-v1",
            }
        ):
            fig, ax = plt.subplots(figsize=(8.5, 4.5))
            target = np.array([0.0, 0.3])
            ax.plot(
                target,
                target * 20,
                "k--",
                label="合成目标：20 kN/m" if zh else "Synthetic target: 20 kN/m",
            )
            for i, series in enumerate(data["series"]):
                plateaus = series["score"]["metrics"]["plateaus"]
                x = [
                    p["indentation_mean_m"] * 1000 for p in plateaus if p["load_n"] > 0
                ]
                y = [p["contact_force_mean_n"] for p in plateaus if p["load_n"] > 0]
                labels = (
                    ["初始配置：约 80 kN/m", "校准配置：约 20 kN/m"]
                    if zh
                    else ["Initial: about 80 kN/m", "Calibrated: about 20 kN/m"]
                )
                ax.plot(
                    x,
                    y,
                    ["o-", "s--"][i],
                    color="#0072B2",
                    label=labels[i],
                    lw=2,
                )
            ax.set(
                xlabel="稳态压入量 (mm)" if zh else "Steady indentation (mm)",
                ylabel="法向接触力 (N)" if zh else "Normal contact force (N)",
                title="同一 MuJoCo 场景：参数改变有效响应"
                if zh
                else "Same MuJoCo fixture: parameters change effective response",
            )
            ax.grid(alpha=0.2)
            ax.legend(fontsize=10, loc="lower right")
            ax.set_xlim(left=0)
            ax.set_ylim(bottom=0)
            fig.text(
                0.5,
                0.015,
                "40 mm · 0.2 kg · 0.5 ms；历史协议，非真实材料标定"
                if zh
                else "40 mm · 0.2 kg · 0.5 ms; historical protocol, not real-material calibration",
                ha="center",
                fontsize=10,
            )
            fig.tight_layout(rect=(0, 0.05, 1, 1))
            for suffix in ("svg", "png"):
                fig.savefig(
                    ROOT / f"docs/evidence/visual/normal-summary.{language}.{suffix}",
                    dpi=160,
                    metadata={"Date": None} if suffix == "svg" else None,
                )
            plt.close(fig)
    # Matplotlib adds trailing spaces inside SVG path attributes. Keep generated
    # figures compatible with the repository's whitespace gate.
    for path in (ROOT / "docs/evidence/visual").glob("*.svg"):
        path.write_text(
            "\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n"
        )


if __name__ == "__main__":
    main()
