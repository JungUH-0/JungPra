"""2안 1단계 — 몸 기준 배치 점검. CGI venv 전용, 확산 없음.

사람 사진마다 관절(Keypoint R-CNN)을 찾고 물건 박스를 정한다. 산출물 형식은
check_placement.py 와 같아서 2단계 gen_placed.py 가 그대로 읽는다.

    bag     손에 든 모습 (bag_in_hand). 배경 = 사람 사진 그대로
    watch   손목 (watch_on_wrist). 시계는 화면의 0.1% 수준이라 AnyDoor 면적
            관문(1%)을 못 넘는다 → **손목 둘레 부분 이미지**를 배경으로 쓰고
            3단계가 원래 사진에 되붙인다 (zoom). 참조도 배경마다 다르다 —
            줄 축이 팔뚝과 직각이 되도록 돌린 시계 머리(watch_head)

산출물 (--out)
    <배경>_overlay.png     관절(초록 선·파란 점, 회색 = 기준 미달) + 박스(노랑)
    <배경>_tar.png         배치 마스크 (watch 는 부분 이미지 좌표)
    <배경>_zoom.png        watch — 부분 이미지 (2단계의 배경)
    <배경>_ref.png / _ref_mask.png   watch — 돌린 시계 머리 (2단계의 참조)
    placement.json · sheet.png

사용:
    ... check_anchor.py --object B01 --only F03 F04 F12
    ... check_anchor.py --kind watch --object A01 --obj-dir work/plan2/raw --only F03 F04 \
        --out work/plan2/watch_A01
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cgiv2 import prep                                   # noqa: E402
from cgiv2.anchor import (PoseEstimator, bag_in_hand, box_mask, draw,   # noqa: E402
                          rotate_bound, watch_head, watch_on_wrist, zoom_box)
from cgiv2.mask import load_mask                         # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KP_SHORT = ("nose", "l_eye", "r_eye", "l_ear", "r_ear", "l_sho", "r_sho", "l_elb", "r_elb",
            "l_wri", "r_wri", "l_hip", "r_hip", "l_knee", "r_knee", "l_ank", "r_ank")


def load_rgb(p: Path, max_w: int | None = None):
    img = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)
    if max_w and img.shape[1] > max_w:
        h = int(img.shape[0] * max_w / img.shape[1])
        img = cv2.resize(img, (max_w, h), interpolation=cv2.INTER_AREA)
    return img


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg-dir", default="D:/JungPra/pythonpra/CGI/objects",
                    help="2안 배경 = 사람 사진")
    ap.add_argument("--only", nargs="+", required=True, help="배경 접두사 (예: F03 F04)")
    ap.add_argument("--object", required=True, help="물건 접두사")
    ap.add_argument("--obj-dir", default=str(root / "work" / "plan2" / "objects"),
                    help="watch 가 참조 사진을 읽는 곳")
    ap.add_argument("--mask-dir", default=str(root / "work" / "plan2" / "masks"))
    ap.add_argument("--kind", default="bag", choices=["bag", "watch"])
    ap.add_argument("--size", type=float, default=0.26, help="bag: 물건 높이 / 사람 키")
    ap.add_argument("--grip", type=float, default=0.03, help="bag")
    ap.add_argument("--face", type=float, default=0.023, help="watch: 문자판 지름 / 사람 키")
    ap.add_argument("--offset", type=float, default=-0.025,
                    help="watch: 손목 점에서 팔꿈치 쪽(+) 이동 / 키. 음수 = 손 쪽")
    ap.add_argument("--keep", type=float, default=0.6, help="watch: 문자판 양옆 줄 = 지름 × keep")
    ap.add_argument("--zoom", type=float, default=6.0, help="watch: 부분 이미지 = 박스 긴 변 × zoom")
    ap.add_argument("--silhouette", action="store_true",
                    help="배치 마스크를 사각형 대신 물건 실루엣으로 — gen_placed.py --shape-control 과 짝")
    ap.add_argument("--out", default=str(root / "work" / "plan2" / "anchor"))
    ap.add_argument("--bg-width", type=int, default=1600)
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    mp = next((p for p in sorted(Path(a.mask_dir).glob("*.png"))
               if p.stem.startswith(a.object)), None)
    if mp is None:
        print(f"{a.mask_dir} 에 '{a.object}' 마스크 없음")
        return 1
    obj_mask = load_mask(mp)
    aspect = prep.object_aspect(obj_mask)
    ys, xs = np.nonzero(obj_mask)
    obj_sil = obj_mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

    head = None
    if a.kind == "watch":
        op = next((p for p in sorted(Path(a.obj_dir).glob("*"))
                   if p.stem == mp.stem and p.suffix.lower() in {".jpg", ".jpeg", ".png"}), None)
        if op is None:
            print(f"{a.obj_dir} 에 '{mp.stem}' 사진 없음")
            return 1
        ref = load_rgb(op)
        if obj_mask.shape != ref.shape[:2]:
            obj_mask = cv2.resize(obj_mask, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_NEAREST)
        head = watch_head(ref, obj_mask, keep=a.keep)
        hr, hm, D, ax = head
        cv2.imwrite(str(out / "_head.png"), hr[:, :, ::-1])
        print(f"시계 머리: 주축 {ax:.1f}° · 문자판 지름 {D:.0f}px · 머리 {hm.shape[1]}x{hm.shape[0]}")

    files = sorted(p for p in Path(a.bg_dir).glob("*")
                   if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
                   and any(p.stem.startswith(n) for n in a.only))
    print(f"배경 {len(files)}개 · {a.kind} · 물건 {mp.stem} 가로세로비 {aspect:.3f}")
    print("모델 로딩 (Keypoint R-CNN)...", flush=True)
    t0 = time.time()
    pose = PoseEstimator()
    print(f"  {time.time()-t0:.1f}초\n")

    rows, thumbs = [], []
    for bp in files:
        bg = load_rgb(bp, a.bg_width)
        H, W = bg.shape[:2]
        key = bp.stem[:24]
        person = pose.main_person(bg)
        row = {"bg_file": bp.name, "key": key, "size": [W, H], "method": f"pose:{a.kind}"}
        box = None
        if person is None:
            row["error"] = "사람 미검출"
        else:
            row.update({"person_box": list(person.box), "person_score": person.score,
                        "kp_scores": {n: float(person.kp[i, 2]) for i, n in enumerate(KP_SHORT)}})
            if a.kind == "bag":
                box, info = bag_in_hand(person, aspect, (H, W), size=a.size, grip=a.grip)
                sil = obj_sil
            else:
                hr, hm, D, _ = head
                box, ang, info = watch_on_wrist(person, hm.shape, (H, W), face=a.face,
                                                offset=a.offset)
                if box is not None:
                    r_rgb = rotate_bound(hr, ang, (255, 255, 255))
                    r_m = rotate_bound(hm, ang, 0)
                    ry, rx = np.nonzero(r_m)
                    r_rgb = r_rgb[ry.min():ry.max() + 1, rx.min():rx.max() + 1]
                    r_m = r_m[ry.min():ry.max() + 1, rx.min():rx.max() + 1]
                    cv2.imwrite(str(out / f"{key}_ref.png"), r_rgb[:, :, ::-1])
                    cv2.imwrite(str(out / f"{key}_ref_mask.png"), r_m * 255)
                    sil = r_m
            row.update(info)

            if box is not None:
                full_box = box
                if a.kind == "watch":
                    # 부분 이미지로 옮긴다 — 이게 2단계의 배경이 된다
                    zy1, zy2, zx1, zx2 = zoom_box(box, (H, W), a.zoom)
                    sub = bg[zy1:zy2, zx1:zx2]
                    cv2.imwrite(str(out / f"{key}_zoom.png"), sub[:, :, ::-1])
                    box = (box[0] - zy1, box[1] - zy1, box[2] - zx1, box[3] - zx1)
                    row.update({"bg_file": f"{key}_zoom.png", "size": [sub.shape[1], sub.shape[0]],
                                "ref_file": f"{key}_ref.png", "ref_mask_file": f"{key}_ref_mask.png",
                                "zoom": {"full_bg_file": bp.name, "box": [zy1, zy2, zx1, zx2],
                                         "full_size": [W, H]}})
                shape = (row["size"][1], row["size"][0])
                m = box_mask(shape, box)
                if a.silhouette:
                    # shape_control 은 사각 마스크면 효과가 없다 — 모양을 줘야 따른다
                    y1, y2, x1, x2 = box
                    m[y1:y2, x1:x2] = cv2.resize(sil, (x2 - x1, y2 - y1),
                                                 interpolation=cv2.INTER_NEAREST)
                area = float(m.mean())
                row.update({"box": list(box), "full_box": list(full_box), "area": area,
                            "height_ratio": (box[1] - box[0]) / shape[0],
                            "gate_ok": 0.01 < area < 0.64})
                cv2.imwrite(str(out / f"{key}_tar.png"), m * 255)
                box = full_box
        ov = draw(bg, person, box)
        cv2.imwrite(str(out / f"{key}_overlay.png"), ov[:, :, ::-1])
        rows.append(row)

        if "error" in row:
            msg = row["error"] + (f"  {row.get('rejected')}" if row.get("rejected") else "")
        elif a.kind == "bag":
            msg = (f"{row['side']} 손 · 사람 키 {row['person_h']:.0f}px · 가방 {row['bag_w']:.0f}x{row['bag_h']:.0f}"
                   f" · 면적 {row['area']:.1%} · 관문 {'통과' if row['gate_ok'] else '탈락'}"
                   f"{' · ⚠ 화면 밖으로 잘림' if row['clipped'] else ''}")
        else:
            z = row["zoom"]["box"]
            msg = (f"{row['side']} 손목 · 사람 키 {row['person_h']:.0f}px · 문자판 {row['face_px']:.0f}px"
                   f" · 회전 {row['angle']:.0f}° · 부분 이미지 {z[3]-z[2]}px · 면적 {row['area']:.1%}"
                   f" · 관문 {'통과' if row['gate_ok'] else '탈락'}")
        print(f"{key:26s} {msg}")

        s = 480 / H
        thumbs.append(cv2.resize(ov, (int(W * s), 480), interpolation=cv2.INTER_AREA))

    (out / "placement.json").write_text(json.dumps(
        {"kind": a.kind, "object_mask": mp.name, "aspect": aspect, "size": a.size,
         "grip": a.grip, "face": a.face, "offset": a.offset, "keep": a.keep,
         "zoom": a.zoom, "silhouette": a.silhouette,
         "rows": rows}, ensure_ascii=False, indent=2, default=float),
        encoding="utf-8")
    h = max(t.shape[0] for t in thumbs)
    sheet = np.hstack([np.pad(t, ((0, h - t.shape[0]), (0, 6), (0, 0))) for t in thumbs])
    cv2.imwrite(str(out / "sheet.png"), sheet[:, :, ::-1])
    print(f"\n저장: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
