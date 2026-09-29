"""베이스라인 일괄 생성 + 격자 탐색 + 지표 집계.

이게 0단계다. 아무것도 개선하지 않은 상태로 먼저 돌려 **실패 유형을 숫자로**
만든다. 이 기준선이 없으면 이후의 모든 변경에 대해 "좀 나아진 것 같다" 까지만
말할 수 있다.

DINOv2 토큰 캐싱이 여기서 값을 한다. 객체 20 x 배경 20 = 400 회 생성인데,
참조가 같으면 토큰도 같으므로 1.1B 모델은 20 번만 돌면 된다.

사용:
    python scripts/run_batch.py                      # 기본 설정으로 전체
    python scripts/run_batch.py --grid               # config 의 격자 전체
    python scripts/run_batch.py --limit-objects 3 --limit-backgrounds 2
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cgiv2 import AnyDoorEngine, Compositor, Settings   # noqa: E402
from cgiv2 import prep                                   # noqa: E402
from cgiv2.evaluate import IdentityScorer, evaluate_one, summarize   # noqa: E402
from cgiv2.mask import load_mask                         # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_objects(P, limit):
    out = []
    for p in sorted(Path(P["objects"]).glob("*")):
        if p.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        mp = Path(P["masks"]) / f"{p.stem}.png"
        if not mp.exists():
            continue
        rgb = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)
        m = load_mask(mp)
        if m.shape != rgb.shape[:2]:
            m = cv2.resize(m, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_NEAREST)
        out.append((p.stem, rgb, m))
        if limit and len(out) >= limit:
            break
    return out


def load_backgrounds(P, limit):
    out = []
    for p in sorted(Path(P["backgrounds"]).glob("*")):
        if p.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        out.append((p.stem, cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)))
        if limit and len(out) >= limit:
            break
    return out


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cfg = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    P = cfg["paths"]

    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", action="store_true", help="config 의 grid 조합을 모두 돈다")
    ap.add_argument("--limit-objects", type=int, default=0)
    ap.add_argument("--limit-backgrounds", type=int, default=0)
    ap.add_argument("--no-save-images", action="store_true", help="지표만 집계")
    a = ap.parse_args()

    objects = load_objects(P, a.limit_objects)
    backgrounds = load_backgrounds(P, a.limit_backgrounds)
    if not objects or not backgrounds:
        print("객체 또는 배경이 없습니다. config.yaml 의 paths 를 확인하십시오.")
        return 1

    if a.grid:
        g = cfg["grid"]
        combos = [
            Settings(
                steps=cfg["sampling"]["steps"], cfg=c, control_strength=s,
                seed=cfg["sampling"]["seed"], shape_control=sc,
                tar_crop_ratio=cfg["prep"]["tar_crop_ratio"],
                normalize_object=cfg["prep"]["normalize_object"],
            )
            for c, s, sc in itertools.product(g["cfg"], g["control_strength"], g["shape_control"])
        ]
    else:
        combos = [Settings(
            steps=cfg["sampling"]["steps"], cfg=cfg["sampling"]["cfg"],
            control_strength=cfg["sampling"]["control_strength"],
            seed=cfg["sampling"]["seed"],
            shape_control=cfg["prep"]["shape_control"],
            tar_crop_ratio=cfg["prep"]["tar_crop_ratio"],
            normalize_object=cfg["prep"]["normalize_object"],
            feather=cfg["post"]["feather"], color_match=cfg["post"]["color_match"],
            shadow=cfg["post"]["shadow"],
        )]

    total = len(objects) * len(backgrounds) * len(combos)
    print(f"객체 {len(objects)} x 배경 {len(backgrounds)} x 설정 {len(combos)} = {total} 장\n")

    print("모델 로딩...", flush=True)
    t0 = time.time()
    engine = AnyDoorEngine(P["anydoor_root"], P["ckpt"],
                           save_memory=cfg["engine"]["save_memory"],
                           device=cfg["engine"]["device"])
    comp = Compositor(engine, P["anydoor_root"])
    scorer = IdentityScorer(engine=engine)
    print(f"  {time.time() - t0:.1f}초\n")

    out_dir = Path(P["out"])
    out_dir.mkdir(parents=True, exist_ok=True)

    rows, skipped = [], []
    t_start = time.time()
    done = 0

    for st in combos:
        tag = st.tag()
        for oname, ref, rm in objects:
            for bname, bg in backgrounds:
                tar = prep.place_box(bg.shape, center=(0.62, 0.5), height_ratio=0.45,
                                     aspect=prep.object_aspect(rm))
                res = comp(ref, rm, bg, tar, st)
                done += 1

                if res.skipped:
                    skipped.append({"object": oname, "background": bname,
                                    "reason": res.skipped})
                    print(f"[{done}/{total}] {oname} x {bname}  탈락: {res.skipped}")
                    continue

                met = evaluate_one(scorer, ref, rm, res.image, tar)
                met.update(object=oname, background=bname, setting=tag,
                           cfg=st.cfg, control_strength=st.control_strength,
                           shape_control=st.shape_control)
                rows.append(met)

                if not a.no_save_images:
                    d = out_dir / tag
                    d.mkdir(parents=True, exist_ok=True)
                    cv2.imwrite(str(d / f"{oname}__{bname}.png"), res.image[:, :, ::-1])

                el = time.time() - t_start
                eta = el / done * (total - done)
                print(f"[{done}/{total}] {oname} x {bname}  "
                      f"id={met['identity']:.3f} seam={met['seam']:.1f}  "
                      f"경과 {el/60:.1f}분 / 남은 {eta/60:.1f}분")

    # ── 집계 ────────────────────────────────────────────────────────
    report = {
        "total": total,
        "generated": len(rows),
        "skipped": len(skipped),
        "dinov2_calls_saved": max(0, len(rows) - engine.cache_size()),
        "elapsed_sec": round(time.time() - t_start, 1),
        "overall": summarize(rows),
        "by_setting": {
            t: summarize([r for r in rows if r["setting"] == t])
            for t in sorted({r["setting"] for r in rows})
        },
        "by_object": {
            o: summarize([r for r in rows if r["object"] == o])
            for o in sorted({r["object"] for r in rows})
        },
        "skipped_detail": skipped,
    }
    (out_dir / "baseline_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 70)
    print(f"생성 {len(rows)} / 탈락 {len(skipped)} / {report['elapsed_sec']/60:.1f}분")
    print(f"DINOv2 호출 절약: {report['dinov2_calls_saved']}회 "
          f"(캐시 {engine.cache_size()}개)")
    if len(combos) > 1:
        print(f"\n{'설정':28s} {'정체성':>8s} {'이음매':>8s}")
        print("-" * 48)
        for t, s in report["by_setting"].items():
            print(f"{t:28s} {s['identity']['mean']:8.3f} {s['seam']['mean']:8.1f}")
    print(f"\n보고서: {out_dir / 'baseline_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
