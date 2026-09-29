"""그림자 비교 — none / offset / contact / cast. CGI venv 전용, 확산 없음.

gen_placed.py 가 남긴 raw 를 `Result.repost()`로 후처리한다. 네 방식 모두
얼굴 이식 + 인물만 되붙이기(person)까지 같고 그림자만 다르다.

    none     그림자 없음 (현재 apply_post.py 결과와 같다)
    offset   기존 postproc.add_contact_shadow — 실루엣 평행이동
    contact  접지 그림자 (shadow.contact_shadow)
    cast     접지 + 투영 그림자. 해는 원본 배경의 기존 사람들 그림자에서 읽는다
             (shadow.estimate_sun). 못 읽으면 contact 와 같아진다

산출물 (outputs/shadow/)
    <키>_<방식>.png
    <키>_sheet.png     전체 · 발 주변 확대
    <키>_sun.png       해 추정 진단 — 사람 박스(파랑) · 증거 광선(빨강)
    shadow_report.json 해 추정 전체 · 메모

사용:
    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/compare_shadow.py
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
from cgiv2 import shadow                           # noqa: E402
from cgiv2.evaluate import FaceScorer             # noqa: E402
from cgiv2.face_restore import FaceTransplanter    # noqa: E402
from cgiv2.mask import get_masker, load_mask       # noqa: E402
from cgiv2.pipeline import Result, Settings         # noqa: E402
from cgiv2.placement import SceneAnalyzer          # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VARIANTS = (
    ("none", {"shadow": False}),
    ("offset", {"shadow": True, "shadow_tool": "offset"}),
    ("contact", {"shadow": True, "shadow_tool": "contact"}),
    ("cast", {"shadow": True, "shadow_tool": "cast"}),
)
PANEL = 460


def load_rgb(p: Path, max_w: int | None = None):
    img = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)
    if max_w and img.shape[1] > max_w:
        h = int(img.shape[0] * max_w / img.shape[1])
        img = cv2.resize(img, (max_w, h), interpolation=cv2.INTER_AREA)
    return img


def fit_w(img, w):
    h = max(1, int(img.shape[0] * w / img.shape[1]))
    return cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA if img.shape[1] > w
                      else cv2.INTER_CUBIC)


def row(imgs, names):
    cells = []
    for im, n in zip(imgs, names):
        c = fit_w(im, PANEL).copy()
        cv2.rectangle(c, (0, 0), (8 + 11 * len(n), 24), (0, 0, 0), -1)
        cv2.putText(c, n, (4, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 1)
        cells.append(c)
    h = max(c.shape[0] for c in cells)
    cells = [np.pad(c, ((0, h - c.shape[0]), (0, 0), (0, 0))) for c in cells]
    gap = np.full((h, 6, 3), 255, np.uint8)
    return np.hstack(sum(([c, gap] for c in cells), [])[:-1])


def draw_sun(bg, people, diag, sun):
    out = bg.copy()
    for x1, y1, x2, y2, *_ in people:
        cv2.rectangle(out, (int(x1), int(y1)), (int(x2), int(y2)), (80, 160, 255), 2)
    H = out.shape[0]
    for e in diag.get("evidence", []):
        a = np.deg2rad(e["angle"])
        fx, fy = e["foot"]
        L = e["len"] * e["h"]
        cv2.arrowedLine(out, (int(fx), int(fy)),
                        (int(fx + L * np.cos(a)), int(fy + L * np.sin(a))),
                        (255, 40, 40), 3, tipLength=0.2)
    txt = ("sun: none - " + diag.get("why", "")) if sun is None else \
        f"sun dir=({sun['dir'][0]:+.2f},{sun['dir'][1]:+.2f}) len={sun['len']:.2f} n={sun['n']} R={sun['R']:.2f}"
    cv2.putText(out, txt.encode("ascii", "replace").decode(), (10, H - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)
    return out


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default=str(root / "work" / "placed"))
    ap.add_argument("--out", default=str(root / "outputs" / "shadow"))
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--obj-dir", default="D:/JungPra/pythonpra/CGI/objects")
    ap.add_argument("--mask-dir", default=str(root / "work" / "masks"))
    ap.add_argument("--models", default=str(root / "work" / "models"))
    ap.add_argument("--min-evidence", type=int, default=2,
                    help="해로 인정할 최소 그림자 증거 인원 (estimate_sun)")
    a = ap.parse_args()

    work, out = Path(a.work), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    keys = sorted(p.name[:-len("_meta.json")] for p in work.glob("*_meta.json"))
    if a.only:
        keys = [k for k in keys if any(f"__{n}" in k for n in a.only)]

    print(f"{len(keys)}건\n모델 로딩 (BiRefNet · YuNet/SFace · Mask2Former · DETR)...", flush=True)
    t0 = time.time()
    masker = get_masker("birefnet_hr")
    md = Path(a.models)
    scorer = FaceScorer(md / "face_detection_yunet_2023mar.onnx",
                        md / "face_recognition_sface_2021dec.onnx")
    transplanter = FaceTransplanter(scorer)
    analyzer = SceneAnalyzer()
    print(f"  {time.time()-t0:.1f}초\n")

    report = []
    for k in keys:
        meta = json.loads((work / f"{k}_meta.json").read_text(encoding="utf-8"))
        ref = load_rgb(Path(a.obj_dir) / meta["object_file"], meta["obj_width"])
        rm = load_mask(Path(a.mask_dir) / f"{Path(meta['object_file']).stem}.png")
        if rm.shape != ref.shape[:2]:
            rm = cv2.resize(rm, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_NEAREST)
        bg = load_rgb(work / f"{k}_bg.png")
        tar = (cv2.imread(str(work / f"{k}_tar.png"), cv2.IMREAD_GRAYSCALE) > 128).astype(np.uint8)
        raw = np.load(work / f"{k}_raw.npy")
        sizes = np.load(work / f"{k}_extra_sizes.npy")
        cbox = np.load(work / f"{k}_crop_box.npy")

        # 해는 **원본** 배경에서 읽는다 — 합성본에서는 우리 인물이 검출된다.
        scene = analyzer.analyze(bg)
        sun, diag = shadow.estimate_sun(bg, scene.people, scene.ground,
                                        min_evidence=a.min_evidence)
        cv2.imwrite(str(out / f"{k}_sun.png"), draw_sun(bg, scene.people, diag, sun)[:, :, ::-1])

        s = meta["settings"]
        imgs, notes_all = {}, {}
        for name, over in VARIANTS:
            st = Settings(steps=s["steps"], cfg=s["cfg"], control_strength=s["strength"],
                          seed=s["seed"], tar_crop_ratio=s["tar_crop_ratio"],
                          normalize_object=s["normalize_object"], feather=s["feather"],
                          face_restore=True, paste="person", sun=sun, **over)
            res = Result(image=bg, region=tar, raw=raw, extra_sizes=sizes, crop_box=cbox)
            img = res.repost(bg, st, ref_image=ref, ref_mask=rm,
                             transplanter=transplanter, masker=masker)
            imgs[name] = img
            notes_all[name] = list(res.notes)
            cv2.imwrite(str(out / f"{k}_{name}.png"), img[:, :, ::-1])

        # 시트 — 전체 + 발 주변 (키의 ±0.7 가로, 발 위 0.35 ~ 아래 0.3)
        ys, xs = np.nonzero(tar)
        H, W = tar.shape
        th = ys.max() - ys.min()
        fx, fy = xs.mean(), ys.max()
        y1, y2 = max(0, int(fy - 0.35 * th)), min(H, int(fy + 0.3 * th))
        x1, x2 = max(0, int(fx - 0.7 * th)), min(W, int(fx + 0.7 * th))
        names = [n for n, _ in VARIANTS]
        parts = [row([imgs[n] for n in names], names),
                 row([imgs[n][y1:y2, x1:x2] for n in names], [f"{n} feet" for n in names])]
        wmax = max(p.shape[1] for p in parts)
        parts = [np.pad(p, ((0, 10), (0, wmax - p.shape[1]), (0, 0)), constant_values=255)
                 for p in parts]
        cv2.imwrite(str(out / f"{k}_sheet.png"), np.vstack(parts)[:, :, ::-1])

        short = k.split("__")[-1][:22]
        if sun is None:
            print(f"{short}  사람 {len(scene.people)} · 해 없음 — {diag.get('why')}")
        else:
            print(f"{short}  사람 {len(scene.people)} · 해 dir=({sun['dir'][0]:+.2f},{sun['dir'][1]:+.2f})"
                  f" len={sun['len']:.2f} beta={[round(b, 2) for b in sun['beta']]} n={sun['n']} R={sun['R']:.2f}")
        for e in diag.get("evidence", []):
            print(f"     증거 키 {e['h']:.0f}px  방향 {e['angle']:.0f}°  어둡기 {e['dark']:.2f}  길이 {e['len']:.2f}")
        for n in names:
            if notes_all[n]:
                print(f"     {n}: {' / '.join(notes_all[n])}")
        report.append({"key": k, "people": len(scene.people), "sun": sun,
                       "diag": {kk: v for kk, v in diag.items()}, "notes": notes_all})

    (out / "shadow_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    print(f"\n저장: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
