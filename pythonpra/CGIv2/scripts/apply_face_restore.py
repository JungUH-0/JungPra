"""face_restore 배선 검증 — 2단계: 이식 적용. CGI venv 전용, GPU 없음.

gen_keep_raw.py 가 남긴 raw(512 모델 출력)를 `Result.repost()`로 다시
후처리한다. **이게 파이프라인에 배선한 `_finish()`/`Result.repost()` 를
실제로 실행하는 첫 검증이다** — 지금까지는 `test_face_transplant.py`로
`FaceTransplanter.transplant()`를 직접 불렀을 뿐, 프로덕션 경로
(`Settings.face_restore` → `_finish()` → `repost()`)는 안 거쳤다.

AnyDoorEngine 을 전혀 안 쓴다 — `Result.repost()`는 순수 후처리라 모델이
필요 없다. 그래서 CGI venv 에서 안전하게(cv2 4.11) 돈다.

사용:
    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/apply_face_restore.py --key <키>
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
from cgiv2.evaluate import FaceScorer            # noqa: E402
from cgiv2.face_restore import FaceTransplanter   # noqa: E402
from cgiv2.mask import load_mask                  # noqa: E402
from cgiv2.pipeline import Result, Settings        # noqa: E402

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

    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True)
    ap.add_argument("--work", default=str(root / "work" / "face_restore_e2e"))
    ap.add_argument("--out", default=str(root / "outputs" / "face_restore_e2e"))
    ap.add_argument("--obj-dir", default="D:/JungPra/pythonpra/CGI/objects")
    ap.add_argument("--mask-dir", default=str(root / "work" / "masks"))
    ap.add_argument("--models", default=str(root / "work" / "models"))
    a = ap.parse_args()

    work, out = Path(a.work), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    k = a.key

    meta = json.loads((work / f"{k}_meta.json").read_text(encoding="utf-8"))

    ref = load_rgb(Path(a.obj_dir) / meta["object_file"], meta["obj_width"])
    obj_stem = Path(meta["object_file"]).stem
    rm = load_mask(Path(a.mask_dir) / f"{obj_stem}.png")
    if rm.shape != ref.shape[:2]:
        rm = cv2.resize(rm, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_NEAREST)

    bg = load_rgb(work / f"{k}_bg.png")
    no_restore = load_rgb(work / f"{k}_no_restore.png")
    raw = np.load(work / f"{k}_raw.npy")
    extra_sizes = np.load(work / f"{k}_extra_sizes.npy")
    crop_box = np.load(work / f"{k}_crop_box.npy")
    tar = (cv2.imread(str(work / f"{k}_tar.png"), cv2.IMREAD_GRAYSCALE) > 128).astype(np.uint8)

    md = Path(a.models)
    scorer = FaceScorer(md / "face_detection_yunet_2023mar.onnx",
                        md / "face_recognition_sface_2021dec.onnx")
    transplanter = FaceTransplanter(scorer)

    # gen_keep_raw.py 와 같은 세팅 + face_restore=True 만 추가.
    s = meta["settings"]
    st = Settings(steps=s["steps"], cfg=s["cfg"], control_strength=s["strength"],
                 seed=s["seed"], tar_crop_ratio=s["tar_crop_ratio"],
                 normalize_object=s["normalize_object"], feather=s["feather"],
                 face_restore=True)

    # Result.repost() 를 그대로 부른다 — 이게 프로덕션 API 다.
    res = Result(image=no_restore, region=tar, raw=raw,
                extra_sizes=extra_sizes, crop_box=crop_box)
    restored = res.repost(bg, st, ref_image=ref, ref_mask=rm, transplanter=transplanter)

    cv2.imwrite(str(out / f"{k}_restored.png"), restored[:, :, ::-1])

    before = scorer.score(ref, no_restore)
    after = scorer.score(ref, restored)

    print(f"repost() 로 얼굴 이식 적용 완료 — 프로덕션 경로(Settings/_finish/Result.repost) 검증됨\n")
    print(f"{'':12s} {'정체성':>9s}")
    print("-" * 24)
    print(f"{'이식 전':12s} {(f'{before:.4f}' if before is not None else '미검출'):>9s}")
    print(f"{'이식 후':12s} {(f'{after:.4f}' if after is not None else '미검출'):>9s}")
    if before is not None and after is not None:
        print(f"{'차이':12s} {after-before:>+9.4f}")
        print(f"\n판정선 0.363")
        print(f"이식 전: {'넘었다' if before >= FaceScorer.SAME_PERSON else '못 넘었다'}"
              f"  →  이식 후: {'넘었다' if after >= FaceScorer.SAME_PERSON else '못 넘었다'}")

    print(f"\n이식 전: {out / (k + '_restored.png')} 와 비교할 원본은 {work / (k + '_no_restore.png')}")
    print(f"이식 후: {out / (k + '_restored.png')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
