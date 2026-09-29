"""후처리 — AnyDoor 가 비워둔 자리.

AnyDoor 에는 명시적 후처리가 없다. 빠뜨린 게 아니라 **확산이 암묵적으로
처리한다**는 설계다. 512 크롭 전체를 재생성하므로 그 안에서 조명이 저절로
맞는다고 본 것이다. 그래서 crop_back 이 25줄짜리 단순 대입이다.

그 전제가 맞는지는 베이스라인을 돌려봐야 안다. **측정 전에 다 켜면 안 된다.**
다섯 개를 한꺼번에 켜면 어느 것이 도움이고 어느 것이 해인지 구분되지 않고,
AnyDoor 가 이미 한 보정 위에 덧칠해 이중 보정이 된다.

그래서 이 모듈의 모든 함수는 **기본이 꺼짐**이고 하나씩 켤 수 있다.

가져오지 못한 것 하나 — 정체성 복원(Frequency Separation)
    CGI 에서 통했던 이유는 SD 1.5 inpainting 이 물체의 픽셀 위치를 대체로
    유지했기 때문이다. 원본 고주파를 같은 좌표에 되붙일 수 있었다.
    AnyDoor 는 동영상 쌍으로 **자세를 바꾸도록** 학습됐다. 참조와 결과 사이에
    픽셀 대응이 없으므로 되붙일 좌표가 존재하지 않는다.
    예외는 강체 + shape_control=True 로 실루엣을 고정한 경우뿐이고, 그때도
    부분적이다. 여기서는 구현하지 않는다.
"""
from __future__ import annotations

import cv2
import numpy as np


def _region_stats(img_lab: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    sel = mask.astype(bool)
    if sel.sum() < 50:
        return np.zeros(3, np.float32), np.ones(3, np.float32)
    px = img_lab[sel].astype(np.float32)
    return px.mean(0), px.std(0) + 1e-6


def match_color_lab(
    image: np.ndarray,
    region: np.ndarray,
    surround: np.ndarray,
    *,
    strength: float = 0.5,
) -> np.ndarray:
    """생성 영역의 색·밝기를 주변 통계에 맞춘다 (LAB 평균/표준편차 매칭).

    region     보정 대상 (생성된 물체 영역, 0/1)
    surround   기준이 되는 주변 배경 (0/1)
    strength   0 이면 원본 유지, 1 이면 완전 이동. 0.5 는 절반만.

    AnyDoor 가 이미 조명을 맞추려 시도하므로 strength 를 1.0 으로 두면
    이중 보정이 된다. 낮게 시작해서 올리는 쪽이 안전하다.

    LAB 을 쓰는 이유는 명도(L)와 색도(a,b)가 분리돼 색상 왜곡이 적기 때문이다.
    """
    if strength <= 0:
        return image
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB).astype(np.float32)
    m_src, s_src = _region_stats(lab, region)
    m_dst, s_dst = _region_stats(lab, surround)

    sel = region.astype(bool)
    px = lab[sel]
    moved = (px - m_src) / s_src * s_dst + m_dst
    lab[sel] = px * (1 - strength) + moved * strength
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)


def surround_ring(mask: np.ndarray, inner: int = 6, outer: int = 40) -> np.ndarray:
    """생성 영역 바깥의 고리. match_color_lab 의 기준 영역으로 쓴다.

    전체 배경을 기준으로 삼으면 멀리 있는 하늘·건물 색까지 끌어와 엉뚱해진다.
    접지면 근처만 보는 것이 맞다.
    """
    k_in = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (inner * 2 + 1,) * 2)
    k_out = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (outer * 2 + 1,) * 2)
    grown = cv2.dilate(mask.astype(np.uint8), k_in)
    far = cv2.dilate(mask.astype(np.uint8), k_out)
    return ((far > 0) & (grown == 0)).astype(np.uint8)


def seam_score(image: np.ndarray, mask: np.ndarray, band: int = 5) -> float:
    """경계 이음매의 세기. 낮을수록 자연스럽다.

    경계 안쪽 띠와 바깥쪽 띠의 LAB 평균 거리를 잰다. 페더링이나 색 정합이
    실제로 효과가 있었는지 숫자로 보려면 이게 필요하다.
    """
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (band * 2 + 1,) * 2)
    m = mask.astype(np.uint8)
    inner = ((m > 0) & (cv2.erode(m, k) == 0)).astype(np.uint8)
    outer = ((cv2.dilate(m, k) > 0) & (m == 0)).astype(np.uint8)
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB).astype(np.float32)
    a, _ = _region_stats(lab, inner)
    b, _ = _region_stats(lab, outer)
    return float(np.linalg.norm(a - b))


def estimate_light_direction(image: np.ndarray, mask: np.ndarray) -> tuple[float, float]:
    """물체 주변 밝기 기울기로 광원 방향을 추정한다. 단위 벡터 (dx, dy).

    학습이 필요 없는 근사다. 그림자를 넣을지 판단하거나, 넣는다면 어느 쪽으로
    늘릴지 정하는 데 쓴다. 정확한 물리 추정이 아니라 방향 힌트다.
    """
    ring = surround_ring(mask, inner=4, outer=60)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=5)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=5)
    sel = ring.astype(bool)
    if sel.sum() < 50:
        return 0.0, 1.0
    v = np.array([gx[sel].mean(), gy[sel].mean()], np.float32)
    n = np.linalg.norm(v)
    return (0.0, 1.0) if n < 1e-6 else tuple((v / n).tolist())


