"""그림자 — 인물을 땅에 붙인다. (2026-09-26)

되붙이기(paste person)가 발밑 생성 영역을 버리면서 AnyDoor 가 발밑에 남긴
희미한 어둠도 같이 사라졌다. 그걸 되살리지 않고 **새로 그린다** — AnyDoor 의
발밑은 그림자가 아니라 새로 그린 바닥이었다 (paste.py 진단 참고).

두 종류
    contact  접지 그림자 (ambient occlusion). 발바닥이 땅에 닿는 곳의 어둠.
             빛 방향과 무관하게 **항상** 생긴다 — 흐린 날에도, 그늘에서도.
    cast     투영 그림자. 해가 비칠 때 몸이 땅에 드리우는 그림자. 방향·길이·
             색이 장면의 해에 달려 있어 **틀리면 없느니만 못하다.**
             장면 속 기존 사람들의 그림자에서 읽어온다 (estimate_sun).

기존 postproc.add_contact_shadow 는 이름과 달리 실루엣을 통째로 평행이동한다
('offset'). 서 있는 사람에게 쓰면 몸 옆에 사람 모양 얼룩이 뜬다.

전부 순수 후처리다 (🟢). 가중치와 무관하다.
"""
from __future__ import annotations

import cv2
import numpy as np

FEET_BAND = 0.04        # 발 = 실루엣 맨 아래 키의 4%
CONTACT_WIDTH = 1.25    # 넓은 타원 가로 반경 = 발 폭/2 × 1.25
CONTACT_HEIGHT = 0.03   # 넓은 타원 세로 반경 = 키 × 0.03
CONTACT_CORE = 0.3      # 좁은 타원 세로 반경 = 넓은 것 × 0.3 (가로는 발 폭/2)
CAST_MIN_DY = 0.08      # 그림자 방향의 세로 성분 하한 — 0 이면 아핀이 특이행렬이 된다


def feet_line(mask: np.ndarray):
    """(발 선 y, 발 왼쪽 x, 발 오른쪽 x, 키) 또는 None. 발 = 실루엣 아래 FEET_BAND."""
    ys, xs = np.nonzero(mask)
    if len(ys) < 50:
        return None
    top, bot = int(ys.min()), int(ys.max())
    h = bot - top + 1
    band = ys >= bot - FEET_BAND * h
    return bot, int(xs[band].min()), int(xs[band].max()), h


def contact_shadow(image: np.ndarray, mask: np.ndarray, *, strength: float = 0.5,
                   width: float = CONTACT_WIDTH, height: float = CONTACT_HEIGHT) -> np.ndarray:
    """발밑 접지 그림자. 가우시안 타원 두 겹을 곱으로 합친다.

    넓고 옅은 것(발 폭 × width, 키 × height)은 몸이 하늘빛을 가리는 어둠,
    좁고 진한 것(발 폭, 그 0.3배 두께)은 발바닥이 땅에 닿는 선이다.
    인물 자신은 어둡게 하지 않는다.

    width·height 는 물건마다 다르다 — 사람은 발 두 개라 얇고, 자동차는 차체 밑
    전체가 어둡다 (2026-09-26 자동차: height 0.03 이면 차 밑이 밝게 떠 보였다).
    """
    f = feet_line(mask)
    if f is None or strength <= 0:
        return image
    y_f, xl, xr, h = f
    H, W = mask.shape
    xc = (xl + xr) / 2
    half = max((xr - xl) / 2, 0.05 * h)
    a1, b1 = half * width, height * h
    a2, b2 = half, b1 * CONTACT_CORE

    y0, y1 = max(0, int(y_f - 3 * b1)), min(H, int(y_f + 3 * b1) + 1)
    x0, x1 = max(0, int(xc - 2 * a1)), min(W, int(xc + 2 * a1) + 1)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    s1 = np.exp(-2 * (((xx - xc) / a1) ** 2 + ((yy - y_f) / b1) ** 2))
    s2 = np.exp(-2 * (((xx - xc) / a2) ** 2 + ((yy - y_f) / b2) ** 2))
    dark = 1 - (1 - 0.6 * strength * s1) * (1 - strength * s2)
    dark *= 1 - mask[y0:y1, x0:x1].astype(np.float32)

    out = image.astype(np.float32)
    out[y0:y1, x0:x1] *= (1 - dark)[:, :, None]
    return np.clip(out, 0, 255).astype(np.uint8)


