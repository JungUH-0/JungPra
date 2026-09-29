"""도구 교체 실험 — 파라미터는 고정하고 🟢 등급 도구만 바꾼다.

등록부(CHANGELOG)의 🟢 등급은 가중치와 무관해 자유롭게 갈아끼울 수 있다.
여기서 실제로 갈아끼워 보고 무엇이 나은지 숫자로 본다.

두 종류를 나눠 다룬다. **비용이 두 자릿수 차이 나기 때문이다.**

    마스크 도구   전처리를 바꾸므로 확산을 다시 돌려야 한다.  쌍당 수 분
    후처리 도구   확산 결과(raw 512)를 재활용한다.            쌍당 수 초

그래서 마스크 도구마다 한 번씩만 생성하고, 후처리 변형은 그 위에서 전부
repost() 로 만든다. 마스크 3종 × 후처리 6종을 전부 생성하면 18회지만
이 방식이면 3회다.

파라미터는 건드리지 않는다 — steps/cfg/control_strength/seed 모두 고정.

사용:
    python scripts/swap_tools.py \
        --objects F01 F07 --backgrounds W03 W05 \
        --mask-tools birefnet_hr deeplabv3 sam2
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cgiv2 import AnyDoorEngine, Compositor, Settings      # noqa: E402
from cgiv2 import prep                                      # noqa: E402
from cgiv2.evaluate import IdentityScorer                   # noqa: E402
from cgiv2.postproc import seam_score                       # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


#: 후처리 변형. (이름, Settings 에 덮어쓸 값)
#: 전부 raw 에서 재계산되므로 GPU 를 쓰지 않는다.
POST_VARIANTS = [
    ("none",          dict(blend_tool="none",           feather=0,  color_match=0.0)),
    ("feather6",      dict(blend_tool="feather",        feather=6,  color_match=0.0)),
    ("feather16",     dict(blend_tool="feather",        feather=16, color_match=0.0)),
    ("poisson",       dict(blend_tool="poisson",        feather=0,  color_match=0.0)),
    ("poisson_mixed", dict(blend_tool="poisson_mixed",  feather=0,  color_match=0.0)),
    ("lab0.3",        dict(blend_tool="feather", feather=6, color_match=0.3, color_tool="lab")),
    ("hist0.3",       dict(blend_tool="feather", feather=6, color_match=0.3, color_tool="hist")),
]


def pick(folder: Path, names):
    files = sorted(p for p in folder.glob("*")
                   if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    out = []
    for n in names:
        hit = next((p for p in files if p.stem.startswith(n)), None)
        if hit is None:
            raise FileNotFoundError(f"{folder} 에 '{n}' 없음")
        out.append(hit)
    return out


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
    ap.add_argument("--objects", nargs="+", required=True)
    ap.add_argument("--backgrounds", nargs="+", required=True)
    ap.add_argument("--mask-tools", nargs="+", default=["birefnet_hr"])
    ap.add_argument("--post", nargs="*", default=None,
                    help=f"후처리 변형 이름. 기본 전부: {[n for n, _ in POST_VARIANTS]}")
    ap.add_argument("--obj-dir", default="D:/JungPra/pythonpra/CGI/objects")
    ap.add_argument("--bg-dir", default="D:/JungPra/pythonpra/CGI/backgrounds")
    ap.add_argument("--out", default=str(root / "outputs" / "swap"))
    # 파라미터는 고정. 바꾸려면 명시해야 한다.
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--cfg", type=float, default=5.0)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--bg-width", type=int, default=1600)
    ap.add_argument("--obj-width", type=int, default=1200)
    ap.add_argument("--cy", type=float, default=0.62)
    ap.add_argument("--cx", type=float, default=0.5)
    ap.add_argument("--height", type=float, default=0.5)
    a = ap.parse_args()

    posts = [(n, d) for n, d in POST_VARIANTS if a.post is None or n in a.post]
    obj_files = pick(Path(a.obj_dir), a.objects)
    bg_files = pick(Path(a.bg_dir), a.backgrounds)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    n_gen = len(obj_files) * len(bg_files) * len(a.mask_tools)
    print(f"마스크 도구 {len(a.mask_tools)}종 × {len(obj_files)}객체 × "
          f"{len(bg_files)}배경 = {n_gen}회 생성")
    print(f"후처리 변형 {len(posts)}종은 raw 재활용 (추가 생성 없음)")
    print(f"파라미터 고정: steps={a.steps} cfg={a.cfg} "
          f"strength={a.strength} seed={a.seed}\n")

    print("모델 로딩...", flush=True)
    t0 = time.time()
    engine = AnyDoorEngine(P["anydoor_root"], P["ckpt"],
                           save_memory=cfg["engine"]["save_memory"],
                           device=cfg["engine"]["device"])
    comp = Compositor(engine, P["anydoor_root"])
    scorer = IdentityScorer(engine=engine)
    print(f"  {time.time()-t0:.1f}초\n")

    rows, t_start, done = [], time.time(), 0

    for tool in a.mask_tools:
        print(f"── 마스크 도구: {tool} ──", flush=True)
        from cgiv2.mask import get_masker
        masker = get_masker(tool, device=cfg["engine"]["device"])

        for op in obj_files:
            ref = load_rgb(op, a.obj_width)
            t_m = time.time()
            rm = masker.binary(ref)
            dt_m = time.time() - t_m

            area = rm.sum() / rm.size
            cnts, _ = cv2.findContours(rm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            areas = [cv2.contourArea(c) for c in cnts] or [0]
            conn = max(areas) / max(sum(areas), 1e-6)
            print(f"  {op.stem[:30]:30s} 마스크 {dt_m:5.1f}초 "
                  f"면적 {area:5.1%} 연결성 {conn:.2f}")

            md = out / f"mask_{tool}"
            md.mkdir(exist_ok=True)
            cv2.imwrite(str(md / f"{op.stem[:24]}_mask.png"), rm * 255)

            for bp in bg_files:
                bg = load_rgb(bp, a.bg_width)
                tar = prep.place_box(bg.shape, center=(a.cy, a.cx),
                                     height_ratio=a.height,
                                     aspect=prep.object_aspect(rm))
                key = f"{op.stem[:20]}__{bp.stem[:20]}"

                base = Settings(steps=a.steps, cfg=a.cfg,
                                control_strength=a.strength, seed=a.seed,
                                tar_crop_ratio=2.0, normalize_object=True,
                                mask_tool=tool)
                np.random.seed(a.seed)
                res = comp(ref, rm, bg, tar, base, keep_raw=True)
                done += 1
                if res.skipped:
                    print(f"    {key}  관문 탈락: {res.skipped}")
                    continue

                # 후처리 변형은 전부 raw 에서 — GPU 를 쓰지 않는다
                for pname, over in posts:
                    st = Settings(**{**base.__dict__, **over})
                    img = res.repost(bg, st)
                    pd = out / f"{tool}__{pname}"
                    pd.mkdir(exist_ok=True)
                    cv2.imwrite(str(pd / f"{key}.png"), img[:, :, ::-1])
                    rows.append({
                        "pair": key, "mask_tool": tool, "post": pname,
                        "mask_area": float(area), "mask_conn": float(conn),
                        "identity": scorer.score(ref, rm, img, tar),
                        "seam": seam_score(img, tar),
                    })

                el = time.time() - t_start
                eta = el / done * (n_gen - done)
                print(f"    {key}  후처리 {len(posts)}종 완료 "
                      f"({el/60:.1f}분 / 남은 {eta/60:.1f}분)")

    if not rows:
        print("결과 없음")
        return 1

    def agg(sel, k):
        v = np.array([r[k] for r in rows if sel(r)], np.float64)
        return float(v.mean()) if v.size else float("nan")

    rep = {"settings": vars(a), "rows": rows,
           "by_mask_tool": {t: {"identity": agg(lambda r, t=t: r["mask_tool"] == t, "identity"),
                                "seam": agg(lambda r, t=t: r["mask_tool"] == t, "seam"),
                                "mask_area": agg(lambda r, t=t: r["mask_tool"] == t, "mask_area"),
                                "mask_conn": agg(lambda r, t=t: r["mask_tool"] == t, "mask_conn")}
                            for t in a.mask_tools},
           "by_post": {p: {"identity": agg(lambda r, p=p: r["post"] == p, "identity"),
                           "seam": agg(lambda r, p=p: r["post"] == p, "seam")}
                       for p, _ in posts}}
    (out / "swap_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 66)
    print(f"{'마스크 도구':16s} {'면적':>8s} {'연결성':>8s} {'정체성':>9s} {'이음매':>9s}")
    print("-" * 66)
    for t, s in rep["by_mask_tool"].items():
        print(f"{t:16s} {s['mask_area']:8.1%} {s['mask_conn']:8.2f} "
              f"{s['identity']:9.4f} {s['seam']:9.2f}")

    print(f"\n{'후처리':16s} {'정체성':>9s} {'이음매':>9s}")
    print("-" * 40)
    for p, s in rep["by_post"].items():
        print(f"{p:16s} {s['identity']:9.4f} {s['seam']:9.2f}")

    print(f"\n보고서: {out / 'swap_report.json'}")
    print("정체성 절대값은 의미가 없다 — rescore.py 의 calibrate() 기준선과 함께 볼 것.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
