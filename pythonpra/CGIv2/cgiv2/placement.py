"""배치 위치 추정 — 발은 걸을 수 있는 지면 위에, 크기는 원근에 맞게.

문제 (2026-09-21~22 의 모든 결과)
    prep.place_box(center=(0.62, 0.5), height_ratio=0.45) 가 장면을 모른 채
    고정 좌표에 박스를 놓는다. 배경마다 지면 높이와 원근이 달라서 인물의 발이
    전경 수풀 위에 떠 있거나(콜로세움), 주변 사람들보다 거인처럼 크게 나왔다.

두 갈래로 푼다
    어디에 서나   걸을 수 있는 지면을 의미 분할로 찾는다.
                  Mask2Former Swin-S (ADE20K 150 클래스) — floor · road ·
                  sidewalk · grass · sand · path ... 을 "지면"으로 본다.
    얼마나 크나   장면 속 사람들로 원근을 맞춘다 (Hoiem, Efros, Hebert,
                  "Putting Objects in Perspective", CVPR 2006).
                  지면에 선 사람의 이미지상 키 h 는 발 위치 v 에 선형이다.

                        h = r · (v − v0)

                  v0 = 지평선 행, r = 사람 키 / 카메라 높이. DETR 로 사람들을
                  찾아 (v, h) 쌍에 직선을 맞추면 두 값이 한꺼번에 나온다.
                  눈높이로 찍은 사진이면 r ≈ 1 이다 — 서 있는 사람들의 머리가
                  전부 지평선에 걸린다는, 사진에서 잘 알려진 성질이다.

사람이 부족할 때의 대체 (정확도 순)
    3명 이상   Theil-Sen 직선 맞춤 (이상치에 강함)          method="fit"
    1~2명      r=1(눈높이) 가정, 머리 윗변 중앙값 = 지평선   method="eye_level"
    0명        r=1 가정, 가장 높은 수평면(지면+물) 윗변      method="surface_top"
               (2026-09-23 전까지는 지면만 봐서 이름이 ground_top 이었다)

아래로 갈수록 추정이 거칠다. info["method"] 로 무엇을 썼는지 남긴다.

모델 선택 기록 (2026-09-23)
    처음엔 nvidia/segformer-b2-finetuned-ade-512-512 를 쓰려 했으나 .bin
    가중치뿐이라, transformers 4.55 가 torch<2.6 에서 .bin 로딩을 보안상
    거부했다(CVE-2025-32434). torch 업그레이드는 환경 설정이라 하지 않았고
    검사 우회도 하지 않았다. safetensors 로 배포되는 Mask2Former Swin-S 로
    바꿨다 — ADE20K mIoU 도 오히려 높다(약 51 대 46).

이 모듈은 가중치 라인과 무관하다 (🟢). tar_mask 를 만드는 전처리일 뿐이다.

**CGI venv 전용** — AnyDoor venv 의 transformers 4.19.2 에는 Mask2Former 가
없다. 여기서 만든 tar_mask 를 PNG 로 저장해 AnyDoor venv 가 읽는다
(predict/generate 를 나눴던 것과 같은 방식).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

#: 걸을 수 있는 지면으로 보는 ADE20K 라벨 (이름으로 매칭한다 — 인덱스를
#: 하드코딩하지 않는다). bridge 는 뺐다: 시드니 하버 브리지처럼 "서 있는
#: 곳"이 아니라 배경 구조물로 잡히는 경우가 많다.
WALKABLE = {
    "floor", "road", "grass", "sidewalk", "earth", "rug", "field", "sand",
    "path", "stairs", "runway", "stairway", "dirt track", "land", "step", "pier",
}

#: 지평선 추정에 쓰는 수평면 — 걸을 수 있는 지면 + 물.
#: 지평선은 **모든 수평면보다 위**에 있다. 그래서 보이는 수평면 중 가장 높은
#: 것의 윗변이 지평선의 가장 좋은 추정치(상한)다. 바다가 수평선까지 이어지면
#: 그게 곧 지평선이다. 처음엔 지면만 봤다가, 산책로가 난간에서 끝나고 그
#: 너머로 바다 수평선이 보이는 W05 산토리니에서 지평선을 너무 낮게 잡아
#: 인물이 작아졌다(2026-09-23).
HORIZON_SURFACES = WALKABLE | {"water", "sea", "lake", "river"}


@dataclass
class Perspective:
    v0: float           # 지평선 행 (px). 이미지 밖(음수 등)일 수 있다
    r: float            # 사람 키 / 카메라 높이
    method: str         # fit | eye_level | ground_top
    n_used: int = 0     # 맞춤에 쓴 사람 수
    residual: float | None = None   # fit 일 때 중앙 절대 잔차 (px)

    def height_at(self, v: float) -> float:
        """발 행 v 에 선 사람의 이미지상 키 (px)."""
        return max(0.0, self.r * (v - self.v0))

    def feet_for_height(self, h: float) -> float:
        """키 h 가 되려면 발이 놓여야 할 행."""
        return self.v0 + h / max(self.r, 1e-6)


@dataclass
class Scene:
    ground: np.ndarray                    # 0/1 uint8 (H, W) — 걸을 수 있는 지면
    people: list[tuple[float, float, float, float, float]]   # (x1, y1, x2, y2, score)
    shape: tuple[int, int]
    labels_present: dict[str, float] = field(default_factory=dict)  # 라벨 -> 면적비
    surfaces: np.ndarray | None = None    # 0/1 — 지면 + 물 (지평선 추정용)


class SceneAnalyzer:
    """지면 분할(Mask2Former) + 사람 검출(DETR)."""

    SEG_MODEL = "facebook/mask2former-swin-small-ade-semantic"
    DET_MODEL = "facebook/detr-resnet-50"

    def __init__(self, device: str = "cuda", det_threshold: float = 0.7,
                 seg_model: str | None = None, det_model: str | None = None):
        import torch
        from transformers import (AutoImageProcessor, DetrForObjectDetection,
                                  DetrImageProcessor,
                                  Mask2FormerForUniversalSegmentation)

        self.torch = torch
        self.device = device
        self.det_threshold = det_threshold

        sm = seg_model or self.SEG_MODEL
        self.seg_proc = AutoImageProcessor.from_pretrained(sm)
        self.seg = Mask2FormerForUniversalSegmentation.from_pretrained(sm).to(device).eval()
        id2label = self.seg.config.id2label
        self.id2label = {int(k): v for k, v in id2label.items()}
        self.walk_ids = {i for i, n in self.id2label.items() if n.lower() in WALKABLE}
        self.surface_ids = {i for i, n in self.id2label.items()
                            if n.lower() in HORIZON_SURFACES}

        dm = det_model or self.DET_MODEL
        self.det_proc = DetrImageProcessor.from_pretrained(dm)
        self.det = DetrForObjectDetection.from_pretrained(dm).to(device).eval()
        self.person_ids = {int(k) for k, v in self.det.config.id2label.items()
                           if v.lower() == "person"}

    def segment(self, rgb: np.ndarray) -> np.ndarray:
        """ADE20K 라벨 맵 (H, W) int."""
        H, W = rgb.shape[:2]
        inp = self.seg_proc(images=rgb, return_tensors="pt").to(self.device)
        with self.torch.no_grad():
            out = self.seg(**inp)
        lab = self.seg_proc.post_process_semantic_segmentation(out, target_sizes=[(H, W)])[0]
        return lab.cpu().numpy().astype(np.int32)

    def detect_people(self, rgb: np.ndarray) -> list[tuple[float, float, float, float, float]]:
        H, W = rgb.shape[:2]
        inp = self.det_proc(images=rgb, return_tensors="pt").to(self.device)
        with self.torch.no_grad():
            out = self.det(**inp)
        res = self.det_proc.post_process_object_detection(
            out, target_sizes=[(H, W)], threshold=self.det_threshold)[0]
        people = []
        for s, l, b in zip(res["scores"], res["labels"], res["boxes"]):
            if int(l) in self.person_ids:
                x1, y1, x2, y2 = [float(v) for v in b.tolist()]
                people.append((x1, y1, x2, y2, float(s)))
        return people

    def analyze(self, rgb: np.ndarray, min_surface: float = 0.005) -> Scene:
        """min_surface  이보다 작은 수평면 조각은 지평선 추정에서 뺀다
                        (하늘 반사를 물로 잘못 잡은 점 같은 것)."""
        lab = self.segment(rgb)
        ground = np.isin(lab, list(self.walk_ids)).astype(np.uint8)
        H, W = lab.shape

        surf = np.isin(lab, list(self.surface_ids)).astype(np.uint8)
        n, cc, stats, _ = cv2.connectedComponentsWithStats(surf, 8)
        keep = np.zeros(n, bool)
        keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_surface * H * W
        surfaces = keep[cc].astype(np.uint8)

        present = {}
        ids, cnt = np.unique(lab, return_counts=True)
        for i, c in zip(ids, cnt):
            frac = c / (H * W)
            if frac >= 0.01:
                present[self.id2label.get(int(i), str(i))] = float(frac)
        return Scene(ground=ground, people=self.detect_people(rgb),
                     shape=(H, W), labels_present=present, surfaces=surfaces)


# ── 원근 맞춤 ───────────────────────────────────────────────────────────
def _feet_on_ground(box, ground: np.ndarray, frac: float = 0.3) -> bool:
    """발 아래 좁은 띠에 지면이 frac 이상 있는가.

    하반신이 가려진 사람(수풀·난간 뒤)은 박스 아랫변이 발이 아니라 가림막에
    걸린다. 그 아래가 지면이 아니면 키를 과소 추정하므로 걸러낸다.
    """
    x1, y1, x2, y2 = [int(round(v)) for v in box[:4]]
    H, W = ground.shape
    h = max(1, y2 - y1)
    band = max(4, int(h * 0.05))
    ya, yb = max(0, y2 - 2), min(H, y2 + band)
    xa, xb = max(0, x1), min(W, x2)
    if yb <= ya or xb <= xa:
        return False
    return float(ground[ya:yb, xa:xb].mean()) >= frac


def fit_perspective(scene: Scene, *, min_h: float = 12.0, min_hw: float = 1.5,
                    r_range: tuple[float, float] = (0.05, 3.0)) -> Perspective:
    """장면 속 사람들로 지평선과 카메라 높이 비를 맞춘다.

    min_hw  박스 세로/가로가 이보다 작으면 앉았거나 웅크린 사람으로 보고 뺀다.
            (2026-09-23 K09 해운대: 앉은 두 사람이 키를 절반으로 끌어내려
            기울기 r 을 왜곡했다. 서 있는 사람 박스는 보통 2~4 이다.)
    """
    H, W = scene.shape
    usable = []
    for p in scene.people:
        x1, y1, x2, y2, _ = p
        h = y2 - y1
        if h < min_h:
            continue                     # 너무 작으면 박스 오차가 키 오차를 삼킨다
        if y2 >= H - 2:
            continue                     # 아래가 잘린 사람 — 발이 안 보인다
        if h / max(x2 - x1, 1.0) < min_hw:
            continue                     # 앉은 사람 — 서 있는 키가 아니다
        usable.append(p)

    on_ground = [p for p in usable if _feet_on_ground(p, scene.ground)]
    pts = on_ground if len(on_ground) >= 3 else usable

    if len(pts) >= 3:
        v = np.array([p[3] for p in pts], np.float64)
        h = np.array([p[3] - p[1] for p in pts], np.float64)
        slopes = []
        for i in range(len(v)):
            for j in range(i + 1, len(v)):
                dv = v[j] - v[i]
                if abs(dv) > 5:
                    slopes.append((h[j] - h[i]) / dv)
        if slopes:
            a = float(np.median(slopes))
            b = float(np.median(h - a * v))
            if r_range[0] <= a <= r_range[1]:
                v0 = -b / a
                if -1.0 * H <= v0 <= 1.2 * H:
                    resid = float(np.median(np.abs(h - (a * v + b))))
                    return Perspective(v0=v0, r=a, method="fit",
                                       n_used=len(pts), residual=resid)

    if len(pts) >= 1:
        # 눈높이 가정: 머리 윗변 = 지평선
        v0 = float(np.median([p[1] for p in pts]))
        return Perspective(v0=v0, r=1.0, method="eye_level", n_used=len(pts))

    # 사람이 없다 — 보이는 수평면(지면 + 물) 중 가장 높은 것의 윗변을 지평선으로.
    # 지평선은 모든 수평면보다 위에 있으므로 이건 상한이다. 바다가 수평선까지
    # 이어지면 정확히 지평선이다. (이전 이름 ground_top — 지면만 봤다.)
    src = scene.surfaces if scene.surfaces is not None and scene.surfaces.any() else scene.ground
    rows = np.nonzero(src.any(axis=1))[0]
    v0 = float(np.percentile(rows, 2)) if len(rows) else 0.45 * H
    return Perspective(v0=v0, r=1.0, method="surface_top", n_used=0)


# ── 배치 ────────────────────────────────────────────────────────────────
def place_feet(bg_shape, feet_xy: tuple[float, float], height_px: float,
               aspect: float) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """발 위치를 박스 아랫변 중앙에 맞춰 tar_mask 를 만든다.

    prep.place_box 는 박스 **중심**을 받는다. 지면에 세우려면 **아랫변**을
    발에 맞춰야 해서 따로 만든다. 박스가 이미지를 벗어나면 잘린다.
    """
    H, W = bg_shape[:2]
    fx, fy = feet_xy
    h = int(round(height_px))
    w = max(1, int(round(h * aspect)))
    y2 = int(round(fy))
    y1 = y2 - h
    x1 = int(round(fx - w / 2))
    x2 = x1 + w
    y1c, y2c = max(0, y1), min(H, y2)
    x1c, x2c = max(0, x1), min(W, x2)
    m = np.zeros((H, W), np.uint8)
    if y2c > y1c and x2c > x1c:
        m[y1c:y2c, x1c:x2c] = 1
    return m, (y1c, y2c, x1c, x2c)


def auto_place(
    scene: Scene,
    persp: Perspective,
    aspect: float,
    *,
    target_height_ratio: float = 0.40,
    x_ratios: tuple[float, ...] = (1 / 3, 2 / 3),
    max_height_ratio: float = 0.78,
    min_area: float = 0.01,
    max_people_overlap: float = 0.05,
    step: int = 2,
) -> tuple[np.ndarray | None, dict]:
    """발을 지면에, 키를 원근에 맞춰 놓는다.

    target_height_ratio  원하는 인물 키 (배경 높이 대비). 원근이 허락하는
                         범위에서 이 크기에 가장 가까운 깊이를 고른다.
    x_ratios             원하는 가로 위치 후보. 기본은 삼등분선(1/3, 2/3) —
                         사진가는 랜드마크를 가운데 둔다. 처음엔 x=0.5 였는데
                         에펠탑·피사탑을 정확히 가렸다(2026-09-23). 후보마다
                         가장 가까운 자리를 찾아 더 가까운 쪽을 쓴다.
    max_height_ratio     0.78 — process_pairs 의 타깃 최대 변 관문(0.8) 회피.
    min_area             0.01 — 관문 면적 하한. 원근상 작아야 하는 자리라도
                         이보다 작으면 보고만 한다(억지로 키우면 거인이 된다).
    max_people_overlap   기존 사람 박스와 겹치는 비율 상한. 처음엔 겹침 회피가
                         없어 K07 골목·K09 해변에서 사람 위에 사람을 얹었다.
    step                 후보 지면 픽셀을 이만큼 건너뛰며 본다 (속도).

    반환: (tar_mask 또는 None, info). 놓을 자리가 없으면 None.
    """
    H, W = scene.shape
    info: dict = {"method": persp.method, "v0": persp.v0, "r": persp.r,
                  "n_people": len(scene.people), "n_used": persp.n_used,
                  "residual": persp.residual}

    target_h = target_height_ratio * H
    v_want = persp.feet_for_height(target_h)
    info.update(v_want=float(v_want))

    # 발 폭만큼 지면을 가로로 깎아, 발 전체가 지면 위에 오게 한다.
    foot_w = max(3, int(target_h * 0.12) | 1)
    g = cv2.erode(scene.ground, cv2.getStructuringElement(cv2.MORPH_RECT, (foot_w, 5)))
    ys, xs = np.nonzero(g[::step, ::step])
    ys, xs = ys * step, xs * step
    if len(ys) == 0:
        info["error"] = "걸을 수 있는 지면이 없다"
        return None, info

    hs = persp.r * (ys - persp.v0)
    ws = hs * aspect
    # 지평선 아래(키 양수) · 머리가 화면 안 · 관문 최대 변 · 좌우로 안 잘림
    ok = ((hs > 0) & (ys - hs >= 0) & (hs <= max_height_ratio * H)
          & (xs - ws / 2 >= 0) & (xs + ws / 2 <= W))
    if not ok.any():
        info["error"] = "원근상 서 있을 수 있는 지면 픽셀이 없다"
        return None, info
    ys, xs, hs, ws = ys[ok], xs[ok], hs[ok], ws[ok]

    # 기존 사람과의 겹침 — 적분 영상으로 후보 전체를 한 번에 잰다
    if scene.people:
        pm = np.zeros((H, W), np.uint8)
        for x1, y1, x2, y2, _ in scene.people:
            pm[int(max(0, y1)):int(min(H, y2)), int(max(0, x1)):int(min(W, x2))] = 1
        I = cv2.integral(pm).astype(np.int64)
        by1 = np.clip((ys - hs).astype(int), 0, H)
        by2 = np.clip(ys.astype(int), 0, H)
        bx1 = np.clip((xs - ws / 2).astype(int), 0, W)
        bx2 = np.clip((xs + ws / 2).astype(int), 0, W)
        s = I[by2, bx2] - I[by1, bx2] - I[by2, bx1] + I[by1, bx1]
        area = np.maximum((by2 - by1) * (bx2 - bx1), 1)
        free = (s / area) <= max_people_overlap
        info["excluded_by_people"] = int((~free).sum())
        if not free.any():
            info["error"] = "기존 사람과 겹치지 않는 자리가 없다"
            return None, info
        ys, xs, hs, ws = ys[free], xs[free], hs[free], ws[free]

    best = None
    for xr in x_ratios:
        x_want = xr * W
        d = ((ys - v_want) / H) ** 2 + ((xs - x_want) / W) ** 2
        k = int(np.argmin(d))
        if best is None or d[k] < best[0]:
            best = (float(d[k]), k, xr)
    dmin, k, xr = best
    v, x, h = float(ys[k]), float(xs[k]), float(hs[k])
    info.update(x_want=float(xr * W), x_ratio_chosen=xr,
                feet=(x, v), height_px=h, height_ratio=h / H,
                snap_dist=float(np.sqrt(dmin)))

    mask, box = place_feet((H, W), (x, v), h, aspect)
    area = float(mask.sum()) / (H * W)
    info.update(box=box, area=area, gate_ok=bool(min_area < area < 0.64))
    if area <= min_area:
        info["warn"] = (f"원근상 이 자리의 사람은 면적 {area:.2%} — 관문 하한 "
                        f"{min_area:.0%} 미만. 전경에 지면이 없는 배경일 수 있다")
    return mask, info


def draw_overlay(rgb: np.ndarray, scene: Scene, persp: Perspective,
                 mask: np.ndarray | None, info: dict) -> np.ndarray:
    """확인용 그림 — 지면(초록), 사람(파랑), 지평선(빨강), 배치(노랑)."""
    out = rgb.copy()
    H, W = scene.shape
    g = scene.ground.astype(bool)
    out[g] = (out[g] * 0.55 + np.array([60, 200, 60]) * 0.45).astype(np.uint8)
    for x1, y1, x2, y2, _ in scene.people:
        cv2.rectangle(out, (int(x1), int(y1)), (int(x2), int(y2)), (60, 120, 255), 2)
    if -H < persp.v0 < 2 * H:
        vy = int(np.clip(persp.v0, 0, H - 1))
        cv2.line(out, (0, vy), (W - 1, vy), (255, 40, 40), 3)
    if mask is not None and "box" in info:
        y1, y2, x1, x2 = info["box"]
        cv2.rectangle(out, (x1, y1), (x2, y2), (255, 220, 0), 4)
        fx, fy = info["feet"]
        cv2.circle(out, (int(fx), int(fy)), 10, (255, 220, 0), -1)
    return out
