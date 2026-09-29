"""객체별 정규화 — 관문을 통과시키기 위한 전처리.

process_pairs 맨 앞의 네 관문은 객체마다 다른 이유로 걸린다.

    시계    면적 하한 1%.  전신 사진에서 0.1% 대라 탈락.
    가방    연결성 0.90.   어깨끈이 가늘어 마스크가 끊기면 탈락.
    자동차  면적 상한 64%. 차 사진은 프레임의 70~90% 를 채워 탈락.
    사람    대체로 통과.

그리고 BaseDataset.__getitem__ 은 예외를 통째로 삼키고 무한 재시도한다.
탈락하면 에러 없이 멈추므로, **여기서 미리 맞춰 넣는다.**

주의 — 참조를 얼마나 타이트하게 자르느냐가 최종 참조 해상도를 결정한다.
process_pairs 가 다시 1.2배 확대 후 224 로 줄이므로, 타이트할수록 물체가 224
안에서 크게 잡힌다. 다만 어디까지가 최적인지는 측정 대상이다.
"""
from __future__ import annotations

import cv2
import numpy as np


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        raise ValueError("빈 마스크")
    return int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1


def area_ratio(mask: np.ndarray) -> float:
    return float(mask.sum()) / (mask.shape[0] * mask.shape[1])


