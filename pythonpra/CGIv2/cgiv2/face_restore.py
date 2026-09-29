"""얼굴 정체성 복원 — 원본 얼굴을 생성 결과에 정렬해 이식한다.

배경 (2026-09-22 측정)
    AnyDoor 는 참조를 224 로 줄이며 얼굴 정보 대부분을 잃는다(전신 17~25px).
    상반신 크롭으로 얼굴을 1.6~2.1배 키워봤지만 정체성 점수는 0.085 -> 0.131
    로 미미하게만 올랐다(판정선 0.363에 크게 못 미침). 정보량 병목이 유일한
    원인이 아니라, 모델이 얼굴 정체성을 전달하는 경로 자체가 약하다는 뜻이다
    (object-level 모델이라 당연한 결과 — readme.md 가 face swap 을 별도
    모델로 예고했다).

    그래서 확산이 만든 얼굴을 신뢰하지 않는다. AnyDoor 가 잘하는 것(자세·
    조명·배경 통합)은 그대로 두고, **얼굴만 원본을 직접 이식**한다.

절차
    1. YuNet 랜드마크(눈 2 · 코 1 · 입꼬리 2)로 참조와 생성물 양쪽에서 얼굴을 찾는다.
    2. 5점 대응으로 닮음변환(회전+균등스케일+평행이동)을 구한다
       (cv2.estimateAffinePartial2D — ArcFace 류가 정렬에 쓰는 것과 같은 부류다).
    3. 참조 얼굴을 그 변환으로 생성물 좌표계에 맞춰 워프한다.
    4. 타원 페더 마스크로 섞는다. 워프된 얼굴을 생성물의 얼굴 색 통계에
       맞춰 LAB 매칭한 뒤 섞는다 — 안 하면 이식 자국이 도드라진다.

이 모듈은 순수 후처리다. 가중치를 하나도 건드리지 않는다 (🟢 등급).
검출기는 evaluate.FaceScorer 가 이미 로드한 것을 재사용한다 — 같은 ONNX
모델을 두 번 띄우지 않는다.
"""
from __future__ import annotations

import cv2
import numpy as np


def _landmarks5(face_row) -> np.ndarray:
    """YuNet 검출 행에서 5점 랜드마크를 뽑는다 (우안·좌안·코·우구·좌구)."""
    return np.array(face_row[4:14], dtype=np.float32).reshape(5, 2)


