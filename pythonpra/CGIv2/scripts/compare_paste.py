"""되붙이기 비교 — crop / box / person_nofg / person. CGI venv 전용, 확산 없음.

gen_placed.py 가 남긴 raw(512 모델 출력)를 `Result.repost()`로 네 방식씩
후처리한다. 모두 얼굴 이식을 켠다 — 되붙이기 방식만 다르다.
person_nofg 는 경계색 제거(Blur-Fusion)를 끈 것이다.

재는 곳: 크롭 안 · 인물 밖 (= 생성이 배경을 바꿀 수 있었던 곳)
    선명도    라플라시안 분산, 원본 대비 %. 100% 면 원본 그대로
    변화량    원본과의 평균 절대차 (0~255)
    정체성    SFace (얼굴 이식 후). 세 방식이 같아야 정상

산출물 (outputs/pasted/)
    <키>_<방식>.png
    <키>_sheet.png         전체 · 디테일 · 머리 · 머리카락 경계 · 발 확대
    <키>_alpha.png         person 방식의 인물 알파
    paste_metrics.json

사용:
    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/compare_paste.py
    D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/compare_paste.py --only W01
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
from cgiv2 import paste                            # noqa: E402
from cgiv2.evaluate import FaceScorer             # noqa: E402
from cgiv2.face_restore import FaceTransplanter    # noqa: E402
from cgiv2.mask import get_masker, load_mask       # noqa: E402
from cgiv2.pairs import crop_back                  # noqa: E402
from cgiv2.pipeline import Result, Settings         # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# (이름, Settings 덮어쓸 값). person_nofg 는 경계색 제거(Blur-Fusion)를 끈 것.
VARIANTS = (
    ("crop", {"paste": "crop"}),
    ("box", {"paste": "box"}),
    ("person_nofg", {"paste": "person", "paste_fg": "none"}),
    ("person", {"paste": "person"}),
)
MODES = tuple(n for n, _ in VARIANTS)
PANEL = 460


def load_rgb(p: Path, max_w: int | None = None):
    img = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)
    if max_w and img.shape[1] > max_w:
        h = int(img.shape[0] * max_w / img.shape[1])
        img = cv2.resize(img, (max_w, h), interpolation=cv2.INTER_AREA)
    return img


def lap_var(gray: np.ndarray, sel: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_32F)[sel].var())


def detail_window(bg, crop_box, person, frac=0.3):
    """크롭 안 · 인물 밖에서 원본 디테일(|라플라시안| 합)이 가장 큰 정사각 창."""
    cy1, cy2, cx1, cx2 = [int(v) for v in crop_box]
    lap = np.abs(cv2.Laplacian(cv2.cvtColor(bg, cv2.COLOR_RGB2GRAY), cv2.CV_32F))
    ii = cv2.integral(lap)
    ip = cv2.integral(person.astype(np.uint8))
    s = int(frac * min(cy2 - cy1, cx2 - cx1))
    step = max(8, s // 6)

    def box_sum(t, y, x):
        return t[y + s, x + s] - t[y, x + s] - t[y + s, x] + t[y, x]

    best = None
    for y in range(cy1, cy2 - s + 1, step):
        for x in range(cx1, cx2 - s + 1, step):
            if box_sum(ip, y, x) > 0.05 * s * s:
                continue
            v = box_sum(ii, y, x)
            if best is None or v > best[0]:
                best = (v, y, x)
    if best is None:
        return None
    _, y, x = best
    return y, y + s, x, x + s


def clip_box(y1, y2, x1, x2, H, W):
    return max(0, int(y1)), min(H, int(y2)), max(0, int(x1)), min(W, int(x2))


def fit_w(img, w):
    h = max(1, int(img.shape[0] * w / img.shape[1]))
    return cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA if img.shape[1] > w
                      else cv2.INTER_CUBIC)


def label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0, 0), (8 + 11 * len(text), 24), (0, 0, 0), -1)
    cv2.putText(out, text, (4, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 1)
    return out


def row(imgs, names):
    cells = [label(fit_w(im, PANEL), n) for im, n in zip(imgs, names)]
    h = max(c.shape[0] for c in cells)
    cells = [np.pad(c, ((0, h - c.shape[0]), (0, 0), (0, 0))) for c in cells]
    gap = np.full((h, 6, 3), 255, np.uint8)
    return np.hstack(sum(([c, gap] for c in cells), [])[:-1])


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default=str(root / "work" / "placed"))
    ap.add_argument("--out", default=str(root / "outputs" / "pasted"))
    ap.add_argument("--only", nargs="*", default=None, help="배경 접두사 (예: W01)")
    ap.add_argument("--obj-dir", default="D:/JungPra/pythonpra/CGI/objects")
    ap.add_argument("--mask-dir", default=str(root / "work" / "masks"))
    ap.add_argument("--models", default=str(root / "work" / "models"))
    ap.add_argument("--mask-tool", default="birefnet_hr")
    a = ap.parse_args()

    work, out = Path(a.work), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    keys = sorted(p.name[:-len("_meta.json")] for p in work.glob("*_meta.json"))
    if a.only:
        keys = [k for k in keys if any(f"__{n}" in k for n in a.only)]
    if not keys:
        print("대상이 없습니다.")
        return 1

    print(f"{len(keys)}건 · 분할 도구 {a.mask_tool}\n모델 로딩...", flush=True)
    t0 = time.time()
    masker = get_masker(a.mask_tool)
    md = Path(a.models)
    scorer = FaceScorer(md / "face_detection_yunet_2023mar.onnx",
                        md / "face_recognition_sface_2021dec.onnx")
    transplanter = FaceTransplanter(scorer)
    print(f"  {time.time()-t0:.1f}초\n")

    report = {"mask_tool": a.mask_tool, "rows": []}
    for k in keys:
        meta = json.loads((work / f"{k}_meta.json").read_text(encoding="utf-8"))
        ref = load_rgb(Path(a.obj_dir) / meta["object_file"], meta["obj_width"])
        rm = load_mask(Path(a.mask_dir) / f"{Path(meta['object_file']).stem}.png")
        if rm.shape != ref.shape[:2]:
            rm = cv2.resize(rm, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_NEAREST)

        bg = load_rgb(work / f"{k}_bg.png")
        raw = np.load(work / f"{k}_raw.npy")
        sizes = np.load(work / f"{k}_extra_sizes.npy")
        cbox = np.load(work / f"{k}_crop_box.npy")
        tar = (cv2.imread(str(work / f"{k}_tar.png"), cv2.IMREAD_GRAYSCALE) > 128).astype(np.uint8)
        H, W = bg.shape[:2]
        s = meta["settings"]

        # 측정 영역을 모든 방식에 공통으로 쓰려고 인물 알파를 한 번 따로 뽑는다.
        # _finish 가 person 방식에서 뽑는 것과 같은 입력이다 — feather 적용
        # crop_back 뒤 얼굴 이식까지 한 것 (이식이 되붙이기보다 먼저다).
        base = crop_back(raw, bg, sizes, cbox, feather=s["feather"])
        st0 = Settings()
        base, _ok = transplanter.transplant(
            ref, rm, base, head_room=st0.face_head_room, torso_ratio=st0.face_torso_ratio,
            width_ratio=st0.face_width_ratio, feather=st0.face_feather,
            color_match=st0.face_color_match, blend=st0.face_blend)
        t1 = time.time()
        alpha, info = paste.person_alpha(
            base, tar, cbox, masker, margin=st0.paste_margin,
            min_aspect=st0.paste_min_aspect, thresh=st0.paste_thresh,
            min_inside=st0.paste_min_inside, grow=st0.paste_grow)
        t_seg = time.time() - t1
        if alpha is None:
            print(f"{k}: 인물 분할 실패 — {info['why']}")
            continue
        cv2.imwrite(str(out / f"{k}_alpha.png"), (alpha * 255).astype(np.uint8))

        ys, xs = np.nonzero(tar)
        ty1, ty2, tx1, tx2 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        th, tw = ty2 - ty1, tx2 - tx1
        person = (alpha > 0.5).astype(np.uint8)
        r = max(3, int(0.02 * th))
        near = cv2.dilate(person, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1,) * 2))
        cy1, cy2, cx1, cx2 = [int(v) for v in cbox]
        sel = np.zeros((H, W), bool)
        sel[cy1 + 8:cy2 - 8, cx1 + 8:cx2 - 8] = True       # crop_back 페더 띠 제외
        sel &= near == 0
        g_bg = cv2.cvtColor(bg, cv2.COLOR_RGB2GRAY)
        lv_bg = lap_var(g_bg, sel)

        imgs, rowm = {}, {"key": k, "segment_sec": round(t_seg, 2),
                         "crop_box": [cy1, cy2, cx1, cx2],
                         "crop_area": round((cy2 - cy1) * (cx2 - cx1) / (H * W), 4),
                         "person_area": round(float(person.mean()), 4),
                         "segment": {kk: (list(v) if isinstance(v, tuple) else v)
                                     for kk, v in info.items()},
                         "modes": {}}
        for mode, over in VARIANTS:
            st = Settings(steps=s["steps"], cfg=s["cfg"], control_strength=s["strength"],
                          seed=s["seed"], tar_crop_ratio=s["tar_crop_ratio"],
                          normalize_object=s["normalize_object"], feather=s["feather"],
                          face_restore=True, **over)
            res = Result(image=base, region=tar, raw=raw, extra_sizes=sizes, crop_box=cbox)
            img = res.repost(bg, st, ref_image=ref, ref_mask=rm,
                             transplanter=transplanter, masker=masker)
            imgs[mode] = img
            cv2.imwrite(str(out / f"{k}_{mode}.png"), img[:, :, ::-1])

            g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            mad = float(np.abs(img.astype(np.float32) - bg.astype(np.float32))[sel].mean())
            face = scorer.score(ref, img)
            rowm["modes"][mode] = {
                "sharp_pct": round(100 * lap_var(g, sel) / max(lv_bg, 1e-6), 1),
                "mad": round(mad, 2),
                "face": None if face is None else round(float(face), 4),
                "notes": list(res.notes),
            }
        report["rows"].append(rowm)

        # ── 시트 ──────────────────────────────────────────────────────
        dw = detail_window(bg, cbox, near)
        head = clip_box(ty1 - 0.05 * th, ty1 + 0.35 * th, tx1 - 0.35 * tw, tx2 + 0.35 * tw, H, W)
        feet = clip_box(ty2 - 0.18 * th, ty2 + 0.08 * th, tx1 - 0.4 * tw, tx2 + 0.4 * tw, H, W)
        # 머리카락 경계 — 테두리(생성 배경색 번짐)가 가장 잘 보이는 곳
        pys, pxs = np.nonzero(person)
        ptop = pys.min()
        hx = pxs[pys < ptop + 0.12 * (pys.max() - ptop)].mean()
        hair = clip_box(ptop - 0.03 * th, ptop + 0.17 * th, hx - 0.12 * th, hx + 0.12 * th, H, W)
        parts = [row([imgs[m] for m in MODES], [f"{m} (full)" for m in MODES])]
        for name, bx in (("detail", dw), ("head", head), ("hair", hair), ("feet", feet)):
            if bx is None:
                continue
            y1, y2, x1, x2 = bx
            parts.append(row([imgs[m][y1:y2, x1:x2] for m in MODES],
                             [f"{m} {name}" for m in MODES]))
        wmax = max(p.shape[1] for p in parts)
        parts = [np.pad(p, ((0, 10), (0, wmax - p.shape[1]), (0, 0)), constant_values=255)
                 for p in parts]
        cv2.imwrite(str(out / f"{k}_sheet.png"), np.vstack(parts)[:, :, ::-1])

        short = k.split("__")[-1][:22]
        print(f"{short}  크롭 {rowm['crop_area']:.0%} · 인물 {rowm['person_area']:.1%}"
              f" · 분할 {t_seg:.1f}초 · 덩어리 남김 {info['kept']} 버림 {info['dropped']}"
              f"{' · ⚠ 창 가장자리' if info['touches_window'] else ''}")
        for mode in MODES:
            mm = rowm["modes"][mode]
            f = f"{mm['face']:.4f}" if mm["face"] is not None else "미검출"
            print(f"   {mode:11s} 선명도 {mm['sharp_pct']:6.1f}%  변화량 {mm['mad']:6.2f}"
                  f"  정체성 {f}  {' / '.join(mm['notes'])}")
        print()

    (out / "paste_metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
