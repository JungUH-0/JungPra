"""되붙이기 — 생성 크롭 중 어디까지 원본 배경 위에 얹을지. (2026-09-23)

AnyDoor 추론 스크립트(run_inference.py:126 crop_back)는 512 크롭 **전체**를
되붙인다. 크롭은 인물 박스의 1.1~1.2배를 다시 2배(tar_crop_ratio)로 넓힌
정사각이라, 인물이 크면 화면의 절반 이상이 저해상도 재생성본으로 바뀐다.
그 안에 랜드마크가 있으면 랜드마크가 뭉개진다 (W01 에펠탑).

    배치 검증 4건 실측 (크롭 안 · 인물 박스 밖)
        크롭 면적     화면의 41 / 45 / 51 / 67 %
        선명도        원본의 13 / 9 / 13 / 30 %   (라플라시안 분산)
        색 변화       ΔL -2.6 ~ +2.5, Δa -0.27 ~ +0.05, Δb +0.21 ~ +0.98

    **문제는 색이 아니라 해상도다.** 그래서 색 보정 없이 영역만 줄인다.

세 가지 방식 (Settings.paste)

    crop     크롭 전체. run_inference.py 와 같다 (기존 동작, 기본값)
    box      배치 박스만. run_gradio_demo.py:140-143 "keep background
             unchanged" 와 같은 발상 — 원저자도 데모에서는 이렇게 했다.
             모델이 필요 없어 AnyDoor venv 에서도 된다
    person   생성물에서 인물을 분할해 그 알파로만 얹는다. 인물 밖은 원본
             픽셀이 그대로 남는다. 분할 모델이 필요하다 (CGI venv).
             경계 픽셀에 섞인 생성 배경색은 estimate_foreground 로 걷어낸다

발밑 생성 영역은 가져오지 않는다. AnyDoor 는 발밑에 그림자를 그리기보다
바닥 무늬를 새로 그린다 (W01 타일 배열이 바뀜, W09 자갈이 매끈해짐).
발밑 밝기비(생성/원본)가 0.88 / 0.92 / 1.14 / 1.23 으로 들쭉날쭉해 그림자로
옮길 신호가 못 된다. 접지 그림자가 필요하면 Settings.shadow 를 켠다 —
person 방식에서는 박스가 아니라 인물 실루엣 기준으로 드리운다.
"""
from __future__ import annotations

import cv2
import numpy as np

BOX_EXPAND = 1.2     # 원본 데모의 expand_bbox [1.1, 1.2] 상한. 생성물이 박스를 약간 넘는다
FG_RADII = (90, 6)   # Blur-Fusion 두 단계 반경 — 논문 기본값 그대로


def _bbox(mask: np.ndarray):
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return None
    return int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1


