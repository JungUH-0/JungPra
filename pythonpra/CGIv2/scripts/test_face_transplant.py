"""3번 검증 — 이미 생성된 결과에 얼굴 이식을 적용해본다. CGI venv 전용, GPU 없음.

새로 합성하지 않는다. outputs/cgiv2(전신 9장)와 outputs/upper_body(상반신
3장)에 이미 있는 결과에 FaceTransplanter 를 적용하고 SFace 로 전/후를 잰다.
확산을 다시 안 돌리므로 몇 초면 끝난다.

사용:
    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/test_face_transplant.py
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
    ap.add_argument("--obj-dir", default="D:/JungPra/pythonpra/CGI/objects")
    ap.add_argument("--mask-dir", default=str(root / "work" / "masks"))
    ap.add_argument("--models", default=str(root / "work" / "models"))
    ap.add_argument("--out", default=str(root / "outputs"))
    ap.add_argument("--obj-width", type=int, default=1200)
    ap.add_argument("--head-room", type=float, default=0.6)
    ap.add_argument("--torso-ratio", type=float, default=1.3)
    ap.add_argument("--width-ratio", type=float, default=1.7)
    ap.add_argument("--feather", type=float, default=0.10)
    ap.add_argument("--color-match", type=float, default=0.5)
    ap.add_argument("--blend", default="feather", choices=["feather", "poisson"])
    a = ap.parse_args()

    md = Path(a.models)
    scorer = FaceScorer(md / "face_detection_yunet_2023mar.onnx",
                        md / "face_recognition_sface_2021dec.onnx")
    transplanter = FaceTransplanter(scorer)

    out = Path(a.out)
    targets = sorted((out / "cgiv2").glob("*.png")) + sorted((out / "upper_body").glob("*_bust.png"))
    if not targets:
        print("대상 결과가 없습니다.")
        return 1

    result_dir = out / "face_restored"
    result_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'쌍':44s} {'이전':>9s} {'이식후':>9s} {'차이':>9s}  얼굴비율")
    print("-" * 88)

    rows = []
    for gp in targets:
        name = gp.stem.replace("_bust", "")
        obj_name = name.split("__")[0]
        op = next((q for q in Path(a.obj_dir).glob(f"{obj_name}*")
                   if q.suffix.lower() in {".jpg", ".jpeg", ".png"}), None)
        if op is None:
            continue
        ref = load_rgb(op, a.obj_width)
        gen = load_rgb(gp)

        mp = Path(a.mask_dir) / f"{op.stem}.png"
        if not mp.exists():
            continue
        ref_mask = (cv2.imread(str(mp), cv2.IMREAD_GRAYSCALE) > 128).astype(np.uint8)
        if ref_mask.shape != ref.shape[:2]:
            ref_mask = cv2.resize(ref_mask, (ref.shape[1], ref.shape[0]),
                                  interpolation=cv2.INTER_NEAREST)

        before = scorer.score(ref, gen)
        ratio = transplanter.face_size_ratio(ref, gen)
        restored, ok = transplanter.transplant(
            ref, ref_mask, gen,
            head_room=a.head_room, torso_ratio=a.torso_ratio, width_ratio=a.width_ratio,
            feather=a.feather, color_match=a.color_match, blend=a.blend)
        after = scorer.score(ref, restored) if ok else None

        if ok:
            cv2.imwrite(str(result_dir / gp.name), restored[:, :, ::-1])

        b_s = f"{before:.4f}" if before is not None else "미검출"
        a_s = f"{after:.4f}" if after is not None else ("이식실패" if not ok else "미검출")
        d_s = f"{after-before:+.4f}" if (before is not None and after is not None) else "—"
        r_s = f"{ratio:.2f}" if ratio is not None else "—"
        print(f"{name[:44]:44s} {b_s:>9s} {a_s:>9s} {d_s:>9s}  {r_s}")

        rows.append({"pair": name, "before": before, "after": after,
                     "ok": ok, "face_size_ratio": ratio,
                     "source_dir": gp.parent.name})

    ok_rows = [r for r in rows if r["ok"] and r["after"] is not None and r["before"] is not None]
    fail = [r for r in rows if not r["ok"]]

    rep = {"settings": vars(a), "rows": rows,
           "before_mean": float(np.mean([r["before"] for r in ok_rows])) if ok_rows else None,
           "after_mean": float(np.mean([r["after"] for r in ok_rows])) if ok_rows else None,
           "transplant_failures": len(fail)}
    (out / "face_restore_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    print("-" * 88)
    if ok_rows:
        print(f"{'평균':44s} {rep['before_mean']:>9.4f} {rep['after_mean']:>9.4f} "
              f"{rep['after_mean']-rep['before_mean']:>+9.4f}")
        print(f"\n판정선 0.363 (기준선: 자기자신 0.9370 / 타인 0.0234, 2026-09-22 측정)")
        v_before = "넘었다" if rep["before_mean"] >= FaceScorer.SAME_PERSON else "못 넘었다"
        v_after = "넘었다" if rep["after_mean"] >= FaceScorer.SAME_PERSON else "못 넘었다"
        print(f"이식 전: {v_before}  →  이식 후: {v_after}")
    if fail:
        print(f"\n이식 실패 {len(fail)}건 (얼굴 검출 실패 또는 변환 불가):")
        for r in fail:
            print(f"  {r['pair']}")
    print(f"\n결과 이미지: {result_dir}")
    print(f"보고서: {out / 'face_restore_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
