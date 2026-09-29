"""몸 기준 배치 — 2안: 사람 사진 위에 가방·시계·자동차. (2026-09-26)

1안(placement.py)은 **장면**을 보고 사람을 세웠다 — 지면과 원근.
2안은 반대로 **사람의 몸**을 보고 물건을 붙인다 — 가방은 손에, 시계는 손목에.
그래서 관절 위치가 필요하다.

도구 — torchvision Keypoint R-CNN ResNet-50 FPN (COCO 17점).
    CGI venv 에 이미 있는 torchvision 으로 돈다 — 새 패키지가 없다.
    가중치가 .pth 라 transformers 의 torch.load 보안 검사(CVE-2025-32434)와 무관하다.
    ViTPose(transformers) 같은 최신 추정기로 갈아끼울 수 있다 (🟢 — 가중치 라인과 무관).

관절 점수는 확률이 아니라 히트맵 로짓이다. torchvision 예제의 시각화 기준(2)을 쓴다.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

KP_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]
KP = {n: i for i, n in enumerate(KP_NAMES)}
SKELETON = [("left_shoulder", "right_shoulder"), ("left_hip", "right_hip"),
            ("left_shoulder", "left_hip"), ("right_shoulder", "right_hip"),
            ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
            ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"),
            ("left_hip", "left_knee"), ("left_knee", "left_ankle"),
            ("right_hip", "right_knee"), ("right_knee", "right_ankle")]
KP_MIN_SCORE = 2.0      # 관절 신뢰 기준 (히트맵 로짓)


@dataclass
class Person:
    box: tuple[float, float, float, float]    # x1, y1, x2, y2
    kp: np.ndarray                            # (17, 3) x, y, 점수
    score: float

    @property
    def height(self) -> float:
        return self.box[3] - self.box[1]

    def point(self, name: str, min_score: float = KP_MIN_SCORE) -> np.ndarray | None:
        x, y, s = self.kp[KP[name]]
        return None if s < min_score else np.array([x, y], np.float32)


class PoseEstimator:
    """Keypoint R-CNN. 사진에서 가장 큰 사람 한 명의 관절을 돌려준다."""

    def __init__(self, device: str = "cuda", det_threshold: float = 0.8):
        import torch
        from torchvision.models.detection import (
            KeypointRCNN_ResNet50_FPN_Weights, keypointrcnn_resnet50_fpn,
        )
        self.torch, self.device, self.det_threshold = torch, device, det_threshold
        w = KeypointRCNN_ResNet50_FPN_Weights.DEFAULT
        self.model = keypointrcnn_resnet50_fpn(weights=w).to(device).eval()

    def people(self, rgb: np.ndarray) -> list[Person]:
        t = self.torch.from_numpy(rgb).permute(2, 0, 1).float().div(255).to(self.device)
        with self.torch.no_grad():
            out = self.model([t])[0]
        res = []
        for b, s, k, ks in zip(out["boxes"], out["scores"], out["keypoints"],
                               out["keypoints_scores"]):
            if float(s) < self.det_threshold:
                continue
            kp = np.concatenate([k[:, :2].cpu().numpy(), ks.cpu().numpy()[:, None]], 1)
            res.append(Person(tuple(float(v) for v in b.tolist()), kp.astype(np.float32), float(s)))
        return res

    def main_person(self, rgb: np.ndarray) -> Person | None:
        ps = self.people(rgb)
        if not ps:
            return None
        return max(ps, key=lambda p: (p.box[2] - p.box[0]) * (p.box[3] - p.box[1]))


# ── 물건별 기준점 ────────────────────────────────────────────────────────
def bag_in_hand(
    person: Person,
    aspect: float,
    image_shape: tuple[int, int],
    *,
    size: float = 0.26,
    grip: float = 0.03,
    drop: float = 0.08,
    max_tilt: float = 15.0,
    max_above_hip: float = 0.05,
    side: str = "auto",
) -> tuple[tuple[int, int, int, int] | None, dict]:
    """가방을 손에 든 모습의 박스 (y1, y2, x1, x2) 와 진단.

    size   가방 높이 / 사람 키. 백팩 약 45cm / 키 175cm ≈ 0.26
    grip   박스 윗변 = 손목 y − 키 × grip. 손이 손잡이를 쥐는 높이
    drop   팔이 내려왔다고 볼 기준 — 손목이 팔꿈치보다 키 × drop 이상 아래
    max_tilt       팔뚝(팔꿈치→손목)이 수직에서 **몸 쪽으로** 기운 각도 상한 (°)
    max_above_hip  손목이 같은 쪽 엉덩이 관절보다 키 × 이 값 넘게 위면 탈락
           — 둘 다 **주머니에 넣은 손**을 거른다 (2026-09-26 F12: 몸 쪽 22°,
             엉덩이보다 키 × 0.073 위). 자연스럽게 내려온 손(F03)은 바깥쪽 6°,
             엉덩이 높이였다
    side   left | right | auto. auto 는 통과한 팔 중 몸 중심에서 더 먼 손
           (몸 앞을 가리는 면적이 작다)
    가로    손목 x 가 가운데. 가방은 손 아래로 매달린다
    """
    H_img, W_img = image_shape
    h = person.height
    hips = [person.point(n) for n in ("left_hip", "right_hip")]
    sh = [person.point(n) for n in ("left_shoulder", "right_shoulder")]
    pts = [p for p in hips + sh if p is not None]
    cx = float(np.mean([p[0] for p in pts])) if pts else (person.box[0] + person.box[2]) / 2

    cands, rejected = [], {}
    for s in ("left", "right"):
        if side != "auto" and s != side:
            continue
        w, e = person.point(f"{s}_wrist"), person.point(f"{s}_elbow")
        if w is None or e is None:
            rejected[s] = "손목·팔꿈치 미검출"
            continue
        if w[1] - e[1] < drop * h:
            rejected[s] = "팔이 안 내려옴"
            continue
        # 몸 쪽으로 기운 각도 — 손목이 팔꿈치보다 몸 중심에 가까워지는 방향이 +
        inward = (e[0] - w[0]) if e[0] > cx else (w[0] - e[0])
        tilt = float(np.degrees(np.arctan2(inward, w[1] - e[1])))
        hip = person.point(f"{s}_hip")
        above = float((hip[1] - w[1]) / h) if hip is not None else 0.0
        if tilt > max_tilt or above > max_above_hip:
            rejected[s] = f"주머니 손으로 보임 (몸 쪽 {tilt:.0f}°, 엉덩이보다 키 × {above:.3f} 위)"
            continue
        cands.append((abs(w[0] - cx), s, w, e, tilt, above))
    if not cands:
        return None, {"error": "가방을 들 수 있는 손이 없음", "rejected": rejected}
    _, s, w, e, tilt, above = max(cands, key=lambda c: c[0])

    bh = size * h
    bw = bh * aspect
    y1 = w[1] - grip * h
    x1 = w[0] - bw / 2
    box = (int(round(y1)), int(round(y1 + bh)), int(round(x1)), int(round(x1 + bw)))
    clipped = (max(0, box[0]), min(H_img, box[1]), max(0, box[2]), min(W_img, box[3]))
    info = {"side": s, "wrist": w.tolist(), "elbow": e.tolist(), "body_cx": cx,
            "tilt_in": tilt, "above_hip": above, "rejected": rejected,
            "person_h": h, "bag_h": bh, "bag_w": bw,
            "clipped": clipped != box}
    return clipped, info


def rotate_bound(img: np.ndarray, angle: float, border) -> np.ndarray:
    """잘림 없이 회전 (캔버스를 넓힌다). angle 은 도, 반시계 +."""
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    c, s = abs(M[0, 0]), abs(M[0, 1])
    nw, nh = int(h * s + w * c), int(h * c + w * s)
    M[0, 2] += nw / 2 - w / 2
    M[1, 2] += nh / 2 - h / 2
    flags = cv2.INTER_NEAREST if img.ndim == 2 else cv2.INTER_LINEAR
    return cv2.warpAffine(img, M, (nw, nh), flags=flags, borderValue=border)


def watch_head(ref_rgb: np.ndarray, ref_mask: np.ndarray, *, keep: float = 0.6):
    """시계 머리(문자판 + 러그 + 줄 조금)만 잘라 **줄 방향을 가로로** 눕힌다.

    손목을 감은 줄은 뒤로 돌아가 안 보인다. 제품 사진처럼 줄을 다 펼친 채로
    넣으면 팔 위에 시계를 납작하게 얹은 모양이 된다.

    줄 방향 = 마스크의 주축 (PCA). 문자판 = 주축을 따라 잰 폭이 가장 넓은 곳,
    그 폭이 문자판 지름 D. 주축 방향으로 ±keep·D 만 남긴다.
    keep 0.75(1.5·D) 로 시작했으나 F04 손목 폭(키 × 0.024, 53px)보다 박스가 넓어
    (77px) 0.6(1.2·D) 으로 줄였다.
    반환 (RGB, 0/1 마스크, D px, 주축 각도)
    """
    ys, xs = np.nonzero(ref_mask)
    pts = np.stack([xs, ys], 1).astype(np.float64)
    ev, evec = np.linalg.eigh(np.cov((pts - pts.mean(0)).T))
    major = evec[:, int(np.argmax(ev))]
    ang = float(np.degrees(np.arctan2(major[1], major[0])))

    rgb = rotate_bound(ref_rgb, ang, (255, 255, 255))      # 주축 → 가로
    m = rotate_bound(ref_mask.astype(np.uint8), ang, 0)
    prof = m.sum(0).astype(np.float32)
    k = max(3, int(0.03 * len(prof)) | 1)
    prof = cv2.GaussianBlur(prof[None, :], (k, 1), 0)[0]
    xf = int(np.argmax(prof))
    D = float(prof[xf])
    x1, x2 = max(0, int(xf - keep * D)), min(m.shape[1], int(xf + keep * D))
    rows = np.nonzero(m[:, x1:x2].any(1))[0]
    y1, y2 = int(rows.min()), int(rows.max()) + 1
    return rgb[y1:y2, x1:x2].copy(), m[y1:y2, x1:x2].copy(), D, ang


def watch_on_wrist(
    person: Person,
    head_shape: tuple[int, int],
    image_shape: tuple[int, int],
    *,
    face: float = 0.023,
    offset: float = -0.025,
    side: str = "auto",
) -> tuple[tuple[int, int, int, int] | None, float, dict]:
    """손목 위 시계 박스 (y1, y2, x1, x2), 참조를 돌릴 각도(도), 진단.

    face    문자판 지름 / 사람 키. 4cm / 175cm ≈ 0.023
    offset  손목 점에서 팔꿈치 쪽(+)으로 옮기는 거리 / 키. 음수면 손 쪽.
            🐛 처음 +0.012(손목뼈 바로 위)로 뒀더니 시계가 **정장 소매 위**에 올라갔다.
            Keypoint R-CNN 손목 점이 실제 손목이 아니라 소매 끝(커프스)에 찍혀서다 —
            F03·F04 에서 실제 손목보다 키 × 0.02~0.03 위. −0.025 로 소매 끝 바로 아래
            드러난 손목에 둔다
    방향    줄이 손목을 감으므로 **줄 축 ⟂ 팔뚝**. watch_head 는 줄 축이 가로이므로
            팔뚝의 법선 각도만큼 돌린다
    side    auto 는 왼손목(관례) 먼저, 안 보이면 오른손목
    """
    H_img, W_img = image_shape
    h = person.height
    order = ["left", "right"] if side == "auto" else [side]
    for s in order:
        w, e = person.point(f"{s}_wrist"), person.point(f"{s}_elbow")
        if w is not None and e is not None and np.linalg.norm(w - e) > 1:
            break
    else:
        return None, 0.0, {"error": "손목·팔꿈치가 보이는 팔이 없음"}

    u = (w - e) / np.linalg.norm(w - e)              # 팔꿈치 → 손목
    n = np.array([-u[1], u[0]])                       # 팔뚝의 법선 = 줄 축
    ang = float(np.degrees(np.arctan2(-n[1], n[0])))  # 이미지 y 가 아래라 부호 반전 (반시계 +)
    c = w - u * offset * h

    hh, hw = head_shape                               # 머리: 가로 = 줄 축
    scale = face * h / hh                             # 세로(팔뚝 방향) = 문자판 지름
    L, T = hw * scale, hh * scale
    corners = np.array([[-L / 2, -T / 2], [L / 2, -T / 2], [L / 2, T / 2], [-L / 2, T / 2]])
    rot = np.array([[n[0], u[0]], [n[1], u[1]]])      # 가로축 → n, 세로축 → u
    pts = corners @ rot.T + c
    x1, y1 = pts.min(0)
    x2, y2 = pts.max(0)
    box = (int(round(y1)), int(round(y2)), int(round(x1)), int(round(x2)))
    clipped = (max(0, box[0]), min(H_img, box[1]), max(0, box[2]), min(W_img, box[3]))
    info = {"side": s, "wrist": w.tolist(), "elbow": e.tolist(), "center": c.tolist(),
            "forearm": u.tolist(), "angle": ang, "face_px": face * h,
            "person_h": h, "clipped": clipped != box}
    return clipped, ang, info


def zoom_box(box, image_shape: tuple[int, int], factor: float = 6.0):
    """작은 물건 둘레의 정사각 부분 이미지 (y1, y2, x1, x2). 물건 박스 긴 변 × factor.

    AnyDoor 면적 관문(1%)은 학습 때 너무 작은 물체를 거르던 것이다. 추론에서
    진짜 제약은 512 크롭의 해상도라서, 부분 이미지 안에서 합성하고 되붙이면
    관문을 지키면서 같은 결과를 얻는다. factor 6 → 박스 면적 ≈ 1/36 ≈ 2.8%.
    """
    H, W = image_shape
    y1, y2, x1, x2 = box
    side = int(max(y2 - y1, x2 - x1) * factor)
    side = min(side, H, W)
    cy, cx = (y1 + y2) / 2, (x1 + x2) / 2
    zy1 = int(np.clip(cy - side / 2, 0, H - side))
    zx1 = int(np.clip(cx - side / 2, 0, W - side))
    return zy1, zy1 + side, zx1, zx1 + side


def box_mask(shape: tuple[int, int], box) -> np.ndarray:
    y1, y2, x1, x2 = box
    m = np.zeros(shape, np.uint8)
    m[y1:y2, x1:x2] = 1
    return m


def draw(rgb: np.ndarray, person: Person | None, box=None) -> np.ndarray:
    out = rgb.copy()
    if person is not None:
        x1, y1, x2, y2 = [int(v) for v in person.box]
        cv2.rectangle(out, (x1, y1), (x2, y2), (80, 160, 255), 2)
        for a, b in SKELETON:
            pa, pb = person.point(a), person.point(b)
            if pa is not None and pb is not None:
                cv2.line(out, tuple(int(v) for v in pa), tuple(int(v) for v in pb), (0, 255, 0), 3)
        for i, (x, y, s) in enumerate(person.kp):
            c = (255, 0, 0) if s >= KP_MIN_SCORE else (120, 120, 120)
            cv2.circle(out, (int(x), int(y)), 6, c, -1)
    if box is not None:
        y1, y2, x1, x2 = box
        cv2.rectangle(out, (x1, y1), (x2, y2), (255, 230, 0), 4)
    return out
