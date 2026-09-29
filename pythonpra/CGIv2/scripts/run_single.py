"""한 장 합성 — 파이프라인이 끝까지 도는지 확인한다.

사용:
    python scripts/run_single.py --object p01 --background kr01_gyeongbokgung
    python scripts/run_single.py --object p01 --background kr01_gyeongbokgung \
        --cfg 9 --strength 0.8 --feather 6
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cgiv2 import AnyDoorEngine, Compositor, Settings   # noqa: E402
from cgiv2 import prep                                   # noqa: E402
from cgiv2.mask import load_mask                         # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cfg = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    P = cfg["paths"]

    ap = argparse.ArgumentParser()
    ap.add_argument("--object", required=True, help="objects/ 안의 파일명 (확장자 제외)")
    ap.add_argument("--background", required=True, help="backgrounds/ 안의 파일명")
    ap.add_argument("--cfg", type=float, default=cfg["sampling"]["cfg"])
    ap.add_argument("--strength", type=float, default=cfg["sampling"]["control_strength"])
    ap.add_argument("--steps", type=int, default=cfg["sampling"]["steps"])
    ap.add_argument("--seed", type=int, default=cfg["sampling"]["seed"])
    ap.add_argument("--shape-control", action="store_true")
    ap.add_argument("--feather", type=int, default=cfg["post"]["feather"])
    ap.add_argument("--color-match", type=float, default=cfg["post"]["color_match"])
    ap.add_argument("--shadow", action="store_true")
    ap.add_argument("--cy", type=float, default=0.62, help="배치 중심 y (0~1)")
    ap.add_argument("--cx", type=float, default=0.5, help="배치 중심 x (0~1)")
    ap.add_argument("--height", type=float, default=0.45, help="배경 높이 대비 물체 높이")
    a = ap.parse_args()

    # ── 입력 ────────────────────────────────────────────────────────
    obj = next(Path(P["objects"]).glob(f"{a.object}.*"))
    bgp = next(Path(P["backgrounds"]).glob(f"{a.background}.*"))
    ref = cv2.cvtColor(cv2.imread(str(obj)), cv2.COLOR_BGR2RGB)
    rm = load_mask(Path(P["masks"]) / f"{a.object}.png")
    if rm.shape != ref.shape[:2]:
        rm = cv2.resize(rm, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_NEAREST)
    bg = cv2.cvtColor(cv2.imread(str(bgp)), cv2.COLOR_BGR2RGB)

    tar = prep.place_box(bg.shape, center=(a.cy, a.cx),
                         height_ratio=a.height, aspect=prep.object_aspect(rm))

    # ── 모델 ────────────────────────────────────────────────────────
    print("모델 로딩...", flush=True)
    t0 = time.time()
    engine = AnyDoorEngine(P["anydoor_root"], P["ckpt"],
                           save_memory=cfg["engine"]["save_memory"],
                           device=cfg["engine"]["device"])
    print(f"  {time.time() - t0:.1f}초")

    comp = Compositor(engine, P["anydoor_root"])
    st = Settings(
        steps=a.steps, cfg=a.cfg, control_strength=a.strength, seed=a.seed,
        shape_control=a.shape_control or cfg["prep"]["shape_control"],
        tar_crop_ratio=cfg["prep"]["tar_crop_ratio"],
        normalize_object=cfg["prep"]["normalize_object"],
        feather=a.feather, color_match=a.color_match,
        shadow=a.shadow or cfg["post"]["shadow"],
    )

    t0 = time.time()
    res = comp(ref, rm, bg, tar, st)
    dt = time.time() - t0

    for n in res.notes:
        print("  ", n)
    if res.skipped:
        print(f"\n관문 탈락: {res.skipped}")
        print("scripts/check_dataset.py 로 먼저 확인하십시오.")
        return 1

    # ── 저장 ────────────────────────────────────────────────────────
    out_dir = Path(P["out"])
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{a.object}__{a.background}__{st.tag()}.png"
    cv2.imwrite(str(out_dir / name), res.image[:, :, ::-1])

    h, w = bg.shape[:2]
    strip = cv2.hconcat([
        cv2.resize(ref, (int(w * 0.5), int(h * 0.5))),
        cv2.resize(bg, (int(w * 0.5), int(h * 0.5))),
        cv2.resize(res.image, (int(w * 0.5), int(h * 0.5))),
    ])
    cv2.imwrite(str(out_dir / f"cmp_{name}"), strip[:, :, ::-1])

    print(f"\n합성 {dt:.1f}초 · 피크 VRAM {engine.peak_vram_gib():.2f} GiB")
    print(f"저장: {out_dir / name}")
    print(f"비교: {out_dir / ('cmp_' + name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
