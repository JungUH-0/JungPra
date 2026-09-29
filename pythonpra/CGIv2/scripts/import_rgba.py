"""알파 채널 PNG → (RGB 사진, 0/1 마스크) 두 파일. 모델 없음.

누끼 딴 상품 사진(배경 투명 PNG)을 파이프라인 규격으로 바꾼다.
    <이름>.png          RGB — 투명 부분은 흰색(255). AnyDoor 참조 규약과 같은 색
    masks/<이름>.png    0/255 마스크 — 알파 > 128

사용:
    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/import_rgba.py \
        D:/JungPra/pythonpra/CGI/AnyDoor/examples/TestDreamBooth/FG/02.png \
        --name B01_backpack-red-anydoor --out work/plan2/objects --mask-out work/plan2/masks
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cgiv2.mask import mask_from_rgba   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--name", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mask-out", required=True)
    a = ap.parse_args()

    rgb, m = mask_from_rgba(a.src)
    rgb = np.where(m[:, :, None].astype(bool), rgb, 255).astype(np.uint8)
    out, mout = Path(a.out), Path(a.mask_out)
    out.mkdir(parents=True, exist_ok=True)
    mout.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out / f"{a.name}.png"), rgb[:, :, ::-1])
    cv2.imwrite(str(mout / f"{a.name}.png"), m * 255)

    n, _, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    big = stats[1:, cv2.CC_STAT_AREA].max() if n > 1 else 0
    print(f"{a.name}: {rgb.shape[1]}x{rgb.shape[0]}  면적 {m.mean():.1%}  "
          f"덩어리 {n - 1}개 (최대 덩어리 {big / max(m.sum(), 1):.1%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
