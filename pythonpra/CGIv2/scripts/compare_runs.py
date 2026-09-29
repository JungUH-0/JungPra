"""AnyDoor 원본 경로 vs CGIv2 경로를 같은 조건으로 돌려 비교한다.

**모델은 한 번만 올린다.** 두 경로가 같은 가중치·같은 seed·같은 배치 마스크를
쓰므로, 차이는 전처리/후처리에서만 온다.

원본 경로는 흉내내지 않고 **run_inference.py 의 함수를 그대로 꺼내 쓴다.**
그 파일은 import 시점에 모델을 올리므로(모듈 최상위 코드), ast 로 함수 정의
둘만 뽑아 실행한다. 복사하면 원본과 어긋날 수 있어서 이렇게 한다.

비교되는 차이 셋:

    타깃 크롭   원본 expand_bbox 는 [1.5,3] 범위에서 np.random 으로 뽑는다.
                CGIv2 는 2.0 고정 — 그래야 격자 탐색 결과를 신뢰할 수 있다.
    패딩 센티넬 원본은 pad_value=-1 후 uint8 캐스팅 -> 255 -> "여기 생성해라".
                CGIv2 는 센티넬 2 를 쓴 뒤 -1 로 되돌린다.
                객체가 프레임 가장자리에 있을 때만 발현한다.
    되붙이기    원본은 pred[1:,:,:] 로 1px 밀린 뒤 5px 마진 하드 대입.
                CGIv2 는 밀지 않고 feather 로 섞는다.

그리고 CGIv2 쪽만 normalize_object 로 면적비를 관문 안쪽으로 민다.

사용:
    python scripts/compare_runs.py --objects F01 F07 F11 \
        --backgrounds K02 W03 W05
"""
from __future__ import annotations

import argparse
import ast
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
from cgiv2.evaluate import IdentityScorer, evaluate_one, summarize   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ── 원본 함수 추출 ──────────────────────────────────────────────────────
def load_original_funcs(anydoor_root: Path):
    """run_inference.py 에서 process_pairs 와 crop_back 만 꺼낸다.

    모듈을 import 하면 최상위에서 create_model + load_state_dict 가 돌아
    9.13GB 를 또 올린다. 함수 정의만 뽑아 실행하면 그게 없다.
    """
    src = (anydoor_root / "run_inference.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    want = {"process_pairs", "crop_back", "aug_data_mask"}
    picked = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in want]
    if len(picked) < 2:
        raise RuntimeError(f"원본 함수를 못 찾았습니다: {[n.name for n in picked]}")

    if str(anydoor_root) not in sys.path:
        sys.path.insert(0, str(anydoor_root))
    ns: dict = {}
    exec("import cv2, numpy as np, albumentations as A\n"
         "from datasets.data_utils import *\n", ns)
    exec(compile(ast.Module(body=picked, type_ignores=[]), "<anydoor_orig>", "exec"), ns)
    return ns["process_pairs"], ns["crop_back"]


def run_original(engine, pp, cb, ref, rm, bg, tar, *, steps, cfg, strength, seed):
    """AnyDoor 원본 경로. 1px 밀림까지 그대로 재현한다."""
    item = pp(ref, rm, bg, tar)
    pred = engine.sample(item, steps=steps, cfg=cfg,
                         control_strength=strength, seed=seed)
    pred = pred[1:, :, :]                      # ← 원본 run_inference.py:215
    return cb(pred, bg.copy(), item["extra_sizes"], item["tar_box_yyxx_crop"])