def crop_to_area(
    image: np.ndarray,
    mask: np.ndarray,
    *,
    target: float = 0.20,
    min_margin: float = 0.15,
) -> tuple[np.ndarray, np.ndarray]:
    """면적비가 너무 작을 때 — 물체 주변으로 크롭해 비율을 끌어올린다.

    시계·반지처럼 전신 사진에서 1% 미만인 객체에 쓴다. 물체 bbox 를 중심으로
    정사각 창을 잡되, 면적비가 target 근처가 되도록 창 크기를 정한다.

    min_margin 은 bbox 대비 최소 여백이다. 물체에 딱 붙여 자르면 process_pairs
    가 다시 1.2배 확대할 때 잘려나간다.
    """
    y1, y2, x1, x2 = _bbox(mask)
    bh, bw = y2 - y1, x2 - x1
    obj_px = float(mask.sum())

    # 원하는 창 넓이 = 물체 픽셀 / 목표 비율
    want = max(obj_px / max(target, 1e-6), bh * bw * (1 + min_margin) ** 2)
    side = int(np.sqrt(want))
    side = max(side, int(max(bh, bw) * (1 + min_margin)))

    cy, cx = (y1 + y2) // 2, (x1 + x2) // 2
    H, W = mask.shape
    side = min(side, H, W)
    ty1 = int(np.clip(cy - side // 2, 0, H - side))
    tx1 = int(np.clip(cx - side // 2, 0, W - side))
    return (
        image[ty1:ty1 + side, tx1:tx1 + side].copy(),
        mask[ty1:ty1 + side, tx1:tx1 + side].copy(),
    )


def pad_to_area(
    image: np.ndarray,
    mask: np.ndarray,
    *,
    target: float = 0.45,
    pad_value: int = 255,
) -> tuple[np.ndarray, np.ndarray]:
    """면적비가 너무 클 때 — 여백을 덧대 비율을 낮춘다.

    자동차처럼 프레임의 70~90% 를 채워 상한 64% 에 걸리는 객체에 쓴다.
    잘라내면 물체가 잘리므로 반대로 캔버스를 키운다.

    pad_value=255 는 process_pairs 가 참조 배경을 흰색으로 채우는 것과 맞춘다.
    """
    r = area_ratio(mask)
    if r <= target:
        return image, mask

    H, W = mask.shape
    scale = np.sqrt(r / target)
    nh, nw = int(H * scale), int(W * scale)
    oy, ox = (nh - H) // 2, (nw - W) // 2

    img = np.full((nh, nw, image.shape[2]), pad_value, dtype=image.dtype)
    msk = np.zeros((nh, nw), dtype=mask.dtype)
    img[oy:oy + H, ox:ox + W] = image
    msk[oy:oy + H, ox:ox + W] = mask
    return img, msk


def normalize_object(
    image: np.ndarray,
    mask: np.ndarray,
    *,
    lo: float = 0.02,
    hi: float = 0.55,
    crop_target: float = 0.20,
    pad_target: float = 0.45,
) -> tuple[np.ndarray, np.ndarray, str]:
    """면적비를 관문 안쪽으로 밀어 넣는다. 어느 쪽으로 움직였는지도 돌려준다.

    lo/hi 는 관문(0.01 / 0.64)보다 안쪽으로 잡았다. process_pairs 가 뒤에서
    다시 확대·크롭하므로 경계에 딱 맞춰두면 넘어갈 수 있다.
    """
    r = area_ratio(mask)
    if r < lo:
        image, mask = crop_to_area(image, mask, target=crop_target)
        return image, mask, f"크롭 ({r:.2%} -> {area_ratio(mask):.2%})"
    if r > hi:
        image, mask = pad_to_area(image, mask, target=pad_target)
        return image, mask, f"여백 ({r:.2%} -> {area_ratio(mask):.2%})"
    return image, mask, f"그대로 ({r:.2%})"


def place_box(
    bg_shape: tuple[int, int],
    *,
    center: tuple[float, float],
    height_ratio: float,
    aspect: float,
    shape_mask: np.ndarray | None = None,
) -> np.ndarray:
    """배경에 놓을 자리 마스크를 만든다 — tar_mask.

    center 는 (0~1, 0~1) 정규화 좌표, height_ratio 는 배경 높이 대비 물체 높이,
    aspect 는 가로/세로 비다. 보통은 UI 에서 사용자가 칠하지만, 400쌍 일괄
    생성처럼 무인으로 돌릴 때는 이걸로 만든다.

    shape_mask 를 주면 사각형 대신 그 실루엣을 창에 맞춰 넣는다. 강체를
    shape_control 과 함께 쓸 때 필요하다.

    주의 — 창이 너무 크면 check_region_size(tar, 0.8, 'max') 에 걸린다.
    height_ratio 는 0.8 미만으로 둔다.
    """
    H, W = bg_shape[:2]
    h = int(H * float(np.clip(height_ratio, 0.05, 0.78)))
    w = max(1, int(h * aspect))
    cy, cx = int(H * center[0]), int(W * center[1])

    y1 = int(np.clip(cy - h // 2, 0, max(0, H - h)))
    x1 = int(np.clip(cx - w // 2, 0, max(0, W - w)))
    y2, x2 = min(H, y1 + h), min(W, x1 + w)

    out = np.zeros((H, W), np.uint8)
    if shape_mask is None:
        out[y1:y2, x1:x2] = 1
    else:
        s = cv2.resize(shape_mask.astype(np.uint8), (x2 - x1, y2 - y1),
                       interpolation=cv2.INTER_NEAREST)
        out[y1:y2, x1:x2] = (s > 0).astype(np.uint8)
    return out


def crop_to_face(
    image: np.ndarray,
    mask: np.ndarray,
    face_box,
    *,
    head_room: float = 0.7,
    torso_ratio: float = 2.6,
    width_ratio: float = 2.0,
) -> tuple[np.ndarray, np.ndarray]:
    """얼굴 검출 결과를 기준으로 상반신(흉상) 프레이밍으로 자른다.

    2026-09-22 SFace 실측: 전신 참조가 224 로 줄어들면 얼굴이 17~25px 밖에
    안 남아 얼굴 정체성이 0.107(판정선 0.363의 9%)까지 떨어진다. 얼굴
    주변만 잘라내면 같은 224 예산 안에서 얼굴이 훨씬 크게 잡힐 것이라는
    가설을 검증하기 위한 크롭이다. (scripts/test_upper_body.py)

    face_box    검출기(YuNet) 결과의 앞 4개 값 (x, y, w, h)
    head_room   정수리 위 여백 = 얼굴 높이 x 이 비율
    torso_ratio 크롭 높이 = 얼굴 높이 x 이 비율 (턱 아래로 어깨까지)
    width_ratio 크롭 폭  = 얼굴 높이 x 이 비율 (얼굴 중심 기준 좌우)

    값은 전형적인 흉상 사진 프레이밍을 본뜬 추정치이며 튜닝된 값이 아니다.
    """
    fx, fy, fw, fh = [float(v) for v in face_box[:4]]
    H, W = mask.shape[:2]

    top = max(0, int(fy - fh * head_room))
    bottom = min(H, int(fy + fh + fh * torso_ratio))
    cx = fx + fw / 2
    half_w = fh * width_ratio / 2
    left = max(0, int(cx - half_w))
    right = min(W, int(cx + half_w))

    if bottom <= top or right <= left:
        raise ValueError("크롭 영역이 비었습니다 — face_box 를 확인하십시오")

    return image[top:bottom, left:right].copy(), mask[top:bottom, left:right].copy()


def object_aspect(mask: np.ndarray) -> float:
    """물체 bbox 의 가로/세로 비. place_box 에 넘겨 원본 비율을 지킨다."""
    y1, y2, x1, x2 = _bbox(mask)
    return (x2 - x1) / max(y2 - y1, 1)
