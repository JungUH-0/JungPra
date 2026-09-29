"""얼굴 정체성 채점 — 저장된 결과에 대해. GPU 불필요.

DINOv2 지표는 인물 전체(옷·체형·자세)를 재느라 얼굴이 뭉개져도 0.88 이 나온다.
"내 사진을 넣는다" 가 목적이면 그 지표는 목적을 안 재고 있다.

여기서는 SFace 로 **얼굴만** 잰다. OpenCV 내장 API 라 추가 패키지가 없다.

기준선도 같이 잡는다. 절대값은 의미가 없고, 아래 셋과 비교해야 읽힌다.

    자기 자신           참조 얼굴 vs 참조 얼굴 (좌우반전)   → 상한
    다른 사람           참조끼리 교차                       → 바닥
    OpenCV 권장 임계값  0.363                               → 같은 사람 판정선

사용:
    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/face_score.py
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cgiv2.evaluate import FaceScorer      # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_rgb(p: Path, max_w: int | None = None):
    img = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)
    if max_w and img.shape[1] > max_w:
        h = int(img.shape[0] * max_w / img.shape[1])
        img = cv2.resize(img, (max_w, h), interpolation=cv2.INTER_AREA)
    return img


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(root / "outputs"))
    ap.add_argument("--obj-dir", default="D:/JungPra/pythonpra/CGI/objects")
    ap.add_argument("--mask-dir", default=str(root / "work" / "masks"))
    ap.add_argument("--models", default=str(root / "work" / "models"))
    ap.add_argument("--obj-width", type=int, default=1200)
    a = ap.parse_args()

    md = Path(a.models)
    scorer = FaceScorer(md / "face_detection_yunet_2023mar.onnx",
                        md / "face_recognition_sface_2021dec.onnx")

    # ── 참조 ────────────────────────────────────────────────────────
    refs: dict[str, np.ndarray] = {}
    for mp in sorted(Path(a.mask_dir).glob("*.png")):
        if mp.stem.endswith("_alpha"):
            continue
        ip = next((q for q in Path(a.obj_dir).glob(f"{mp.stem}.*")
                   if q.suffix.lower() in {".jpg", ".jpeg", ".png"}), None)
        if ip:
            refs[mp.stem[:24]] = load_rgb(ip, a.obj_width)

    print(f"{'참조':26s} {'얼굴 높이':>10s}")
    print("-" * 40)
    ref_emb = {}
    for k, img in refs.items():
        px = scorer.face_px(img)
        ref_emb[k] = scorer.embed(img)
        print(f"{k:26s} {('%.0f px' % px) if px else '검출 실패':>10s}")

    # ── 기준선 ──────────────────────────────────────────────────────
    print("\n기준선")
    same = []
    for k, img in refs.items():
        e = scorer.embed(img[:, ::-1].copy())
        if e is not None and ref_emb.get(k) is not None:
            v = ref_emb[k]
            same.append(float(np.dot(v, e) / (np.linalg.norm(v) * np.linalg.norm(e))))
    diff = []
    for x, y in itertools.combinations([k for k in refs if ref_emb.get(k) is not None], 2):
        u, v = ref_emb[x], ref_emb[y]
        diff.append(float(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))))

    hi = float(np.mean(same)) if same else float("nan")
    lo = float(np.mean(diff)) if diff else float("nan")
    print(f"  자기 자신 (좌우반전)  {hi:.4f}   ← 상한")
    print(f"  다른 사람             {lo:.4f}   ← 바닥  (n={len(diff)})")
    print(f"  OpenCV 같은 사람 선   {FaceScorer.SAME_PERSON:.3f}")

    # ── 결과 채점 ───────────────────────────────────────────────────
    d_any, d_v2 = Path(a.out) / "anydoor", Path(a.out) / "cgiv2"
    pairs = sorted(p.stem for p in d_v2.glob("*.png"))

    print(f"\n{'쌍':52s} {'원본':>9s} {'CGIv2':>9s} {'얼굴px':>8s}")
    print("-" * 84)
    rows, miss = [], 0
    for key in pairs:
        rk = key.split("__")[0]
        if ref_emb.get(rk) is None:
            continue
        fa, fv = d_any / f"{key}.png", d_v2 / f"{key}.png"
        if not (fa.exists() and fv.exists()):
            continue
        g_any, g_v2 = load_rgb(fa), load_rgb(fv)

        s_any = scorer.score(refs[rk], g_any)
        s_v2 = scorer.score(refs[rk], g_v2)
        px = scorer.face_px(g_v2)
        miss += (s_any is None) + (s_v2 is None)

        fmt = lambda x: f"{x:9.4f}" if x is not None else f"{'미검출':>9s}"   # noqa: E731
        print(f"{key:52s} {fmt(s_any)} {fmt(s_v2)} "
              f"{('%.0f' % px) if px else '—':>8s}")
        rows.append({"pair": key, "anydoor": s_any, "cgiv2": s_v2,
                     "gen_face_px": px})

    ok_any = [r["anydoor"] for r in rows if r["anydoor"] is not None]
    ok_v2 = [r["cgiv2"] for r in rows if r["cgiv2"] is not None]
    px_all = [r["gen_face_px"] for r in rows if r["gen_face_px"] is not None]

    rep = {
        "baseline": {"self_flipped": hi, "different_person": lo,
                     "opencv_same_person": FaceScorer.SAME_PERSON},
        "anydoor": {"mean": float(np.mean(ok_any)) if ok_any else None, "n": len(ok_any)},
        "cgiv2": {"mean": float(np.mean(ok_v2)) if ok_v2 else None, "n": len(ok_v2)},
        "gen_face_px_mean": float(np.mean(px_all)) if px_all else None,
        "detect_failures": miss,
        "rows": rows,
    }
    (Path(a.out) / "face_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    print("-" * 84)
    if ok_any and ok_v2:
        ma, mv = float(np.mean(ok_any)), float(np.mean(ok_v2))
        print(f"{'원본':10s} {ma:9.4f}   {'같은 사람' if ma >= FaceScorer.SAME_PERSON else '다른 사람'}")
        print(f"{'CGIv2':10s} {mv:9.4f}   {'같은 사람' if mv >= FaceScorer.SAME_PERSON else '다른 사람'}")
        print(f"\n판정선 {FaceScorer.SAME_PERSON:.3f} 대비  원본 {ma - FaceScorer.SAME_PERSON:+.4f} / "
              f"CGIv2 {mv - FaceScorer.SAME_PERSON:+.4f}")
    if px_all:
        print(f"생성물 얼굴 높이 평균 {np.mean(px_all):.0f} px")
    if miss:
        print(f"검출 실패 {miss}건 — 얼굴이 너무 작거나 형태가 무너진 것이다")
    print(f"\n보고서: {Path(a.out) / 'face_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