def cast_shadow(
    image: np.ndarray,
    mask: np.ndarray,
    direction,
    *,
    length: float = 0.6,
    beta=None,
    strength: float = 0.45,
    soft: tuple[float, float] = (0.002, 0.008),
    fade: float = 0.2,
) -> np.ndarray:
    """투영 그림자. 실루엣을 발 선에 붙인 채 땅으로 눕힌다 (아핀 하나).

        x' = x + (y_f − y)·length·dx
        y' = y_f + (y_f − y)·length·dy

    발(y = y_f)은 제자리에 있고, 키 H 인 머리는 발에서 방향 d 로 H·length 만큼
    떨어진다. 몸의 가로 폭은 그대로 남는다.

    direction  그림자 방향 (이미지 좌표, y 아래가 +). 세로 성분이 0 이면
               행렬이 특이해지므로 |dy| ≥ CAST_MIN_DY 로 민다
    beta       그림자 속 색 / 볕 색 (RGB, 0~1). 장면에서 잰 값을 주면 그림자 색이
               장면의 기존 그림자와 같아진다. None 이면 1 − strength 회색
    soft       흐림 σ = 키 × (발 쪽, 끝 쪽). 멀어질수록 반그림자가 넓어진다.
               해의 시직경이 0.53° 라 반그림자 폭은 거리 × 0.009 뿐이다 — 머리
               그림자도 거의 선명하다. 처음 값 (0.006, 0.03) 은 흐린 날 수준이라
               옆으로 누운 얇은 그림자(K05, 약 18px)가 녹아 없어졌다
    fade       끝으로 갈수록 옅어지는 비율 (끝에서 1 − fade)
    """
    f = feet_line(mask)
    if f is None:
        return image
    y_f, xl, xr, h = f
    H, W = mask.shape
    dx, dy = float(direction[0]), float(direction[1])
    if abs(dy) < CAST_MIN_DY:
        dy = CAST_MIN_DY if dy >= 0 else -CAST_MIN_DY
    n = np.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    k = length

    M = np.float32([[1, -k * dx, k * dx * y_f],
                    [0, -k * dy, (1 + k * dy) * y_f]])
    m = mask.astype(np.float32)
    sh = cv2.warpAffine(m, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    near = cv2.GaussianBlur(sh, (0, 0), max(1.0, soft[0] * h))
    far = cv2.GaussianBlur(sh, (0, 0), max(1.0, soft[1] * h))

    xc = (xl + xr) / 2
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    t = np.clip(((xx - xc) * dx + (yy - y_f) * dy) / (k * h + 1e-6), 0, 1)
    matte = ((1 - t) * near + t * far) * (1 - fade * t) * (1 - m)

    b = np.full(3, 1 - strength, np.float32) if beta is None else np.clip(
        np.asarray(beta, np.float32), 0.05, 1.0)
    out = image.astype(np.float32) * (1 - matte[:, :, None] * (1 - b[None, None, :]))
    return np.clip(out, 0, 255).astype(np.uint8)


def estimate_sun(
    image: np.ndarray,
    people,
    ground: np.ndarray,
    *,
    min_h: float = 40,
    step_deg: int = 5,
    dark_min: float = 0.3,
    min_evidence: int = 2,
    min_concentration: float = 0.9,
) -> tuple[dict | None, dict]:
    """장면 속 사람들의 그림자로 해를 읽는다. 반환 (해 | None, 진단).

    사람마다 발에서 사방으로 광선을 쏴 **가장 어두운 방향**을 찾는다.
        기준 밝기   발 주변 고리(키 × 0.35~0.9)의 지면 L 중앙값
        광선        키 × 0.05~0.5 구간의 지면 L 평균, step_deg 간격
        어둡기      1 − 광선 평균 / 기준
    어둡기가 dark_min 이상이면 그 사람을 증거로 삼는다. 증거가 min_evidence 명
    이상이고 방향이 한곳에 모일 때(평균 단위벡터 길이 ≥ min_concentration,
    0.9 ≈ 흩어짐 ±25°)만 해가 있다고 본다. 흐린 날의 바닥 무늬(W01 타일)는
    사람마다 어두운 방향이 달라 여기서 걸러진다.

    해 dict
        dir     그림자 방향 (이미지 단위벡터, y 아래가 +) — 증거의 원형 평균
        len     그림자 길이 / 키 — 증거의 중앙값
        beta    그림자 속 RGB / 볕 RGB — Chuang et al. 2003 shadow matting 의 β
        n, R    증거 수, 집중도

    한계 — 우리 인물이 선 자리가 볕인지 그늘인지는 모른다 (그늘 속 W09 앞마당).
    바닥 재질 차이와 그늘을 밝기만으로 구분할 수 없어서다. 켜고 끄는 건 호출부 몫.
    """
    H, W = ground.shape
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    L = cv2.GaussianBlur(lab[:, :, 0].astype(np.float32), (0, 0), 1.5)
    rgb = image.astype(np.float32)

    occ = np.zeros((H, W), bool)
    for x1, y1, x2, y2, *_ in people:
        occ[max(0, int(y1) - 3):min(H, int(y2) + 4), max(0, int(x1) - 3):min(W, int(x2) + 4)] = True
    usable = ground.astype(bool) & ~occ

    def samples(fx, fy, radii, angles):
        rr, aa = np.meshgrid(radii, angles, indexing="ij")
        xs = np.round(fx + rr * np.cos(aa)).astype(int)
        ys = np.round(fy + rr * np.sin(aa)).astype(int)
        ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
        xs, ys = xs[ok], ys[ok]
        keep = usable[ys, xs]
        return ys[keep], xs[keep]

    angles = np.deg2rad(np.arange(0, 360, step_deg))
    evidence, diag = [], {"people": len(people), "checked": 0}
    for x1, y1, x2, y2, *_ in people:
        h = y2 - y1
        if h < min_h or y2 >= H - 2:
            continue
        diag["checked"] += 1
        fx, fy = (x1 + x2) / 2, y2

        ys, xs = samples(fx, fy, np.linspace(0.35 * h, 0.9 * h, 12), angles)
        if len(ys) < 30:
            continue
        L_ref = float(np.median(L[ys, xs]))
        rgb_ref = np.median(rgb[ys, xs], axis=0)

        d = np.arange(0.05 * h, 0.5 * h, max(1.0, 0.01 * h))
        best = (0.0, None)
        for a in angles:
            ys, xs = samples(fx, fy, d, [a])
            if len(ys) < 8:
                continue
            dark = 1 - float(L[ys, xs].mean()) / max(L_ref, 1e-6)
            if dark > best[0]:
                best = (dark, a)
        dark, a = best
        if a is None or dark < dark_min:
            continue

        # 길이 — 그 방향으로 멀리까지 보고 어둠이 절반 이상 풀리는 곳
        dd = np.arange(0.05 * h, 1.5 * h, max(1.0, 0.01 * h))
        prof = []
        for r in dd:
            ys, xs = samples(fx, fy, [r], [a])
            prof.append(L[ys, xs].mean() if len(ys) else np.nan)
        prof = np.array(prof, np.float32)
        if np.all(np.isnan(prof)):
            continue
        lo = np.nanmin(prof)
        thr = lo + 0.5 * (L_ref - lo)
        i_min = int(np.nanargmin(prof))
        after = np.nonzero(np.nan_to_num(prof[i_min:], nan=-1) > thr)[0]
        k = float(dd[i_min + after[0]] / h) if len(after) else float(dd[-1] / h)

        ys, xs = samples(fx, fy, np.linspace(0.05 * h, max(0.06 * h, 0.8 * k * h), 10), [a])
        if len(ys) < 3:
            continue
        beta = np.clip(rgb[ys, xs].mean(0) / np.maximum(rgb_ref, 1e-6), 0.05, 1.0)
        evidence.append({"angle": float(np.rad2deg(a)), "dark": dark, "len": k,
                         "beta": beta.tolist(), "L_ref": L_ref, "h": float(h),
                         "foot": [float(fx), float(fy)]})

    diag["evidence"] = evidence
    if len(evidence) < min_evidence:
        diag["why"] = f"그림자 증거 {len(evidence)}명 < {min_evidence}"
        return None, diag
    u = np.array([[np.cos(np.deg2rad(e["angle"])), np.sin(np.deg2rad(e["angle"]))]
                  for e in evidence])
    mean = u.mean(0)
    R = float(np.hypot(*mean))
    diag["R"] = R
    if R < min_concentration:
        diag["why"] = f"방향이 흩어짐 (집중도 {R:.2f} < {min_concentration})"
        return None, diag

    sun = {
        "dir": (mean / R).tolist(),
        "len": float(np.median([e["len"] for e in evidence])),
        "beta": np.median([e["beta"] for e in evidence], axis=0).tolist(),
        "n": len(evidence), "R": R,
    }
    return sun, diag


def apply(image: np.ndarray, mask: np.ndarray, tool: str = "contact", *,
          contact_strength: float = 0.5, contact_width: float = CONTACT_WIDTH,
          contact_height: float = CONTACT_HEIGHT, sun: dict | None = None,
          cast_strength: float = 0.45, notes: list[str] | None = None) -> np.ndarray:
    """contact | cast. cast 는 접지 그림자 위에 투영 그림자를 더한다.
    sun 이 없으면 cast 를 못 그리고 contact 만 한다 (notes 에 남김).
    """
    out = image
    if tool == "cast":
        if sun is None:
            if notes is not None:
                notes.append("그림자 cast: 해 정보 없음 → contact 만")
        else:
            out = cast_shadow(out, mask, sun["dir"], length=sun["len"],
                              beta=sun.get("beta"), strength=cast_strength)
    return contact_shadow(out, mask, strength=contact_strength,
                          width=contact_width, height=contact_height)
