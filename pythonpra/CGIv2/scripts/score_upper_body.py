"""2번 검증 — 3단계: 얼굴 정체성 채점 + 전신 결과와 비교. CGI venv 전용.

generate_upper_body.py(AnyDoor venv)가 만든 결과를 읽어 SFace 로 채점하고,
2026-09-22 전신 실행 결과(outputs/face_report.json)와 같은 쌍 키로 직접
대조한다. GPU 없음.

사용:
    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/score_upper_body.py
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
from cgiv2.evaluate import FaceScorer     # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cfg = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    P = cfg["paths"]

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(root / "outputs" / "upper_body"))
    ap.add_argument("--obj-dir", default="D:/JungPra/pythonpra/CGI/objects")
    ap.add_argument("--models", default=str(root / "work" / "models"))
    ap.add_argument("--obj-width", type=int, default=1200)
    ap.add_argument("--prev-report", default=str(Path(P["out"]) / "face_report.json"))
    a = ap.parse_args()

    out = Path(a.out)
    gm = json.loads((out / "generate_meta.json").read_text(encoding="utf-8"))
    if not gm["done"]:
        print("생성된 결과가 없습니다.")
        return 1

    md = Path(a.models)
    scorer = FaceScorer(md / "face_detection_yunet_2023mar.onnx",
                        md / "face_recognition_sface_2021dec.onnx")

    prev_by_pair = {}
    prev_path = Path(a.prev_report)
    if prev_path.exists():
        for r in json.loads(prev_path.read_text(encoding="utf-8"))["rows"]:
            prev_by_pair[r["pair"]] = r["cgiv2"]

    def load_rgb(p, max_w=None):
        img = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)
        if max_w and img.shape[1] > max_w:
            h = int(img.shape[0] * max_w / img.shape[1])
            img = cv2.resize(img, (max_w, h), interpolation=cv2.INTER_AREA)
        return img

    print(f"{'쌍':30s} {'전신(이전)':>12s} {'상반신':>10s} {'차이':>10s}")
    print("-" * 66)

    rows = []
    for name in gm["done"]:
        op = next((q for q in Path(a.obj_dir).glob(f"{name}*")
                   if q.suffix.lower() in {".jpg", ".jpeg", ".png"}), None)
        if op is None:
            print(f"{name:30s} 원본 이미지 못 찾음")
            continue
        ref = load_rgb(op, a.obj_width)

        pair_key = f"{name}__{gm['bg_key']}"
        gen_path = out / f"{pair_key}_bust.png"
        gen = load_rgb(gen_path)

        s = scorer.score(ref, gen)
        prev = prev_by_pair.get(pair_key)
        rows.append({"pair": pair_key, "bust_face_identity": s,
                     "full_face_identity": prev})

        s_s = f"{s:.4f}" if s is not None else "미검출"
        p_s = f"{prev:.4f}" if prev is not None else "—"
        d_s = f"{s-prev:+.4f}" if (s is not None and prev is not None) else "—"
        print(f"{pair_key:30s} {p_s:>12s} {s_s:>10s} {d_s:>10s}")

    ok = [r for r in rows if r["bust_face_identity"] is not None]
    prevs = [r["full_face_identity"] for r in ok if r["full_face_identity"] is not None]
    rep = {"rows": rows,
           "bust_mean": float(np.mean([r["bust_face_identity"] for r in ok])) if ok else None,
           "full_mean": float(np.mean(prevs)) if prevs else None,
           "same_person_threshold": FaceScorer.SAME_PERSON}
    (out / "upper_body_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    print("-" * 66)
    if rep["bust_mean"] is not None:
        full_mean_s = f"{rep['full_mean']:.4f}" if rep["full_mean"] is not None else "—"
        print(f"{'평균':30s} {full_mean_s:>12s} {rep['bust_mean']:>10.4f}")
        print(f"\n판정선 {FaceScorer.SAME_PERSON:.3f} "
              f"(기준선: 자기자신 0.9370 / 타인 0.0234, 2026-09-22 측정)")
        verdict = "넘었다" if rep["bust_mean"] >= FaceScorer.SAME_PERSON else "못 넘었다"
        print(f"상반신 평균이 판정선을 {verdict}")
        if rep["full_mean"] is not None:
            print(f"전신 대비 변화: {rep['bust_mean'] - rep['full_mean']:+.4f}")
    print(f"\n보고서: {out / 'upper_body_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