# ── 입출력 ──────────────────────────────────────────────────────────────
def pick(folder: Path, names, exts={".jpg", ".jpeg", ".png"}):
    files = sorted(p for p in folder.glob("*") if p.suffix.lower() in exts)
    out = []
    for n in names:
        hit = next((p for p in files if p.stem.startswith(n)), None)
        if hit is None:
            raise FileNotFoundError(f"{folder} 에 '{n}' 로 시작하는 파일이 없습니다")
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
    cfgf = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    P = cfgf["paths"]

    ap = argparse.ArgumentParser()
    ap.add_argument("--objects", nargs="+", required=True)
    ap.add_argument("--backgrounds", nargs="+", required=True)
    ap.add_argument("--obj-dir", default="D:/JungPra/pythonpra/CGI/objects")
    ap.add_argument("--bg-dir", default="D:/JungPra/pythonpra/CGI/backgrounds")
    ap.add_argument("--mask-dir", default=str(root / "work" / "masks"))
    ap.add_argument("--out", default=str(root / "outputs"))
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--cfg", type=float, default=5.0)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--feather", type=int, default=6)
    ap.add_argument("--bg-width", type=int, default=1600)
    ap.add_argument("--obj-width", type=int, default=1200)
    ap.add_argument("--cy", type=float, default=0.62)
    ap.add_argument("--cx", type=float, default=0.5)
    ap.add_argument("--height", type=float, default=0.5)
    a = ap.parse_args()

    obj_files = pick(Path(a.obj_dir), a.objects)
    bg_files = pick(Path(a.bg_dir), a.backgrounds)
    mask_dir = Path(a.mask_dir)

    out = Path(a.out)
    d_any, d_v2, d_cmp = out / "anydoor", out / "cgiv2", out / "compare"
    for d in (d_any, d_v2, d_cmp):
        d.mkdir(parents=True, exist_ok=True)

    print(f"객체 {len(obj_files)} x 배경 {len(bg_files)} = "
          f"{len(obj_files)*len(bg_files)}쌍 x 2경로\n")

    print("모델 로딩...", flush=True)
    t0 = time.time()
    engine = AnyDoorEngine(P["anydoor_root"], P["ckpt"],
                           save_memory=cfgf["engine"]["save_memory"],
                           device=cfgf["engine"]["device"])
    pp, cb = load_original_funcs(Path(P["anydoor_root"]))
    comp = Compositor(engine, P["anydoor_root"])
    scorer = IdentityScorer(engine=engine)
    print(f"  {time.time()-t0:.1f}초\n")

    st = Settings(steps=a.steps, cfg=a.cfg, control_strength=a.strength,
                  seed=a.seed, shape_control=False, tar_crop_ratio=2.0,
                  normalize_object=True, feather=a.feather,
                  color_match=0.0, shadow=False)

    rows, t_start, n = [], time.time(), 0
    total = len(obj_files) * len(bg_files)

    for op in obj_files:
        ref0 = load_rgb(op, a.obj_width)
        mp = mask_dir / f"{op.stem}.png"
        if not mp.exists():
            print(f"마스크 없음, 건너뜀: {mp.name}")
            continue
        rm0 = (cv2.imread(str(mp), cv2.IMREAD_GRAYSCALE) > 128).astype(np.uint8)
        if rm0.shape != ref0.shape[:2]:
            rm0 = cv2.resize(rm0, (ref0.shape[1], ref0.shape[0]),
                             interpolation=cv2.INTER_NEAREST)

        for bp in bg_files:
            bg = load_rgb(bp, a.bg_width)
            tar = prep.place_box(bg.shape, center=(a.cy, a.cx),
                                 height_ratio=a.height,
                                 aspect=prep.object_aspect(rm0))
            key = f"{op.stem[:24]}__{bp.stem[:24]}"
            n += 1

            # ① 원본 — expand_bbox 의 np.random 을 고정해 재실행 재현성을 준다
            np.random.seed(a.seed)
            g_any = run_original(engine, pp, cb, ref0, rm0, bg, tar,
                                 steps=a.steps, cfg=a.cfg,
                                 strength=a.strength, seed=a.seed)

            # ② CGIv2
            np.random.seed(a.seed)
            res = comp(ref0, rm0, bg, tar, st)
            if res.skipped:
                print(f"[{n}/{total}] {key}  CGIv2 관문 탈락: {res.skipped}")
                continue
            g_v2 = res.image

            cv2.imwrite(str(d_any / f"{key}.png"), g_any[:, :, ::-1])
            cv2.imwrite(str(d_v2 / f"{key}.png"), g_v2[:, :, ::-1])

            h = 540
            def thumb(x):
                return cv2.resize(x, (int(x.shape[1] * h / x.shape[0]), h))
            cv2.imwrite(str(d_cmp / f"{key}.png"),
                        cv2.hconcat([thumb(bg), thumb(g_any), thumb(g_v2)])[:, :, ::-1])

            m_any = evaluate_one(scorer, ref0, rm0, g_any, tar)
            m_v2 = evaluate_one(scorer, ref0, rm0, g_v2, tar)
            rows.append({"pair": key,
                         "anydoor": m_any, "cgiv2": m_v2,
                         "notes": res.notes})

            el = time.time() - t_start
            print(f"[{n}/{total}] {key}")
            print(f"        원본  id={m_any['identity']:.3f} seam={m_any['seam']:.1f}")
            print(f"        CGIv2 id={m_v2['identity']:.3f} seam={m_v2['seam']:.1f}"
                  f"   ({el/60:.1f}분 경과)")

    if not rows:
        print("\n생성된 결과가 없습니다.")
        return 1

    rep = {
        "pairs": len(rows),
        "settings": {"steps": a.steps, "cfg": a.cfg, "strength": a.strength,
                     "seed": a.seed, "feather": a.feather,
                     "bg_width": a.bg_width, "obj_width": a.obj_width},
        "anydoor": summarize([r["anydoor"] for r in rows]),
        "cgiv2": summarize([r["cgiv2"] for r in rows]),
        "rows": rows,
        "elapsed_sec": round(time.time() - t_start, 1),
        "dinov2_cache": engine.cache_size(),
    }
    (out / "compare_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 62)
    print(f"{'':10s} {'정체성(↑)':>12s} {'이음매(↓)':>12s}")
    print("-" * 62)
    for k in ("anydoor", "cgiv2"):
        s = rep[k]
        print(f"{k:10s} {s['identity']['mean']:12.4f} {s['seam']['mean']:12.2f}")
    di = rep["cgiv2"]["identity"]["mean"] - rep["anydoor"]["identity"]["mean"]
    ds = rep["cgiv2"]["seam"]["mean"] - rep["anydoor"]["seam"]["mean"]
    print("-" * 62)
    print(f"{'차이':10s} {di:+12.4f} {ds:+12.2f}")
    print(f"\n{rep['elapsed_sec']/60:.1f}분 · DINOv2 캐시 {rep['dinov2_cache']}개")
    print(f"원본  {d_any}\nCGIv2 {d_v2}\n비교  {d_cmp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
