"""배치 점검 — 확산 없이 배경마다 자동 배치를 그려본다. CGI venv 전용.

확산은 쌍당 수 분이 걸린다. 배치가 틀렸는지 알려고 확산까지 돌릴 필요는
없다. 여기서는 지면(초록)·사람(파랑)·지평선(빨강)·제안 배치(노랑)만 그려
콘택트 시트로 모은다. 배치가 말이 되는 걸 확인한 뒤에 확산을 돌린다.

산출물 (work/placement/)
    <배경>_overlay.png     확인용 그림
    <배경>_tar.png         tar_mask — AnyDoor venv 가 그대로 읽는다
    <배경>_ground.png      지면 마스크
    placement.json         배경별 수치 전부
    sheet.png              콘택트 시트

사용:
    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/check_placement.py
    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/check_placement.py --only K02 W03 W05
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cgiv2 import prep, shadow                                # noqa: E402
from cgiv2.mask import load_mask                              # noqa: E402
from cgiv2.placement import (SceneAnalyzer, auto_place,        # noqa: E402
                             draw_overlay, fit_perspective)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_rgb(p: Path, max_w: int | None = None):
    img = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)
    if max_w and img.shape[1] > max_w:
        h = int(img.shape[0] * max_w / img.shape[1])
        img = cv2.resize(img, (max_w, h), interpolation=cv2.INTER_AREA)
    return img


def letterbox(img: np.ndarray, w: int, h: int) -> np.ndarray:
    s = min(w / img.shape[1], h / img.shape[0])
    r = cv2.resize(img, (int(img.shape[1] * s), int(img.shape[0] * s)),
                   interpolation=cv2.INTER_AREA)
    out = np.full((h, w, 3), 30, np.uint8)
    y, x = (h - r.shape[0]) // 2, (w - r.shape[1]) // 2
    out[y:y + r.shape[0], x:x + r.shape[1]] = r
    return out


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg-dir", default="D:/JungPra/pythonpra/CGI/backgrounds")
    ap.add_argument("--only", nargs="*", default=None, help="배경 접두사 (예: K02 W03)")
    ap.add_argument("--out", default=str(root / "work" / "placement"))
    ap.add_argument("--bg-width", type=int, default=1600)
    ap.add_argument("--aspect-from", default="F01_man-olive-sweater-cream_6150523",
                    help="work/masks/ 의 마스크로 인물 가로세로비를 정한다")
    ap.add_argument("--aspect", type=float, default=None, help="직접 지정 (우선)")
    ap.add_argument("--target", type=float, default=0.40, help="원하는 인물 키 / 배경 높이")
    ap.add_argument("--x", type=float, nargs="+", default=[1 / 3, 2 / 3],
                    help="가로 위치 후보 (0~1). 기본 삼등분선 — 더 가까운 쪽을 고른다")
    ap.add_argument("--det-threshold", type=float, default=0.7)
    ap.add_argument("--height-scale", type=float, default=1.0,
                    help="물건 실제 높이 / 사람 키 (2안 자동차 2026-09-26: 세단 1.45/1.70 ≈ 0.85)."
                         " 원근의 r 에 곱해 그 자리 사람 키 대신 물건 높이를 쓴다")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    if a.aspect is not None:
        aspect = a.aspect
    else:
        aspect = prep.object_aspect(load_mask(root / "work" / "masks" / f"{a.aspect_from}.png"))

    # 대소문자 구분 — 소문자 kr01/w01 옛 세트는 제외 (2026-09-22 오매칭 교훈)
    pat = re.compile(r"^[KW]\d\d_")
    files = sorted(p for p in Path(a.bg_dir).glob("*")
                   if p.suffix.lower() in {".jpg", ".jpeg", ".png"} and pat.match(p.stem))
    if a.only:
        files = [p for p in files if any(p.stem.startswith(n) for n in a.only)]
    if not files:
        print("대상 배경이 없습니다.")
        return 1

    print(f"배경 {len(files)}개 · 인물 가로세로비 {aspect:.3f} · 목표 키 {a.target:.0%} · x {a.x}")
    print("모델 로딩 (Mask2Former + DETR)...", flush=True)
    t0 = time.time()
    an = SceneAnalyzer(det_threshold=a.det_threshold)
    print(f"  {time.time()-t0:.1f}초\n")

    print(f"{'배경':28s} {'사람':>4s} {'방식':>10s} {'지평선':>7s} {'r':>5s} "
          f"{'키':>6s} {'면적':>7s} {'이동':>5s}  비고")
    print("-" * 96)

    rows, thumbs = [], []
    for bp in files:
        bg = load_rgb(bp, a.bg_width)
        H, W = bg.shape[:2]
        scene = an.analyze(bg)
        persp = fit_perspective(scene)
        # 물건 높이 = 그 자리 사람 키 × height_scale. 지평선 v0 는 그대로, 기울기만 줄인다
        obj_persp = dataclasses.replace(persp, r=persp.r * a.height_scale)
        mask, info = auto_place(scene, obj_persp, aspect,
                                target_height_ratio=a.target, x_ratios=tuple(a.x))

        key = bp.stem[:24]
        cv2.imwrite(str(out / f"{key}_ground.png"), scene.ground * 255)
        ov = draw_overlay(bg, scene, persp, mask, info)
        cv2.imwrite(str(out / f"{key}_overlay.png"), ov[:, :, ::-1])
        if mask is not None:
            cv2.imwrite(str(out / f"{key}_tar.png"), mask * 255)

        top = sorted(scene.labels_present.items(), key=lambda x: -x[1])[:4]
        # 해 — 기존 사람들의 그림자에서 읽는다 (2026-09-26). apply_post.py --shadow cast 가 쓴다.
        sun, sun_diag = shadow.estimate_sun(bg, scene.people, scene.ground)
        row = {"bg_file": bp.name, "key": key, "size": [W, H],
               "ground_ratio": float(scene.ground.mean()),
               "labels_top": top, **{k: v for k, v in info.items()},
               "sun": sun, "sun_why": sun_diag.get("why"),
               "sun_evidence": len(sun_diag.get("evidence", []))}
        rows.append(row)

        hr = info.get("height_ratio")
        note = info.get("error") or info.get("warn") or ""
        hr_s = f"{hr:.0%}" if hr is not None else "—"
        area_s = f"{info['area']:.1%}" if "area" in info else "—"
        snap_s = f"{info['snap_dist']:.2f}" if "snap_dist" in info else "—"
        sun_s = (f"해({sun['dir'][0]:+.2f},{sun['dir'][1]:+.2f})" if sun
                 else f"해없음({row['sun_evidence']})")
        print(f"{key:28s} {len(scene.people):4d} {persp.method:>10s} "
              f"{persp.v0/H:7.2f} {persp.r:5.2f} {hr_s:>6s} {area_s:>7s} {snap_s:>5s}  "
              f"{sun_s:16s} {note[:40]}")

        cell = letterbox(ov, 360, 480)
        cv2.putText(cell, key[:22], (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(cell, f"{persp.method} n={len(scene.people)}", (6, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        thumbs.append(cell)

    (out / "placement.json").write_text(
        json.dumps({"aspect": aspect, "target": a.target, "x": a.x,
                    "det_threshold": a.det_threshold, "height_scale": a.height_scale,
                    "rows": rows},
                   ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    cols = 5
    while len(thumbs) % cols:
        thumbs.append(np.full_like(thumbs[0], 30))
    sheet = cv2.vconcat([cv2.hconcat(thumbs[i:i + cols]) for i in range(0, len(thumbs), cols)])
    cv2.imwrite(str(out / "sheet.png"), sheet[:, :, ::-1])

    print(f"\n콘택트 시트: {out / 'sheet.png'}")
    print(f"수치: {out / 'placement.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