def edge_ramp(h: int, w: int, feather: int) -> np.ndarray:
    """가장자리 feather 픽셀에서 0→1 로 오르는 사각 알파. feather=0 이면 전부 1."""
    alpha = np.ones((h, w), np.float32)
    f = min(feather, h // 2, w // 2)
    if f > 0:
        ramp = np.linspace(0.0, 1.0, f, dtype=np.float32)
        alpha[:f, :] *= ramp[:, None]
        alpha[-f:, :] *= ramp[::-1][:, None]
        alpha[:, :f] *= ramp[None, :]
        alpha[:, -f:] *= ramp[::-1][None, :]
    return alpha


def box_alpha(region: np.ndarray, crop_box, *, expand: float = BOX_EXPAND,
              feather: int = 0) -> np.ndarray | None:
    """배치 박스(bbox × expand, 크롭 안으로 클램프)만 1 인 알파. 모델 없음."""
    b = _bbox(region)
    if b is None:
        return None
    y1, y2, x1, x2 = b
    yc, xc = (y1 + y2) / 2, (x1 + x2) / 2
    h, w = (y2 - y1) * expand, (x2 - x1) * expand
    cy1, cy2, cx1, cx2 = [int(v) for v in crop_box]
    by1, by2 = max(cy1, int(yc - h / 2)), min(cy2, int(yc + h / 2))
    bx1, bx2 = max(cx1, int(xc - w / 2)), min(cx2, int(xc + w / 2))

    a = np.zeros(region.shape, np.float32)
    a[by1:by2, bx1:bx2] = edge_ramp(by2 - by1, bx2 - bx1, feather)
    return a


def person_alpha(
    composite: np.ndarray,
    region: np.ndarray,
    crop_box,
    masker,
    *,
    margin: float = 0.08,
    min_aspect: float = 0.6,
    thresh: float = 0.5,
    min_inside: float = 0.5,
    grow: float = 0.01,
) -> tuple[np.ndarray | None, dict]:
    """생성물에서 배치 박스에 선 인물의 알파 (0~1, 원본 크기).

    composite   crop_back 이 끝난 원본 크기 합성 (인물이 그려진 것)
    region      배치 마스크 (0/1). 인물이 여기 그려졌다
    crop_box    생성 크롭 y1,y2,x1,x2. 이 밖에는 생성된 것이 없다
    masker      alpha(RGB) -> 0~1 또는 binary(RGB) -> 0/1 을 가진 분할 도구

    창      박스를 키의 margin 만큼 사방으로 넓히고, 가로가 세로의 min_aspect
            보다 좁으면 넓힌다. 분할 모델은 창을 정사각으로 늘려 넣으므로
            1:3 같은 좁은 창은 사람이 옆으로 3배 늘어난 채 들어간다.
    선택    창에는 다른 관광객·랜드마크도 들어온다. thresh 로 이진화한 덩어리
            중 **면적의 min_inside 이상이 박스 안에 있는 것만** 남긴다.
    경계    남긴 덩어리를 키의 grow 만큼 팽창한 범위 안에서 모델의 연속
            알파를 그대로 쓴다 — 머리카락 같은 반투명 경계가 산다.

    실패하면 (None, 사유) — 호출부가 다른 방식으로 되돌아간다.
    """
    b = _bbox(region)
    if b is None:
        return None, {"why": "배치 영역 없음"}
    ty1, ty2, tx1, tx2 = b
    th, tw = ty2 - ty1, tx2 - tx1
    H, W = region.shape

    m = int(round(margin * th))
    wy1, wy2 = ty1 - m, ty2 + m
    half = max(tw + 2 * m, min_aspect * (wy2 - wy1)) / 2
    xc = (tx1 + tx2) / 2
    wx1, wx2 = int(xc - half), int(xc + half)
    cy1, cy2, cx1, cx2 = [int(v) for v in crop_box]
    wy1, wy2 = max(wy1, cy1, 0), min(wy2, cy2, H)
    wx1, wx2 = max(wx1, cx1, 0), min(wx2, cx2, W)

    win = composite[wy1:wy2, wx1:wx2]
    if hasattr(masker, "alpha"):
        a = masker.alpha(win).astype(np.float32)
    else:
        a = masker.binary(win).astype(np.float32)

    fg = (a > thresh).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
    inbox = np.zeros(fg.shape, bool)
    inbox[ty1 - wy1:ty2 - wy1, tx1 - wx1:tx2 - wx1] = True
    inside = np.bincount(lab[inbox].ravel(), minlength=n)
    area = stats[:, cv2.CC_STAT_AREA]
    keep = inside >= min_inside * area
    keep[0] = False
    if not keep.any():
        return None, {"why": "박스 안 인물 미검출", "window": (wy1, wy2, wx1, wx2)}

    sel = keep[lab].astype(np.uint8)
    r = max(1, int(round(grow * th)))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    a = a * cv2.dilate(sel, k).astype(np.float32)

    out = np.zeros((H, W), np.float32)
    out[wy1:wy2, wx1:wx2] = a
    info = {
        "window": (wy1, wy2, wx1, wx2),
        "kept": int(keep.sum()), "dropped": int(n - 1 - keep.sum()),
        "area": float((out > thresh).mean()),
        # 창 가장자리에 닿으면 인물이 창 밖으로 나간 것 — 잘린 채 붙는다
        "touches_window": bool(sel[0].any() or sel[-1].any()
                               or sel[:, 0].any() or sel[:, -1].any()),
    }
    return out, info


def estimate_foreground(image: np.ndarray, alpha: np.ndarray,
                        radii: tuple[int, ...] = FG_RADII) -> np.ndarray:
    """경계 픽셀에서 생성 배경색을 걷어내고 인물 색만 추정한다 (Blur-Fusion).

    Forte & Pitié, "Approximate Fast Foreground Colour Estimation", ICIP 2021.

    경계 픽셀은 I = αF + (1-α)B_생성 이다. 그대로 원본 위에 얹으면 B_생성 이
    테두리로 남는다 — 밝은 벽 앞에서 생성된 머리카락을 원본의 어두운 기둥
    앞에 얹으면 흰 테두리가 생긴다 (W09). F 를 추정해 αF + (1-α)B_원본 으로
    합성하면 테두리 색이 원본 배경을 따른다.

    박스 블러 두 번(반경 90 → 6)뿐이라 수십 ms 다. 알파가 있는 범위만 계산한다.
    반환은 0~255 float32, image 와 같은 크기 (알파 밖은 image 그대로).
    """
    out = image.astype(np.float32).copy()
    b = _bbox(alpha > 0)
    if b is None:
        return out
    p = max(radii)
    H, W = alpha.shape
    y1, y2 = max(0, b[0] - p), min(H, b[1] + p)
    x1, x2 = max(0, b[2] - p), min(W, b[3] + p)

    img = out[y1:y2, x1:x2] / 255
    a = alpha[y1:y2, x1:x2, None].astype(np.float32)
    F, B = img, img
    for r in radii:
        ba = cv2.blur(a, (r, r))[:, :, None]
        bF = cv2.blur(F * a, (r, r)) / (ba + 1e-5)
        bB = cv2.blur(B * (1 - a), (r, r)) / ((1 - ba) + 1e-5)
        F = np.clip(bF + a * (img - a * bF - (1 - a) * bB), 0, 1)
        B = bB
    out[y1:y2, x1:x2] = F * 255
    return out


def compose(composite: np.ndarray, background: np.ndarray, alpha: np.ndarray,
            fg: np.ndarray | None = None) -> np.ndarray:
    """alpha 만큼만 합성을, 나머지는 원본 배경을 쓴다.

    fg 를 주면 합성 대신 그 색을 쓴다 (estimate_foreground 결과).
    """
    a = alpha[:, :, None]
    F = composite.astype(np.float32) if fg is None else fg
    out = background.astype(np.float32) * (1 - a) + F * a
    return np.clip(out, 0, 255).astype(np.uint8)
