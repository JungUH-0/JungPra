"""객체 마스크 생성 — AnyDoor 가 비워둔 자리를 채운다.

AnyDoor 는 마스크를 만들지 않는다 (readme.md:111 — "사용자가 직접 표시하라").
iseg/ 는 거친 마스크를 정제할 뿐 빈손에서 만들지 못한다.

BiRefNet_HR-matting 으로 뽑는다. 2048 로 학습된 변종이라 가는 구조(가방 끈,
시계 줄)가 살아남을 확률이 높다. 끈이 끊기면 mask_score 가 0.90 아래로
떨어져 process_pairs 관문에서 탈락하므로 중요하다.

연속 알파도 같이 저장하지만 **파이프라인은 이진 마스크만 쓴다.**
process_pairs 가 어디서도 알파를 안 쓰고 전부 `> 128` 로 이진화하기 때문이다.
알파는 경계를 눈으로 확인할 때만 본다.

이 스크립트는 CGI venv 에서 돌린다 (transformers + timm 이 필요하다).

    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/make_masks.py \
        --src D:/JungPra/pythonpra/CGI/objects \
        --out work/masks --names F01 F07 F11
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cgiv2.mask import BiRefNetMasker, bridge_thin_parts   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def mask_score(mask: np.ndarray) -> float:
    """가장 큰 덩어리가 차지하는 비율. AnyDoor data_utils 와 같은 계산."""
    m = mask.astype(np.uint8)
    if m.sum() < 10:
        return 0.0
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    areas = [cv2.contourArea(c) for c in cnts]
    s = sum(areas)
    return float(max(areas) / s) if s > 0 else 0.0


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", default=str(root / "work" / "masks"))
    ap.add_argument("--names", nargs="*", default=None,
                    help="파일명 접두사. 없으면 전부")
    ap.add_argument("--save-alpha", action="store_true", help="연속 알파도 저장 (진단용)")
    ap.add_argument("--bridge", type=int, default=0,
                    help="끊긴 가는 부분을 이어붙일 반지름. 0 이면 안 함")
    ap.add_argument("--model", default="ZhengPeng7/BiRefNet_HR-matting")
    a = ap.parse_args()

    src, out = Path(a.src), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    files = sorted(p for p in src.glob("*")
                   if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if a.names:
        files = [p for p in files if any(p.stem.startswith(n) for n in a.names)]
    if not files:
        print(f"대상 없음: {src} (names={a.names})")
        return 1

    print(f"모델 로딩 {a.model} ...", flush=True)
    masker = BiRefNetMasker(model_name=a.model)
    print(f"  입력 해상도 {masker.size}\n")

    print(f"{'파일':38s} {'크기':>11s} {'면적':>7s} {'연결성':>7s}  판정")
    print("-" * 80)

    ok = 0
    for p in files:
        rgb = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)
        alpha = masker.alpha(rgb)
        m = (alpha > 0.5).astype(np.uint8)
        if a.bridge > 0:
            m = bridge_thin_parts(m, radius=a.bridge)

        H, W = m.shape
        area = m.sum() / (H * W)
        score = mask_score(m)

        cv2.imwrite(str(out / f"{p.stem}.png"), m * 255)
        if a.save_alpha:
            cv2.imwrite(str(out / f"{p.stem}_alpha.png"),
                        (np.clip(alpha, 0, 1) * 255).astype(np.uint8))

        # process_pairs 의 관문 기준
        bad = []
        if score <= 0.90:
            bad.append(f"조각남({score:.2f})")
        if not (0.01 < area < 0.64):
            bad.append(f"면적({area:.1%})")
        ok += not bad

        print(f"{p.stem:38s} {W:5d}x{H:<5d} {area:7.1%} {score:7.2f}  "
              f"{'통과' if not bad else '주의 ' + ' '.join(bad)}")

    print("-" * 80)
    print(f"{len(files)}장 저장 · 관문 통과 {ok}장 -> {out}")
    if ok < len(files):
        print("\n연결성이 낮으면 --bridge 3 부터 올려가며 최소값을 찾으십시오.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
