"""2번 검증 — 1단계: 얼굴 검출 + 상반신 크롭 + 크기 예측. CGI venv 전용.

**GPU 없음.** 여기서 만든 산출물을 generate_upper_body.py(AnyDoor venv)가
읽어 실제로 합성한다.

venv 를 분리한 이유
    YuNet(cv2.FaceDetectorYN)이 AnyDoor venv 의 cv2 4.7.0 에서 깨진다
    (NaryEltwise shape 불일치 — 홀수 입력 폭에서 FPN 두 갈래의 출력 크기가
    어긋나는 구버전 DNN 버그로 보인다). CGI venv 의 cv2 4.11.0 에서는
    정상 동작한다. 반대로 확산 생성은 pytorch_lightning 이 있는 AnyDoor
    venv 에서만 된다. 한 프로세스에 같이 넣을 수 없어 쪼갠다
    (compare_runs.py / rescore.py 를 나눈 것과 같은 이유).

사용:
    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/predict_upper_body.py
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
from cgiv2 import prep                                   # noqa: E402
from cgiv2.evaluate import FaceScorer                     # noqa: E402
from cgiv2.pairs import PairBuilder                        # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def pick_one(folder: Path, name: str) -> Path:
    """compare_runs.py 의 pick() 과 반드시 같은 규칙을 써야 한다.

    Windows 는 파일명 대소문자를 구분하지 않으므로 Path.glob(f"{name}*")
    는 "W03*" 로 "w03_colosseum.jpg" 까지 걸리고, 정렬도 안 돼 있어 어느
    쪽이 뽑힐지 OS 마다 달라진다. 실제로 그래서 엉뚱한 배경(984x1600,
    베이스라인이 쓴 7232x4827 짜리와 다른 사진)이 뽑혀 3장을 다시 생성한
    적이 있다 (2026-09-22). sorted() + 대소문자 구분 startswith 로 고정한다.
    """
    files = sorted(p for p in folder.glob("*")
                   if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    hit = next((p for p in files if p.stem.startswith(name)), None)
    if hit is None:
        raise FileNotFoundError(f"{folder} 에 '{name}' 로 시작하는 파일이 없습니다")
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
    ap.add_argument("--objects", nargs="+", default=["F01", "F07", "F11"])
    ap.add_argument("--background", default="W03")
    ap.add_argument("--obj-dir", default="D:/JungPra/pythonpra/CGI/objects")
    ap.add_argument("--bg-dir", default="D:/JungPra/pythonpra/CGI/backgrounds")
    ap.add_argument("--mask-dir", default=str(root / "work" / "masks"))
    ap.add_argument("--models", default=str(root / "work" / "models"))
    ap.add_argument("--out", default=str(root / "work" / "upper_body"))
    ap.add_argument("--obj-width", type=int, default=1200)
    ap.add_argument("--bg-width", type=int, default=1600)
    ap.add_argument("--height-ratio", type=float, default=0.22,
                    help="상반신 배치 크기(배경 높이 대비). 전신 실행은 0.45 였다")
    ap.add_argument("--head-room", type=float, default=1.0)
    ap.add_argument("--torso-ratio", type=float, default=3.6)
    ap.add_argument("--width-ratio", type=float, default=2.8)
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    md = Path(a.models)

    scorer = FaceScorer(md / "face_detection_yunet_2023mar.onnx",
                        md / "face_recognition_sface_2021dec.onnx")
    builder = PairBuilder(P["anydoor_root"])

    bgp = pick_one(Path(a.bg_dir), a.background)
    bg = load_rgb(bgp, a.bg_width)
    bg_key = bgp.stem[:24]
    print(f"배경: {bgp.name}  ({cv2.imread(str(bgp)).shape[1]}x{cv2.imread(str(bgp)).shape[0]} 원본)\n")

    print(f"{'객체':26s} {'원본':>8s} {'전신→224':>10s} {'상반신→224':>12s}  관문")
    print("-" * 78)

    rows = []
    for name in a.objects:
        op = pick_one(Path(a.obj_dir), name)
        mp = Path(a.mask_dir) / f"{op.stem}.png"
        if not mp.exists():
            print(f"{op.stem[:26]:26s} 마스크 없음 — 건너뜀")
            continue
        ref = load_rgb(op, a.obj_width)
        rm = (cv2.imread(str(mp), cv2.IMREAD_GRAYSCALE) > 128).astype(np.uint8)
        if rm.shape != ref.shape[:2]:
            rm = cv2.resize(rm, (ref.shape[1], ref.shape[0]),
                            interpolation=cv2.INTER_NEAREST)

        orig_face_px = scorer.face_px(ref)

        dummy_tar = prep.place_box(bg.shape, center=(0.62, 0.5), height_ratio=0.45,
                                   aspect=prep.object_aspect(rm))
        item_full = builder.build(ref, rm, bg, dummy_tar, train=False, tar_crop_ratio=2.0)
        full_face_px = scorer.face_px((item_full["ref"] * 255).astype(np.uint8))

        _, face_box = scorer.detect(ref)
        if face_box is None:
            print(f"{op.stem[:26]:26s} {('%d'%orig_face_px) if orig_face_px else '—':>8s} "
                  f"{('%d'%full_face_px) if full_face_px else '—':>10s}   얼굴 검출 실패 — 건너뜀")
            continue

        bust_img, bust_mask = prep.crop_to_face(
            ref, rm, face_box,
            head_room=a.head_room, torso_ratio=a.torso_ratio, width_ratio=a.width_ratio)
        bust_area = float(bust_mask.sum() / bust_mask.size)
        bad = builder.check_gates(bust_mask, dummy_tar)
        gate_ok = not bad
        note = f"면적 {bust_area:.1%}  " + (" / ".join(bad) if bad else "통과")

        tar_bust = prep.place_box(bg.shape, center=(0.55, 0.5),
                                  height_ratio=a.height_ratio,
                                  aspect=prep.object_aspect(bust_mask))
        item_bust = builder.build(bust_img, bust_mask, bg, tar_bust, train=False,
                                  tar_crop_ratio=2.0)
        bust_face_px = scorer.face_px((item_bust["ref"] * 255).astype(np.uint8))

        print(f"{op.stem[:26]:26s} {('%d'%orig_face_px) if orig_face_px else '—':>8s} "
              f"{('%d'%full_face_px) if full_face_px else '—':>10s} "
              f"{('%d'%bust_face_px) if bust_face_px else '—':>12s}  {note}")

        key = op.stem[:24]
        cv2.imwrite(str(out / f"{key}_bust_img.png"), bust_img[:, :, ::-1])
        cv2.imwrite(str(out / f"{key}_bust_mask.png"), bust_mask * 255)
        cv2.imwrite(str(out / f"{key}_tar.png"), tar_bust * 255)
        cv2.imwrite(str(out / f"ref224_full_{key}.png"),
                    (item_full["ref"] * 255).astype(np.uint8)[:, :, ::-1])
        cv2.imwrite(str(out / f"ref224_bust_{key}.png"),
                    (item_bust["ref"] * 255).astype(np.uint8)[:, :, ::-1])

        rows.append(dict(name=key, background=bg_key, gate_ok=gate_ok, gate_note=note,
                         bust_area=bust_area, orig_face_px=orig_face_px,
                         full_face_px=full_face_px, bust_face_px=bust_face_px,
                         improved=bool(bust_face_px and full_face_px
                                       and bust_face_px > full_face_px)))

    runnable = [r for r in rows if r["gate_ok"] and r["improved"]]
    meta = {"background": a.background, "bg_file": bgp.name, "bg_key": bg_key,
            "bg_width": a.bg_width,
            "height_ratio": a.height_ratio,
            "crop_params": {"head_room": a.head_room, "torso_ratio": a.torso_ratio,
                            "width_ratio": a.width_ratio},
            "runnable": [r["name"] for r in runnable], "rows": rows}
    (out / "predict_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n예측상 개선되고 관문 통과: {len(runnable)}/{len(rows)}건")
    print(f"산출물: {out}")
    print(f"메타:   {out / 'predict_meta.json'}")
    if runnable:
        print(f"\n다음: AnyDoor venv 에서 generate_upper_body.py 실행")
    return 0 if runnable else 1


if __name__ == "__main__":
    raise SystemExit(main())
