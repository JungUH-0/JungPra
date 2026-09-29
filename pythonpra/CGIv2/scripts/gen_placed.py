"""배치대로 확산 생성 — 1안(placement.py)·2안(anchor.py) 공통. AnyDoor venv 전용.

2안(2026-09-26): check_anchor.py 산출물도 같은 형식이라 그대로 읽는다.
    --placement work/plan2/anchor --bg-dir <사람 사진> --obj-dir work/plan2/objects
    --mask-dir work/plan2/masks --object B01 --out work/plan2/gen

check_placement.py(CGI venv)가 만든 <배경>_tar.png 를 그대로 읽는다.
Mask2Former 가 AnyDoor venv 의 transformers 4.19.2 에 없어서 배치 계산은
CGI venv 에서 하고, 여기서는 마스크 파일만 읽는다.

산출물 형식은 gen_keep_raw.py 와 같다 — 얼굴 이식과 인물만 되붙이기는
CGI venv 에서 apply_post.py --work <여기 out> 로 적용한다 (2026-09-23 부터).

사용:
    D:/JungPra/pythonpra/CGI/AnyDoor/.venv/Scripts/python.exe scripts/gen_placed.py \
        --object F01 --backgrounds K05 W01 W05 W09
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
from cgiv2 import AnyDoorEngine, Compositor, Settings   # noqa: E402
from cgiv2.mask import load_mask                         # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def pick_one(folder: Path, name: str) -> Path:
    files = sorted(p for p in folder.glob("*")
                   if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    hit = next((p for p in files if p.stem.startswith(name)), None)
    if hit is None:
        raise FileNotFoundError(f"{folder} 에 '{name}' 없음")
    return hit


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
    ap.add_argument("--object", default="F01")
    ap.add_argument("--backgrounds", nargs="+", required=True)
    ap.add_argument("--obj-dir", default="D:/JungPra/pythonpra/CGI/objects")
    ap.add_argument("--bg-dir", default="D:/JungPra/pythonpra/CGI/backgrounds")
    ap.add_argument("--mask-dir", default=str(root / "work" / "masks"))
    ap.add_argument("--placement", default=str(root / "work" / "placement"))
    ap.add_argument("--out", default=str(root / "work" / "placed"))
    ap.add_argument("--obj-width", type=int, default=1200)
    ap.add_argument("--bg-width", type=int, default=1600)
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--cfg", type=float, default=5.0)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--shape-control", action="store_true",
                    help="배치 마스크를 참조 실루엣으로 (강체 물건용, 2026-09-26)")
    a = ap.parse_args()

    out, pdir = Path(a.out), Path(a.placement)
    out.mkdir(parents=True, exist_ok=True)
    pj = json.loads((pdir / "placement.json").read_text(encoding="utf-8"))
    rows = {r["key"]: r for r in pj["rows"]}

    op = pick_one(Path(a.obj_dir), a.object)
    ref = load_rgb(op, a.obj_width)
    rm = load_mask(Path(a.mask_dir) / f"{op.stem}.png")
    if rm.shape != ref.shape[:2]:
        rm = cv2.resize(rm, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_NEAREST)

    jobs = []
    for pref in a.backgrounds:
        row = next((r for k, r in rows.items() if k.startswith(pref)), None)
        if row is None:
            print(f"{pref}: placement.json 에 없음 — check_placement.py 먼저")
            continue
        tp = pdir / f"{row['key']}_tar.png"
        if not tp.exists():
            print(f"{pref}: tar 마스크 없음 ({row.get('error', '?')})")
            continue
        jobs.append((row, tp))

    print(f"객체 {op.name} · 배경 {len(jobs)}개\n모델 로딩...", flush=True)
    t0 = time.time()
    engine = AnyDoorEngine(P["anydoor_root"], P["ckpt"],
                           save_memory=cfg["engine"]["save_memory"],
                           device=cfg["engine"]["device"])
    comp = Compositor(engine, P["anydoor_root"])     # face_transplanter 없음 — cv2 4.7.0
    print(f"  {time.time()-t0:.1f}초\n")

    st = Settings(steps=a.steps, cfg=a.cfg, control_strength=a.strength, seed=a.seed,
                  tar_crop_ratio=2.0, normalize_object=True, feather=6, face_restore=False,
                  shape_control=a.shape_control)

    keys, t_start = [], time.time()
    for i, (row, tp) in enumerate(jobs, 1):
        bg = load_rgb(Path(a.bg_dir) / row["bg_file"], a.bg_width)
        if [bg.shape[1], bg.shape[0]] != row["size"]:
            print(f"[{i}] {row['key']}: 크기 불일치 {bg.shape[1]}x{bg.shape[0]} vs {row['size']}")
            continue
        tar = (cv2.imread(str(tp), cv2.IMREAD_GRAYSCALE) > 128).astype(np.uint8)

        # 행마다 참조가 다를 수 있다 (2안 시계 — 팔뚝 방향으로 돌린 시계 머리)
        r_ref, r_rm, ref_paths = ref, rm, {}
        if row.get("ref_file"):
            rp, rmp = pdir / row["ref_file"], pdir / row["ref_mask_file"]
            r_ref, r_rm = load_rgb(rp), load_mask(rmp)
            ref_paths = {"ref_path": str(rp.resolve()), "ref_mask_path": str(rmp.resolve())}

        np.random.seed(a.seed)
        res = comp(r_ref, r_rm, bg, tar, st, keep_raw=True)
        if res.skipped:
            print(f"[{i}] {row['key']}: 관문 탈락 {res.skipped}")
            continue

        key = f"{op.stem[:24]}__{row['key']}"
        np.save(out / f"{key}_raw.npy", res.raw)
        np.save(out / f"{key}_extra_sizes.npy", res.extra_sizes)
        np.save(out / f"{key}_crop_box.npy", res.crop_box)
        cv2.imwrite(str(out / f"{key}_bg.png"), bg[:, :, ::-1])
        cv2.imwrite(str(out / f"{key}_tar.png"), tar * 255)
        cv2.imwrite(str(out / f"{key}_no_restore.png"), res.image[:, :, ::-1])
        meta = {"key": key, "object_file": op.name, "background_file": row["bg_file"],
                "obj_width": a.obj_width, "bg_width": a.bg_width, **ref_paths,
                "placement": {k: row.get(k) for k in
                              ("method", "v0", "r", "n_people", "n_used", "feet",
                               "height_ratio", "area", "x_ratio_chosen", "sun", "zoom")},
                "settings": {"steps": a.steps, "cfg": a.cfg, "strength": a.strength,
                             "seed": a.seed, "tar_crop_ratio": 2.0,
                             "normalize_object": True, "feather": 6,
                             "shape_control": a.shape_control}}
        (out / f"{key}_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2,
                                                         default=str), encoding="utf-8")
        keys.append(key)
        print(f"[{i}/{len(jobs)}] {row['key']}  {row['method']}  키 {row['height_ratio']:.0%}"
              f"  ({(time.time()-t_start)/60:.1f}분)")

    (out / "keys.json").write_text(json.dumps(keys, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(keys)}건 저장: {out}")
    print("다음: CGI venv 에서 apply_post.py --work <out>  (얼굴 이식 + 인물만 되붙이기)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
