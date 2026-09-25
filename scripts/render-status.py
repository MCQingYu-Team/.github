#!/usr/bin/env python3
"""Append one uptime sample and render server-status.json + uptime.svg.

Called from .github/workflows/status.yml with one argument: up | down.
The history file lives on the status branch, so the strip accumulates over time.
"""

import json
import sys
from pathlib import Path

MAX_SAMPLES = 96  # 96 次采样 × 30 分钟 = 48 小时
SLOT_W = 3
SLOT_GAP = 1
BAR_H = 16
PAD_X = 8
PAD_Y = 4
LABEL_SPACE = 62
COLORS = {"up": "#2ea44f", "down": "#cf222e", "unknown": "#3a4166"}


def main() -> None:
    state = (sys.argv[1] if len(sys.argv) > 1 else "unknown").strip().lower()
    if state not in ("up", "down"):
        state = "unknown"

    history_path = Path("history.json")
    try:
        samples = json.loads(history_path.read_text() or '{"samples": []}').get("samples", [])
    except (OSError, ValueError):
        samples = []
    samples = [s if s in ("up", "down") else "unknown" for s in samples]
    samples = (samples + [state])[-MAX_SAMPLES:]

    Path("status-history.json").write_text(
        json.dumps({"samples": samples}, ensure_ascii=False, indent=2) + "\n"
    )

    up = samples.count("up")
    known = sum(1 for s in samples if s in ("up", "down"))
    rate = f"{up / known * 100:.1f}%" if known else "--"

    status = {
        "schemaVersion": 1,
        "label": "主服",
        "message": "在线" if state == "up" else "离线",
        "color": COLORS["up"] if state == "up" else COLORS["down"],
        "labelColor": "rgba(36,41,67,0.5)",
        "style": "flat-square",
    }
    Path("server-status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n")

    slots = ["unknown"] * (MAX_SAMPLES - len(samples)) + samples
    step = SLOT_W + SLOT_GAP
    bar_w = MAX_SAMPLES * step - SLOT_GAP
    width = bar_w + PAD_X * 2 + LABEL_SPACE
    height = BAR_H + PAD_Y * 2

    rects = "".join(
        f'<rect x="{PAD_X + i * step}" y="{PAD_Y}" width="{SLOT_W}" height="{BAR_H}" fill="{COLORS[s]}"/>'
        for i, s in enumerate(slots)
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="主服近 48 小时在线情况：{rate}">\n'
        f'  <rect width="{width}" height="{height}" fill="#242943"/>\n'
        f'  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" fill="none" '
        f'stroke="#3a4166" stroke-width="1"/>\n'
        f"  {rects}\n"
        f'  <text x="{width - PAD_X}" y="{height / 2 + 4}" text-anchor="end" '
        f'font-family="\'Source Sans Pro\',\'Segoe UI\',\'Microsoft YaHei\',sans-serif" '
        f'font-size="11" fill="#d4d4ff">{rate}</text>\n'
        f"</svg>\n"
    )
    Path("uptime.svg").write_text(svg)

    print(f"state={state} rate={rate} samples={len(samples)}")


if __name__ == "__main__":
    main()