def _lab_stats(rgb: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    sel = mask.astype(bool)
    if sel.sum() < 20:
        return np.zeros(3, np.float32), np.ones(3, np.float32)
    px = lab[sel]
    return px.mean(0), px.std(0) + 1e-6


def _match_face_color(warped_rgb: np.ndarray, mask: np.ndarray,
                      target_mean: np.ndarray, target_std: np.ndarray,
                      strength: float) -> np.ndarray:
    """워프된 얼굴의 LAB 통계를 생성물 얼굴 쪽 통계에 맞춘다.

    target_mean/std 는 AnyDoor 가 그 장면에 대해 이미 추정한 조명이다.
    그걸 재사용하는 것이 새로 조명을 추정하는 것보다 이치에 맞는다.
    """
    if strength <= 0:
        return warped_rgb
    lab = cv2.cvtColor(warped_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    sel = mask.astype(bool)
    src_mean, src_std = _lab_stats(warped_rgb, mask)
    px = lab[sel]
    moved = (px - src_mean) / src_std * target_std + target_mean
    lab[sel] = px * (1 - strength) + moved * strength
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)


class FaceTransplanter:
    def __init__(self, scorer):
        """scorer 는 evaluate.FaceScorer 인스턴스 — 검출기를 공유한다."""
        self.scorer = scorer

    def transplant(
        self,
        ref_rgb: np.ndarray,
        ref_mask: np.ndarray,
        gen_rgb: np.ndarray,
        *,
        head_room: float = 0.6,
        torso_ratio: float = 1.3,
        width_ratio: float = 1.7,
        feather: float = 0.10,
        color_match: float = 0.5,
        blend: str = "feather",
    ) -> tuple[np.ndarray, bool]:
        """gen_rgb 에 ref_rgb 의 얼굴을 정렬해 이식한다.

        **ref_mask 가 필수다.** 처음 버전은 얼굴 bbox 주변에 그냥 타원을
        그렸는데, 그러면 참조 사진의 흰 스튜디오 배경까지 함께 워프되어
        머리 둘레에 흰 안개처럼 번졌다(2026-09-22 육안 확인, SFace 점수는
        0.94로 좋아 보였지만 실제로는 실패였다). 참조의 실루엣 마스크와
        얼굴 주변 ROI 를 교집합해 **실제 머리 모양**만 오려내면 이 문제가
        사라진다.

        head_room/torso_ratio/width_ratio  참조 쪽에서 오려낼 ROI (prep.crop_to_face
                                           와 같은 휴리스미틱, 목 아래로 조금만)
        feather      페더 커널 폭 = 생성물 쪽 얼굴 높이 x 이 비율
        color_match  워프된 얼굴을 생성물 얼굴 색에 맞추는 강도
        blend        "feather" 또는 "poisson"

        반환: (결과, 성공 여부).
        """
        ref_bgr, ref_face = self.scorer.detect(ref_rgb)
        gen_bgr, gen_face = self.scorer.detect(gen_rgb)
        if ref_face is None or gen_face is None:
            return gen_rgb, False

        src_pts = _landmarks5(ref_face)
        dst_pts = _landmarks5(gen_face)
        M, _ = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.LMEDS)
        if M is None:
            return gen_rgb, False

        # 참조 쪽 머리 ROI = 얼굴 주변 사각 영역 ∩ 인물 실루엣.
        # 실루엣과 교집합하므로 스튜디오 배경은 애초에 마스크에 안 들어간다.
        fx, fy, fw, fh = [float(v) for v in ref_face[:4]]
        rH, rW = ref_mask.shape[:2]
        top = max(0, int(fy - fh * head_room))
        bottom = min(rH, int(fy + fh + fh * torso_ratio))
        cx = fx + fw / 2
        half_w = fh * width_ratio / 2
        left = max(0, int(cx - half_w))
        right = min(rW, int(cx + half_w))
        roi = np.zeros(ref_mask.shape[:2], np.uint8)
        roi[top:bottom, left:right] = 1
        src_mask = (ref_mask.astype(bool) & roi.astype(bool)).astype(np.float32)

        H, W = gen_rgb.shape[:2]
        warped = cv2.warpAffine(ref_rgb, M, (W, H), flags=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        warped_mask = cv2.warpAffine(src_mask, M, (W, H), flags=cv2.INTER_LINEAR,
                                     borderMode=cv2.BORDER_CONSTANT, borderValue=0)

        gfh = float(gen_face[3])
        k = max(3, int(gfh * feather) | 1)
        mask = np.clip(cv2.GaussianBlur(warped_mask, (k, k), 0), 0, 1)
        hard_mask = (mask > 0.5).astype(np.uint8)
        if hard_mask.sum() < 20:
            return gen_rgb, False

        target_mean, target_std = _lab_stats(gen_rgb, hard_mask)
        warped = _match_face_color(warped, hard_mask, target_mean, target_std, color_match)

        out = None
        if blend == "poisson":
            ys, xs = np.nonzero(hard_mask)
            if len(ys):
                center = (int((xs.min() + xs.max()) / 2), int((ys.min() + ys.max()) / 2))
                try:
                    out = cv2.seamlessClone(warped, gen_rgb, hard_mask * 255,
                                            center, cv2.NORMAL_CLONE)
                except cv2.error:
                    out = None          # 경계에 닿으면 실패 -> feather 로 폴백
        if out is None:
            a = mask[:, :, None]
            out = np.clip(warped.astype(np.float32) * a + gen_rgb.astype(np.float32) * (1 - a),
                         0, 255).astype(np.uint8)

        return out, True

    def face_size_ratio(self, ref_rgb: np.ndarray, gen_rgb: np.ndarray) -> float | None:
        """생성물/참조 얼굴 높이 비율. 극단적 크기 차이를 사전에 확인하는 용도."""
        rp = self.scorer.face_px(ref_rgb)
        gp = self.scorer.face_px(gen_rgb)
        if rp is None or gp is None:
            return None
        return gp / rp
