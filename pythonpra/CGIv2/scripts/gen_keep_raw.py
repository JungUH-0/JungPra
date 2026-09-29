"""face_restore 배선 검증 — 1단계: 생성. AnyDoor venv 전용.

**방금 확인**: FaceTransplanter(YuNet)를 AnyDoor venv 안에서 직접 부르면
cv2 4.7.0 의 NaryEltwise 버그로 크래시한다(참조 1200폭·생성물 1600폭
양쪽 다 재현 확인). `Settings(face_restore=True)`를 AnyDoorEngine 과
같은 프로세스에서 켜면 안 된다 — compare_runs/rescore, predict/generate/
score_upper_body 를 나눴던 것과 같은 이유로 여기서도 쪼갠다.

이 스크립트는 face_restore=False 로 평소처럼 생성하되 keep_raw=True 로
raw(512 모델 출력)와 crop 메타를 남긴다. 얼굴 이식은 2단계
(apply_face_restore.py, CGI venv)에서 `Result.repost()`로 GPU 없이
적용한다 — 이게 `repost()`를 만든 이유 그 자체다.

사용:
    D:/JungPra/pythonpra/CGI/AnyDoor/.venv/Scripts/python.exe scripts/gen_keep_raw.py
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
from cgiv2 import prep                                   # noqa: E402
from cgiv2.mask import load_mask                         # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def pick_one(folder: Path, name: str) -> Path:
    """compare_runs.py 와 같은 규칙. Windows 대소문자 무시로 인한
    배경 오매칭(2026-09-22)을 반복하지 않기 위해 sorted()+대소문자구분."""
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
    ap.add_argument("--background", default="W03")
    ap.add_argument("--obj-dir", default="D:/JungPra/pythonpra/CGI/objects")
    ap.add_argument("--bg-dir", default="D:/JungPra/pythonpra/CGI/backgrounds")
    ap.add_argument("--mask-dir", default=str(root / "work" / "masks"))
    ap.add_argument("--out", default=str(root / "work" / "face_restore_e2e"))
    ap.add_argument("--obj-width", type=int, default=1200)
    ap.add_argument("--bg-width", type=int, default=1600)
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--cfg", type=float, default=5.0)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=1234)
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    op = pick_one(Path(a.obj_dir), a.object)
    bgp = pick_one(Path(a.bg_dir), a.background)
    ref = load_rgb(op, a.obj_width)
    rm = load_mask(Path(a.mask_dir) / f"{op.stem}.png")
    if rm.shape != ref.shape[:2]:
        rm = cv2.resize(rm, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_NEAREST)
    bg = load_rgb(bgp, a.bg_width)
    print(f"객체: {op.name}\n배경: {bgp.name} ({bg.shape[1]}x{bg.shape[0]})\n")

    tar = prep.place_box(bg.shape, center=(0.62, 0.5), height_ratio=0.45,
                         aspect=prep.object_aspect(rm))

    print("모델 로딩...", flush=True)
    t0 = time.time()
    engine = AnyDoorEngine(P["anydoor_root"], P["ckpt"],
                           save_memory=cfg["engine"]["save_memory"],
                           device=cfg["engine"]["device"])
    # face_transplanter 를 안 준다 — 이 프로세스(AnyDoor venv, cv2 4.7.0)에서
    # FaceScorer/YuNet 을 만들면 그 자체로 크래시한다. face_restore=False 로
    # 두고 keep_raw 만 켜서, 이식은 2단계(CGI venv)에서 한다.
    comp = Compositor(engine, P["anydoor_root"])
    print(f"  {time.time()-t0:.1f}초\n")

    st = Settings(steps=a.steps, cfg=a.cfg, control_strength=a.strength, seed=a.seed,
                  tar_crop_ratio=2.0, normalize_object=True, feather=6,
                  face_restore=False)

    t0 = time.time()
    np.random.seed(a.seed)
    res = comp(ref, rm, bg, tar, st, keep_raw=True)
    print(f"생성 {time.time()-t0:.1f}초")

    if res.skipped:
        print(f"관문 탈락: {res.skipped}")
        return 1
    if res.raw is None:
        print("raw 가 비어 있습니다 (keep_raw 확인).")
        return 1

    key = f"{op.stem[:24]}__{bgp.stem[:24]}"
    np.save(out / f"{key}_raw.npy", res.raw)
    np.save(out / f"{key}_extra_sizes.npy", res.extra_sizes)
    np.save(out / f"{key}_crop_box.npy", res.crop_box)
    cv2.imwrite(str(out / f"{key}_bg.png"), bg[:, :, ::-1])
    cv2.imwrite(str(out / f"{key}_tar.png"), tar * 255)
    cv2.imwrite(str(out / f"{key}_no_restore.png"), res.image[:, :, ::-1])

    meta = {"key": key, "object_file": op.name, "background_file": bgp.name,
            "obj_width": a.obj_width, "bg_width": a.bg_width,
            "settings": {"steps": a.steps, "cfg": a.cfg, "strength": a.strength,
                        "seed": a.seed, "tar_crop_ratio": 2.0,
                        "normalize_object": True, "feather": 6}}
    (out / f"{key}_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                          encoding="utf-8")

    print(f"\n저장: {out}")
    print(f"다음: CGI venv 에서 scripts/apply_face_restore.py --key {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
