"""2번 검증 — 2단계: 실제 합성. AnyDoor venv 전용.

predict_upper_body.py(CGI venv)가 만든 산출물을 디스크에서 읽는다.
**얼굴 검출을 하지 않는다** — 그래서 AnyDoor venv 의 cv2 4.7.0 에서도
안전하다. Compositor 가 쓰는 것은 AnyDoor 자체의 mask_score 등(cv2 기본
연산)뿐이고 cv2.FaceDetectorYN 은 여기서 호출되지 않는다.

사용:
    D:/JungPra/pythonpra/CGI/AnyDoor/.venv/Scripts/python.exe scripts/generate_upper_body.py
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
from cgiv2 import AnyDoorEngine, Compositor, Settings    # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cfg = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    P = cfg["paths"]

    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default=str(root / "work" / "upper_body"))
    ap.add_argument("--bg-dir", default="D:/JungPra/pythonpra/CGI/backgrounds")
    ap.add_argument("--out", default=str(root / "outputs" / "upper_body"))
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--cfg", type=float, default=5.0)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--tar-crop-ratio", type=float, default=2.0)
    a = ap.parse_args()

    work, out = Path(a.work), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    meta = json.loads((work / "predict_meta.json").read_text(encoding="utf-8"))
    runnable = meta["runnable"]
    if not runnable:
        print("predict_meta.json 에 실행 가능한 대상이 없습니다.")
        return 1

    # predict_upper_body.py 가 고른 파일명을 그대로 쓴다 — 다시 매칭하지 않는다.
    # (2026-09-22: 재매칭 방식은 Windows 대소문자 무시 때문에 "W03*" 가
    #  베이스라인과 다른 파일(w03_colosseum.jpg, 984x1600)을 골라 3장을
    #  잘못된 배경으로 생성한 적이 있다.)
    bgp = Path(a.bg_dir) / meta["bg_file"]
    bg = cv2.cvtColor(cv2.imread(str(bgp)), cv2.COLOR_BGR2RGB)
    print(f"배경: {bgp.name}")
    if bg.shape[1] > meta["bg_width"]:
        h = int(bg.shape[0] * meta["bg_width"] / bg.shape[1])
        bg = cv2.resize(bg, (meta["bg_width"], h), interpolation=cv2.INTER_AREA)

    print(f"대상 {len(runnable)}건: {runnable}")
    print(f"steps={a.steps} cfg={a.cfg} strength={a.strength} seed={a.seed} "
          f"height_ratio={meta['height_ratio']}\n")

    print("모델 로딩...", flush=True)
    t0 = time.time()
    engine = AnyDoorEngine(P["anydoor_root"], P["ckpt"],
                           save_memory=cfg["engine"]["save_memory"],
                           device=cfg["engine"]["device"])
    comp = Compositor(engine, P["anydoor_root"])
    print(f"  {time.time()-t0:.1f}초\n")

    st = Settings(steps=a.steps, cfg=a.cfg, control_strength=a.strength,
                  seed=a.seed, tar_crop_ratio=a.tar_crop_ratio,
                  normalize_object=False)

    t_start = time.time()
    done = []
    for i, name in enumerate(runnable, 1):
        bust_img = cv2.cvtColor(cv2.imread(str(work / f"{name}_bust_img.png")),
                                cv2.COLOR_BGR2RGB)
        bust_mask = (cv2.imread(str(work / f"{name}_bust_mask.png"),
                                cv2.IMREAD_GRAYSCALE) > 128).astype(np.uint8)
        tar = (cv2.imread(str(work / f"{name}_tar.png"),
                          cv2.IMREAD_GRAYSCALE) > 128).astype(np.uint8)

        np.random.seed(a.seed)
        res = comp(bust_img, bust_mask, bg, tar, st)
        if res.skipped:
            print(f"[{i}/{len(runnable)}] {name}  탈락: {res.skipped}")
            continue

        out_path = out / f"{name}__{meta['bg_key']}_bust.png"
        cv2.imwrite(str(out_path), res.image[:, :, ::-1])
        done.append(name)
        el = time.time() - t_start
        print(f"[{i}/{len(runnable)}] {name}  저장 {out_path.name}  ({el/60:.1f}분 경과)")

    (out / "generate_meta.json").write_text(
        json.dumps({"settings": vars(a), "background": meta["background"],
                    "bg_key": meta["bg_key"], "done": done},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{len(done)}/{len(runnable)}건 생성 완료 · {(time.time()-t_start)/60:.1f}분")
    print(f"다음: CGI venv 에서 score_upper_body.py 실행")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
