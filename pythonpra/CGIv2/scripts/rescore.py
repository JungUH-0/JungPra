"""저장된 결과를 다시 채점한다 — 모델 재생성 없이.

compare_runs.py 의 첫 실행은 정체성 지표가 틀린 채로 돌았다. DINOv2 의 CLS
토큰은 **장면 기술자**라, 배경을 지우지 않고 넣으면 정체성이 아니라 배경
유사도를 잰다. 실제로 같은 인물 F01 이 배경에 따라 이렇게 나왔다.

    콜로세움(석조)   0.051
    경복궁(단청)     0.259
    산토리니(흰 벽)  0.483   ← 크림색 스튜디오 배경과 비슷해서 높다

이미지는 정상이므로 다시 생성할 필요가 없다. PNG 만 다시 읽어 채점한다.

고친 점 둘:

    배경 제거   cutout() 으로 양쪽 다 흰 배경 정사각으로 만든다.
                process_pairs 가 참조를 다루는 방식과 같게 맞춘 것이다.
    실루엣      생성물은 배치 사각형이 아니라 BiRefNet 으로 다시 분할한다.
                사각형 안의 배경이 섞이면 그만큼 점수가 깎인다.

그리고 calibrate() 로 상한/바닥을 잡는다. **값 자체는 의미가 없다.**
같은 객체가 어디, 다른 객체가 어디인지 알아야 0.48 이 좋은 건지 판단된다.

CGI venv 에서 돌린다 (BiRefNet 에 transformers + timm 이 필요하다).

    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/rescore.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cgiv2 import prep                                  # noqa: E402
from cgiv2.evaluate import IdentityScorer, cutout       # noqa: E402
from cgiv2.postproc import seam_score                   # noqa: E402

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
    cfg = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    P = cfg["paths"]

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(root / "outputs"))
    ap.add_argument("--obj-dir", default="D:/JungPra/pythonpra/CGI/objects")
    ap.add_argument("--mask-dir", default=str(root / "work" / "masks"))
    ap.add_argument("--obj-width", type=int, default=1200)
    ap.add_argument("--bg-width", type=int, default=1600)
    ap.add_argument("--cy", type=float, default=0.62)
    ap.add_argument("--cx", type=float, default=0.5)
    ap.add_argument("--height", type=float, default=0.5)
    ap.add_argument("--no-segment", action="store_true",
                    help="BiRefNet 재분할 없이 배치 사각형으로만 채점")
    a = ap.parse_args()

    out = Path(a.out)
    d_any, d_v2 = out / "anydoor", out / "cgiv2"
    pairs = sorted(p.stem for p in d_v2.glob("*.png"))
    if not pairs:
        print(f"결과가 없습니다: {d_v2}")
        return 1
    print(f"{len(pairs)}쌍 재채점\n")

    # ── 참조 캐시 ───────────────────────────────────────────────────
    obj_dir, mask_dir = Path(a.obj_dir), Path(a.mask_dir)
    refs: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for mp in sorted(mask_dir.glob("*.png")):
        if mp.stem.endswith("_alpha"):
            continue
        ip = next((q for q in obj_dir.glob(f"{mp.stem}.*")
                   if q.suffix.lower() in {".jpg", ".jpeg", ".png"}), None)
        if ip is None:
            continue
        rgb = load_rgb(ip, a.obj_width)
        m = (cv2.imread(str(mp), cv2.IMREAD_GRAYSCALE) > 128).astype(np.uint8)
        if m.shape != rgb.shape[:2]:
            m = cv2.resize(m, (rgb.shape[1], rgb.shape[0]),
                           interpolation=cv2.INTER_NEAREST)
        refs[mp.stem[:24]] = (rgb, m)
    print(f"참조 {len(refs)}개 로드")

    # ── 모델 ────────────────────────────────────────────────────────
    print("DINOv2 로딩...", flush=True)
    scorer = IdentityScorer(dinov2_root=P["dinov2_root"], weight=P["dinov2_weight"])

    segment = None
    if not a.no_segment:
        print("BiRefNet 로딩...", flush=True)
        from cgiv2.mask import BiRefNetMasker
        masker = BiRefNetMasker()
        segment = lambda rgb: masker.binary(rgb)      # noqa: E731

    # ── 기준선 ──────────────────────────────────────────────────────
    print("\n지표 보정 중...", flush=True)
    cal = scorer.calibrate(list(refs.values()))
    hi = cal["same_object"]["mean"]
    lo = cal["different_object"]["mean"]
    print(f"  같은 객체(좌우반전쌍)  {hi:.4f}   ← 상한")
    print(f"  다른 객체              {lo:.4f} ± {cal['different_object']['std']:.4f}   ← 바닥")
    print(f"  유효 폭                {hi - lo:.4f}\n")

    # ── 재채점 ──────────────────────────────────────────────────────
    rows = []
    print(f"{'쌍':52s} {'원본':>8s} {'CGIv2':>8s} {'차이':>8s}")
    print("-" * 82)

    for key in pairs:
        ref_key = key.split("__")[0]
        if ref_key not in refs:
            print(f"{key:52s}  참조 못 찾음")
            continue
        ref, rm = refs[ref_key]

        fa, fv = d_any / f"{key}.png", d_v2 / f"{key}.png"
        if not (fa.exists() and fv.exists()):
            continue
        g_any, g_v2 = load_rgb(fa), load_rgb(fv)

        tar = prep.place_box(g_v2.shape, center=(a.cy, a.cx),
                             height_ratio=a.height,
                             aspect=prep.object_aspect(rm))

        s_any = scorer.score(ref, rm, g_any, tar, segment=segment)
        s_v2 = scorer.score(ref, rm, g_v2, tar, segment=segment)
        rows.append({
            "pair": key,
            "anydoor": {"identity": s_any, "seam": seam_score(g_any, tar)},
            "cgiv2": {"identity": s_v2, "seam": seam_score(g_v2, tar)},
        })
        print(f"{key:52s} {s_any:8.4f} {s_v2:8.4f} {s_v2 - s_any:+8.4f}")

    if not rows:
        print("채점된 쌍이 없습니다.")
        return 1

    def agg(side, k):
        v = np.array([r[side][k] for r in rows], np.float64)
        return {"mean": float(v.mean()), "std": float(v.std())}

    rep = {
        "calibration": cal,
        "segmented": segment is not None,
        "pairs": len(rows),
        "anydoor": {k: agg("anydoor", k) for k in ("identity", "seam")},
        "cgiv2": {k: agg("cgiv2", k) for k in ("identity", "seam")},
        "rows": rows,
    }
    (out / "rescore_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    print("-" * 82)
    print(f"{'':10s} {'정체성(↑)':>12s} {'이음매(↓)':>12s}   {'기준선 내 위치':>14s}")
    for k in ("anydoor", "cgiv2"):
        m = rep[k]["identity"]["mean"]
        pos = (m - lo) / max(hi - lo, 1e-6)
        print(f"{k:10s} {m:12.4f} {rep[k]['seam']['mean']:12.2f} {pos:14.1%}")

    d = rep["cgiv2"]["identity"]["mean"] - rep["anydoor"]["identity"]["mean"]
    print(f"\n차이 {d:+.4f}  (유효 폭 {hi - lo:.4f} 대비 {d / max(hi - lo, 1e-6):+.1%})")
    print(f"보고서: {out / 'rescore_report.json'}")
    print("\n'기준선 내 위치' 가 0% 면 다른 객체와 구분이 안 되는 것이고,")
    print("100% 면 같은 객체를 좌우반전한 정도로 닮은 것이다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
