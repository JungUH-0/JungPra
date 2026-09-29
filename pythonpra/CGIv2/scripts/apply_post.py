"""3단계 — CGI venv 후처리: 얼굴 이식 + 인물만 되붙이기 + 그림자. 확산 없음.

배치 합성 흐름 (venv 가 둘로 나뉜다 — CHANGELOG 'venv 제약' 절)

    1. check_placement.py   CGI venv      배치 마스크 (Mask2Former + DETR)
    2. gen_placed.py        AnyDoor venv  확산 → raw 512 저장 (keep_raw)
    3. apply_post.py        CGI venv      얼굴 이식 + 되붙이기   ← 이 파일

2단계는 YuNet(얼굴 이식, cv2 4.7.0 에서 크래시)과 BiRefNet(되붙이기)을
AnyDoor venv 에서 쓸 수 없어 raw 만 남긴다. 여기서 `Result.repost()` 로
마무리한다 — 프로덕션 경로(Settings → _finish → repost) 그대로다.

산출물 (outputs/placed/)
    <키>_final.png    최종 합성
    <키>_final.json   설정 전체 · 정체성 · 메모(되붙이기 실패 등)

사용:
    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/apply_post.py
    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/apply_post.py --only W01 --paste box
    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/apply_post.py --shadow cast

2안 (사람 사진 + 물건):
    ... apply_post.py --work work/plan2/gen --out outputs/plan2 --paste object --shadow none \
        --no-face --obj-dir work/plan2/objects --mask-dir work/plan2/masks

그림자 (2026-09-26) — 기본 contact(접지 그림자). cast 는 check_placement.py 가
기록한 해(기존 사람들 그림자 2명 이상이 한 방향)가 있을 때만 투영 그림자를
더하고, 없으면 contact 만 한다 (메모에 남음).
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cgiv2.evaluate import FaceScorer             # noqa: E402
from cgiv2.face_restore import FaceTransplanter    # noqa: E402
from cgiv2.mask import get_masker, load_mask       # noqa: E402
from cgiv2.pipeline import Result, Settings         # noqa: E402

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
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default=str(root / "work" / "placed"))
    ap.add_argument("--out", default=str(root / "outputs" / "placed"))
    ap.add_argument("--only", nargs="*", default=None, help="배경 접두사 (예: W01)")
    ap.add_argument("--paste", default="person", choices=["crop", "box", "person", "object"])
    ap.add_argument("--shadow", default="contact", choices=["none", "contact", "cast"],
                    help="cast 는 check_placement.py 가 기록한 해가 있을 때만 그린다")
    ap.add_argument("--placement", default=str(root / "work" / "placement" / "placement.json"))
    ap.add_argument("--no-face", action="store_true",
                    help="얼굴 이식 끔 — 2안(사람이 배경, 물건이 참조)에서 쓴다")
    ap.add_argument("--full-bg-dir", default="D:/JungPra/pythonpra/CGI/objects",
                    help="zoom(부분 이미지) 결과를 되붙일 원래 사진이 있는 곳 — 2안 시계")
    ap.add_argument("--contact-strength", type=float, default=0.5)
    ap.add_argument("--contact-width", type=float, default=1.25)
    ap.add_argument("--contact-height", type=float, default=0.03,
                    help="접지 그림자 두께 / 물건 높이. 사람 0.03, 자동차는 더 두껍게")
    ap.add_argument("--color-match", type=float, default=0.0,
                    help="물건 색을 둘레 배경 통계로 끌어당기는 강도 (LAB, 0~1)")
    ap.add_argument("--mask-tool", default="birefnet_hr", help="person 방식의 분할 도구")
    ap.add_argument("--obj-dir", default="D:/JungPra/pythonpra/CGI/objects")
    ap.add_argument("--mask-dir", default=str(root / "work" / "masks"))
    ap.add_argument("--models", default=str(root / "work" / "models"))
    a = ap.parse_args()

    work, out = Path(a.work), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    keys = sorted(p.name[:-len("_meta.json")] for p in work.glob("*_meta.json"))
    if a.only:
        keys = [k for k in keys if any(f"__{n}" in k for n in a.only)]
    if not keys:
        print("대상이 없습니다.")
        return 1

    # 해 — 2단계 meta 에 있으면 그걸, 없으면(2026-09-26 이전 생성분) 배치 기록에서 찾는다
    pj_path = Path(a.placement)
    sun_by_bg = {}
    if pj_path.exists():
        for r in json.loads(pj_path.read_text(encoding="utf-8"))["rows"]:
            sun_by_bg[r["bg_file"]] = r.get("sun")

    print(f"{len(keys)}건 · 되붙이기 {a.paste} · 그림자 {a.shadow}\n모델 로딩...", flush=True)
    t0 = time.time()
    masker = get_masker(a.mask_tool) if a.paste in {"person", "object"} else None
    md = Path(a.models)
    scorer = FaceScorer(md / "face_detection_yunet_2023mar.onnx",
                        md / "face_recognition_sface_2021dec.onnx")
    transplanter = FaceTransplanter(scorer)
    print(f"  {time.time()-t0:.1f}초\n")

    for k in keys:
        meta = json.loads((work / f"{k}_meta.json").read_text(encoding="utf-8"))
        if meta.get("ref_path"):        # 행마다 다른 참조 (2안 시계 — 돌린 시계 머리)
            ref, rm = load_rgb(Path(meta["ref_path"])), load_mask(meta["ref_mask_path"])
        else:
            ref = load_rgb(Path(a.obj_dir) / meta["object_file"], meta["obj_width"])
            rm = load_mask(Path(a.mask_dir) / f"{Path(meta['object_file']).stem}.png")
        if rm.shape != ref.shape[:2]:
            rm = cv2.resize(rm, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_NEAREST)

        bg = load_rgb(work / f"{k}_bg.png")
        tar = (cv2.imread(str(work / f"{k}_tar.png"), cv2.IMREAD_GRAYSCALE) > 128).astype(np.uint8)
        res = Result(image=bg, region=tar, raw=np.load(work / f"{k}_raw.npy"),
                     extra_sizes=np.load(work / f"{k}_extra_sizes.npy"),
                     crop_box=np.load(work / f"{k}_crop_box.npy"))

        # 2단계와 같은 세팅 + 얼굴 이식 + 되붙이기 + 그림자. 나머지는 Settings 기본값.
        s = meta["settings"]
        sun = meta.get("placement", {}).get("sun") or sun_by_bg.get(meta["background_file"])
        st = Settings(steps=s["steps"], cfg=s["cfg"], control_strength=s["strength"],
                      seed=s["seed"], tar_crop_ratio=s["tar_crop_ratio"],
                      normalize_object=s["normalize_object"], feather=s["feather"],
                      face_restore=not a.no_face, paste=a.paste,
                      shape_control=s.get("shape_control", False),
                      shadow=a.shadow != "none",
                      shadow_tool=a.shadow if a.shadow != "none" else "contact",
                      contact_strength=a.contact_strength, contact_width=a.contact_width,
                      contact_height=a.contact_height, color_match=a.color_match,
                      sun=sun)

        t1 = time.time()
        img = res.repost(bg, st, ref_image=ref, ref_mask=rm,
                         transplanter=transplanter, masker=masker)
        sec = time.time() - t1
        face = scorer.score(ref, img)

        zoom = meta.get("placement", {}).get("zoom")
        if zoom:
            # 부분 이미지에서 합성한 결과를 원래 사진 제자리에 되붙인다
            cv2.imwrite(str(out / f"{k}_final_zoom.png"), img[:, :, ::-1])
            full = load_rgb(Path(a.full_bg_dir) / zoom["full_bg_file"], zoom["full_size"][0])
            zy1, zy2, zx1, zx2 = zoom["box"]
            full[zy1:zy2, zx1:zx2] = img
            img = full
        cv2.imwrite(str(out / f"{k}_final.png"), img[:, :, ::-1])
        (out / f"{k}_final.json").write_text(json.dumps({
            "key": k, "background_file": meta["background_file"],
            "object_file": meta["object_file"], "tag": st.tag(),
            "mask_tool": a.mask_tool if a.paste in {"person", "object"} else None,
            "face": None if face is None else round(float(face), 4),
            "notes": list(res.notes), "post_sec": round(sec, 2),
            "settings": dataclasses.asdict(st),
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        f = f"{face:.4f}" if face is not None else "미검출"
        print(f"{k.split('__')[-1][:24]:24s}  정체성 {f}  {sec:.1f}초  {' / '.join(res.notes)}")

    print(f"\n저장: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
