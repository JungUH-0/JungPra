"""관문 사전검사 — 모델을 하나도 안 쓴다. GPU 도 필요 없다.

process_pairs 맨 앞의 네 관문에 우리 객체가 걸리는지 미리 본다.

    mask_score(ref_mask) > 0.90            한 덩어리인가
    check_mask_area(ref_mask)              면적 1 ~ 64%
    check_mask_area(tar_mask)
    check_region_size(ref_mask, 0.10)      변의 10% 이상

학습 경로의 BaseDataset.__getitem__ 은 예외를 통째로 삼키고 무한 재시도한다.
탈락한 객체가 섞여 있으면 에러 없이 멈춘다. 그래서 먼저 본다.

normalize_object 를 적용한 전후를 같이 보여주므로, 시계를 얼마나 크롭해야
하는지 자동차에 여백을 얼마나 덧대야 하는지가 숫자로 나온다.

사용:
    python scripts/check_dataset.py
    python scripts/check_dataset.py --objects <dir> --masks <dir>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cgiv2 import prep                        # noqa: E402
from cgiv2.mask import load_mask              # noqa: E402
from cgiv2.pairs import PairBuilder           # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cfg = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))

    ap = argparse.ArgumentParser()
    ap.add_argument("--objects", default=cfg["paths"]["objects"])
    ap.add_argument("--masks", default=cfg["paths"]["masks"])
    ap.add_argument("--no-normalize", action="store_true")
    a = ap.parse_args()

    builder = PairBuilder(cfg["paths"]["anydoor_root"])
    obj_dir, mask_dir = Path(a.objects), Path(a.masks)

    files = sorted(p for p in obj_dir.glob("*") if p.suffix.lower() in {".jpg", ".png", ".jpeg"})
    if not files:
        print(f"이미지가 없습니다: {obj_dir}")
        return 1

    # 배치 마스크는 전형적인 크기로 하나 만들어 타깃 관문도 같이 본다.
    dummy_bg = (1200, 1600)

    print(f"{'파일':14s} {'면적':>7s} {'연결성':>7s} {'가로':>6s} {'세로':>6s}  {'판정':4s}  사유 / 정규화")
    print("-" * 92)

    ok, bad = [], []
    for p in files:
        img = cv2.imread(str(p))
        if img is None:
            continue
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        mp = mask_dir / f"{p.stem}.png"
        if not mp.exists():
            print(f"{p.stem:14s} {'—':>7s} {'—':>7s} {'—':>6s} {'—':>6s}  탈락  마스크 파일 없음")
            bad.append(p.stem)
            continue
        m = load_mask(mp)
        if m.shape != rgb.shape[:2]:
            m = cv2.resize(m, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_NEAREST)

        note = ""
        if not a.no_normalize:
            rgb, m, note = prep.normalize_object(rgb, m)

        if m.sum() == 0:
            print(f"{p.stem:14s} {'—':>7s} {'—':>7s} {'—':>6s} {'—':>6s}  탈락  빈 마스크")
            bad.append(p.stem)
            continue

        H, W = m.shape
        area = m.sum() / (H * W)
        score = builder.u.mask_score(m)
        ys, xs = np.nonzero(m)
        bw = (xs.max() - xs.min() + 1) / W
        bh = (ys.max() - ys.min() + 1) / H

        tar = prep.place_box(dummy_bg, center=(0.62, 0.5),
                             height_ratio=0.45, aspect=prep.object_aspect(m))
        reasons = builder.check_gates(m, tar)

        passed = not reasons
        (ok if passed else bad).append(p.stem)
        tail = " ".join(reasons) if reasons else note
        print(f"{p.stem:14s} {area:7.1%} {score:7.2f} {bw:6.0%} {bh:6.0%}  "
              f"{'통과' if passed else '탈락':4s}  {tail}")

    print("-" * 92)
    print(f"통과 {len(ok)}장 / 탈락 {len(bad)}장")
    if bad:
        print("탈락:", ", ".join(bad))
        print("\n대처:")
        print("  면적 하한   normalize_object 가 자동 크롭한다. 그래도 안 되면 원본을 더 타이트하게")
        print("  면적 상한   normalize_object 가 여백을 덧댄다")
        print("  연결성      mask.bridge_thin_parts(mask, radius=3) 으로 끈을 이어본다")
        print("  변 10%      물체가 프레임에서 너무 작다. 다시 촬영/수집이 답이다")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