def add_contact_shadow(
    image: np.ndarray,
    mask: np.ndarray,
    *,
    direction: tuple[float, float] = (0.3, 1.0),
    length: float = 0.25,
    blur: int = 31,
    opacity: float = 0.35,
) -> np.ndarray:
    """접지 그림자를 기하 근사로 넣는다.

    실루엣을 방향으로 밀어 눌러 붙이고 흐린 뒤 곱하기로 어둡게 한다. 학습형
    모델이 아니라 근사이므로, **AnyDoor 가 이미 그림자를 그렸는지 먼저 확인**
    해야 한다. 이중으로 들어가면 오히려 어색해진다.
    """
    if opacity <= 0 or length <= 0:
        return image
    H, W = mask.shape
    y1 = np.nonzero(mask.any(1))[0]
    if len(y1) == 0:
        return image
    h = y1.max() - y1.min() + 1

    dx, dy = direction
    off = np.float32([[1, 0, dx * h * length], [0, 1, dy * h * length]])
    sh = cv2.warpAffine(mask.astype(np.float32), off, (W, H))
    sh = cv2.GaussianBlur(sh, (blur | 1, blur | 1), 0)
    sh = np.clip(sh, 0, 1) * opacity
    sh[mask.astype(bool)] = 0            # 물체 위에는 얹지 않는다

    out = image.astype(np.float32) * (1 - sh[:, :, None])
    return np.clip(out, 0, 255).astype(np.uint8)


def match_color_hist(
    image: np.ndarray,
    region: np.ndarray,
    surround: np.ndarray,
    *,
    strength: float = 0.5,
) -> np.ndarray:
    """히스토그램 CDF 매칭. match_color_lab 의 대안 도구.

    평균/표준편차만 맞추는 LAB 매칭과 달리 **분포 전체를 옮긴다.** 조명이
    복잡한 장면(역광, 얼룩진 그림자)에서 더 잘 맞을 수 있고, 반대로 물체
    고유의 명암 대비까지 뭉갤 위험도 있다.

    skimage 없이 numpy 로만 구현한다 (CGI venv 에 skimage 가 없다).
    """
    if strength <= 0:
        return image
    src_sel, dst_sel = region.astype(bool), surround.astype(bool)
    if src_sel.sum() < 50 or dst_sel.sum() < 50:
        return image

    out = image.astype(np.float32).copy()
    for c in range(3):
        s = image[:, :, c][src_sel]
        d = image[:, :, c][dst_sel]
        s_hist = np.bincount(s.astype(np.uint8), minlength=256).astype(np.float64)
        d_hist = np.bincount(d.astype(np.uint8), minlength=256).astype(np.float64)
        s_cdf = np.cumsum(s_hist) / max(s_hist.sum(), 1)
        d_cdf = np.cumsum(d_hist) / max(d_hist.sum(), 1)
        lut = np.interp(s_cdf, d_cdf, np.arange(256)).astype(np.float32)
        mapped = lut[s.astype(np.uint8)]
        out[:, :, c][src_sel] = s * (1 - strength) + mapped * strength
    return np.clip(out, 0, 255).astype(np.uint8)


def blend_poisson(
    composite: np.ndarray,
    background: np.ndarray,
    region: np.ndarray,
    *,
    mixed: bool = False,
) -> np.ndarray:
    """포아송 블렌딩 (cv2.seamlessClone). 페더링의 대안 도구.

    경사도를 보존하면서 색을 주변에 맞춘다. 이음매가 확실히 사라지는 대신
    **물체 전체의 색이 주변 쪽으로 끌려간다.** 로고·라벨 색이 바뀔 수 있어
    2안(시계·가방)에서는 위험하다.

    mixed=True 는 MIXED_CLONE — 배경의 텍스처를 더 살린다. 질감이 강한
    배경(석조, 자갈)에서 NORMAL 보다 나을 수 있다.
    """
    m = (region.astype(np.uint8) * 255)
    ys, xs = np.nonzero(region)
    if len(ys) == 0:
        return composite
    center = (int((xs.min() + xs.max()) / 2), int((ys.min() + ys.max()) / 2))
    mode = cv2.MIXED_CLONE if mixed else cv2.NORMAL_CLONE
    try:
        return cv2.seamlessClone(composite, background, m, center, mode)
    except cv2.error:
        # 영역이 이미지 경계에 닿으면 seamlessClone 이 실패한다
        return composite


def apply(
    image: np.ndarray,
    region: np.ndarray,
    *,
    color_match: float = 0.0,
    color_tool: str = "lab",
    shadow: bool = False,
    shadow_opacity: float = 0.35,
) -> np.ndarray:
    """후처리 묶음. 기본은 전부 꺼짐 — 베이스라인 측정용.

    베이스라인에서 실패 유형을 세고, 그 유형에 해당하는 것만 켠다.
        조명이 안 맞음  -> color_match 를 0.3 부터 올린다
        떠 보임         -> shadow=True
        경계 티         -> crop_back(feather=...) 쪽에서 처리한다
    """
    out = image
    if color_match > 0:
        ring = surround_ring(region)
        fn = {"lab": match_color_lab, "hist": match_color_hist}[color_tool]
        out = fn(out, region, ring, strength=color_match)
    if shadow:
        d = estimate_light_direction(out, region)
        out = add_contact_shadow(out, region, direction=d, opacity=shadow_opacity)
    return out
