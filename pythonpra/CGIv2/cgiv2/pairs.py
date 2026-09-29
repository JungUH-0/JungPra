"""process_pairs 통합본 — AnyDoor 규약을 지키면서 세 벌을 하나로 합친다.

원본에는 같은 함수가 **세 벌** 있고 미묘하게 다르다.

    datasets/base.py:103        학습용   assert 4개 + 증강
    run_inference.py:46         추론용   패딩 센티넬 버그
    run_gradio_demo.py:146      데모용   enable_shape_control 있음

여기서 하는 일은 셋을 합치는 것뿐이다. **숫자(224 / 512 / 1.3~3.0배)는 그대로
둔다** — 가중치가 55만 표본에서 학습한 규약이라, 바꾸면 에러 없이 품질만
떨어진다.

원본에서 고친 것은 둘이다.

  패딩 센티넬
      run_inference.py:255 가 pad_value=-1 을 준 뒤 uint8 로 캐스팅한다.
      -1 은 255 로 감기고, 이어지는 `> 0.5` 를 통과해 1.0(= 여기 생성해라)이
      된다. 학습 쪽은 이걸 알고 센티넬 2 를 쓴 뒤 나중에 -1 로 되돌린다.
      죽은 경로가 아니다. box2squre 가 max(0,x1)/min(W,x2) 로 경계를 클램프
      하므로, 객체가 프레임 가장자리에 있으면 패딩이 실제로 생긴다.

  타깃 크롭 랜덤성
      expand_bbox 가 ratio 범위에서 np.random 으로 뽑는다. 추론에서도
      [1.5, 3] 이라 매 실행마다 크롭이 달라진다. diffusion seed 를 고정해도
      크롭이 흔들리므로 "strength 0.8 이 나았나" 를 판정할 수 없다.
      학습에서는 증강이니 그대로 두고, 추론에서는 고정값을 쓴다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np


def _load_utils(anydoor_root: str | Path):
    """AnyDoor 의 data_utils 를 그대로 쓴다. 복사하면 원본과 어긋날 수 있다."""
    root = Path(anydoor_root).resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from datasets import data_utils  # noqa: PLC0415
    return data_utils


class PairBuilder:
    """참조/타깃 한 쌍을 모델 입력으로 만든다."""

    def __init__(self, anydoor_root: str | Path):
        self.u = _load_utils(anydoor_root)

    # ── 관문 ────────────────────────────────────────────────────────────
    def check_gates(self, ref_mask: np.ndarray, tar_mask: np.ndarray) -> list[str]:
        """process_pairs 가 assert 로 막는 네 조건을 미리 검사해 사유를 돌려준다.

        학습 경로의 BaseDataset.__getitem__ 은 예외를 통째로 삼키고 무한
        재시도한다. 소량 데이터에서 걸리면 에러 없이 멈추므로 미리 본다.
        """
        bad: list[str] = []
        score = self.u.mask_score(ref_mask)
        if score <= 0.90:
            bad.append(f"참조 조각남({score:.2f})")

        for name, m in (("참조", ref_mask), ("타깃", tar_mask)):
            r = m.sum() / (m.shape[0] * m.shape[1])
            if not (0.01 < r < 0.64):
                bad.append(f"{name} 면적({r:.2%})")

        ry1, ry2, rx1, rx2 = self.u.get_bbox_from_mask(ref_mask)
        H, W = ref_mask.shape
        if (ry2 - ry1) < 0.10 * H or (rx2 - rx1) < 0.10 * W:
            bad.append(f"참조 변 10% 미만({(rx2-rx1)/W:.0%}x{(ry2-ry1)/H:.0%})")
        return bad

    # ── 본체 ────────────────────────────────────────────────────────────
    def build(
        self,
        ref_image: np.ndarray,
        ref_mask: np.ndarray,
        tar_image: np.ndarray,
        tar_mask: np.ndarray,
        *,
        train: bool = False,
        shape_control: bool = False,
        tar_crop_ratio: float = 2.0,
        max_ratio: float = 0.8,
    ) -> dict:
        """RGB uint8 이미지와 0/1 마스크를 받아 모델 입력 dict 를 만든다.

        train=True  학습용. assert 4개 + flip/밝기 증강 + 참조 확대 1.1~1.4 랜덤
                    + 70% 확률로 타깃 마스크 교란.
        train=False 추론용. 검사·증강 없음, 참조 확대 1.2 고정, 크롭 고정.

        shape_control 은 배치 마스크를 bbox 사각형 대신 실제 실루엣으로 만든다.
        강체(시계·자동차)에서는 형태가 변하면 안 되므로 켤 만하고, 사람은
        자세가 배경에 맞게 변해야 하므로 끄는 쪽이 맞다. 검증 대상이다.
        """
        u = self.u

        if train:
            assert u.mask_score(ref_mask) > 0.90
            assert self._area_ok(ref_mask) and self._area_ok(tar_mask)

        # ========= 참조: 배경 제거 -> bbox 크롭 -> 확대 -> 정사각 -> 224 =========
        ref_box = u.get_bbox_from_mask(ref_mask)
        if train:
            ry1, ry2, rx1, rx2 = ref_box
            H, W = ref_mask.shape
            assert (ry2 - ry1) >= 0.10 * H and (rx2 - rx1) >= 0.10 * W

        m3 = np.stack([ref_mask] * 3, -1)
        masked_ref = ref_image * m3 + np.ones_like(ref_image) * 255 * (1 - m3)

        y1, y2, x1, x2 = ref_box
        masked_ref = masked_ref[y1:y2, x1:x2, :]
        rmask = ref_mask[y1:y2, x1:x2]

        ratio = (np.random.randint(11, 15) / 10) if train else 1.2
        masked_ref, rmask = u.expand_image_mask(masked_ref, rmask, ratio=ratio)

        masked_ref = u.pad_to_square(masked_ref, pad_value=255, random=False)
        masked_ref = cv2.resize(masked_ref.astype(np.uint8), (224, 224)).astype(np.uint8)

        rmask3 = u.pad_to_square(np.stack([rmask] * 3, -1) * 255, pad_value=0, random=False)
        rmask3 = cv2.resize(rmask3.astype(np.uint8), (224, 224)).astype(np.uint8)
        rmask = rmask3[:, :, 0]

        if train:
            ref_aug, rmask_c = self._aug(masked_ref, rmask)
        else:
            ref_aug, rmask_c = masked_ref, rmask

        # ControlNet 힌트가 되는 고주파 맵. 이 함수의 thresh/erode 상수는
        # 가중치가 "고주파 맵"이라는 성격만 학습했으므로 객체별 조정이 가능하다.
        ref_collage = u.sobel(ref_aug, rmask_c / 255)

        # ========= 타깃: bbox -> 크롭 확대 -> 정사각 -> 512 =========
        tar_box = u.get_bbox_from_mask(tar_mask)
        tar_box = u.expand_bbox(tar_mask, tar_box, ratio=[1.1, 1.2])
        if train:
            assert self._region_ok(tar_mask, tar_box, max_ratio)

        if train:
            crop_box = u.expand_bbox(tar_image, tar_box, ratio=[1.3, 3.0])
        else:
            crop_box = self._expand_fixed(tar_image, tar_box, tar_crop_ratio)
        crop_box = u.box2squre(tar_image, crop_box)

        cy1, cy2, cx1, cx2 = crop_box
        cropped_tar = tar_image[cy1:cy2, cx1:cx2, :]
        cropped_tar_mask = tar_mask[cy1:cy2, cx1:cx2]

        y1, y2, x1, x2 = u.box_in_box(tar_box, crop_box)

        # ========= 콜라주: 배경 크롭 위에 고주파 맵을 붙인다 =========
        patch = cv2.resize(ref_collage.astype(np.uint8), (x2 - x1, y2 - y1))
        pmask = cv2.resize(rmask_c.astype(np.uint8), (x2 - x1, y2 - y1))
        pmask = (pmask > 128).astype(np.uint8)

        collage = cropped_tar.copy()
        collage[y1:y2, x1:x2, :] = patch

        collage_mask = cropped_tar.copy() * 0.0
        collage_mask[y1:y2, x1:x2, :] = 1.0

        if train and np.random.uniform(0, 1) < 0.7:
            cropped_tar_mask = u.perturb_mask(cropped_tar_mask)
            collage_mask = np.stack([cropped_tar_mask] * 3, -1)
        elif shape_control:
            collage_mask = np.stack([cropped_tar_mask] * 3, -1)

        H1, W1 = collage.shape[0], collage.shape[1]

        cropped_tar = u.pad_to_square(cropped_tar, pad_value=0, random=False).astype(np.uint8)
        collage = u.pad_to_square(collage, pad_value=0, random=False).astype(np.uint8)
        # 센티넬 2. -1 을 바로 주면 uint8 에서 255 로 감긴다 (원본 추론 경로의 버그).
        collage_mask = u.pad_to_square(collage_mask, pad_value=2, random=False).astype(np.uint8)

        H2, W2 = collage.shape[0], collage.shape[1]

        cropped_tar = cv2.resize(cropped_tar, (512, 512)).astype(np.float32)
        collage = cv2.resize(collage, (512, 512)).astype(np.float32)
        collage_mask = cv2.resize(
            collage_mask, (512, 512), interpolation=cv2.INTER_NEAREST
        ).astype(np.float32)
        collage_mask[collage_mask == 2] = -1        # 패딩 = 무효

        ref_out = ref_aug / 255
        cropped_tar = cropped_tar / 127.5 - 1.0
        collage = collage / 127.5 - 1.0
        collage = np.concatenate([collage, collage_mask[:, :, :1]], -1)

        return dict(
            ref=ref_out.copy(),
            jpg=cropped_tar.copy(),
            hint=collage.copy(),
            extra_sizes=np.array([H1, W1, H2, W2]),
            tar_box_yyxx_crop=np.array(crop_box),
        )

    # ── 보조 ────────────────────────────────────────────────────────────
    @staticmethod
    def _area_ok(mask: np.ndarray) -> bool:
        r = mask.sum() / (mask.shape[0] * mask.shape[1])
        return 0.01 < r < 0.64

    @staticmethod
    def _region_ok(mask, yyxx, ratio) -> bool:
        H, W = mask.shape[0] * ratio, mask.shape[1] * ratio
        y1, y2, x1, x2 = yyxx
        return (y2 - y1) <= H and (x2 - x1) <= W

    @staticmethod
    def _expand_fixed(image, yyxx, ratio: float):
        """expand_bbox 의 결정론 버전. 추론 재현성을 위해 랜덤을 뺀다."""
        y1, y2, x1, x2 = yyxx
        H, W = image.shape[0], image.shape[1]
        xc, yc = 0.5 * (x1 + x2), 0.5 * (y1 + y2)
        h, w = ratio * (y2 - y1 + 1), ratio * (x2 - x1 + 1)
        return (
            max(0, int(yc - h * 0.5)), min(H, int(yc + h * 0.5)),
            max(0, int(xc - w * 0.5)), min(W, int(xc + w * 0.5)),
        )

    @staticmethod
    def _aug(image, mask):
        import albumentations as A  # noqa: PLC0415
        t = A.Compose([A.HorizontalFlip(p=0.5), A.RandomBrightnessContrast(p=0.5)])
        out = t(image=image.astype(np.uint8), mask=mask)
        return out["image"], out["mask"]


def crop_back(
    pred: np.ndarray,
    tar_image: np.ndarray,
    extra_sizes: np.ndarray,
    tar_box_yyxx_crop: np.ndarray,
    *,
    feather: int = 0,
) -> np.ndarray:
    """512 결과를 원본 좌표계로 되돌린다.

    원본(run_inference.py:126) 대비 둘을 고쳤다.

      1픽셀 밀림   호출부가 pred[1:,:,:] 로 맨 윗줄을 버린 뒤 resize 해서
                   결과가 세로로 1px 밀린다. 여기서는 자르지 않는다.
      경계 처리    원본은 5px 마진 하드 대입이라 이음매가 남는다. feather 를
                   주면 그 폭만큼 알파를 선형으로 떨어뜨려 섞는다.

    feather=0 이면 원본과 같은 하드 대입이다. 베이스라인 측정 때는 0 으로 둔다.
    """
    H1, W1, H2, W2 = [int(v) for v in extra_sizes]
    y1, y2, x1, x2 = [int(v) for v in tar_box_yyxx_crop]

    pred = cv2.resize(pred.astype(np.float32), (W2, H2))

    # pad_to_square 가 더한 여백을 되돌린다.
    if W1 != H1:
        if W1 < W2:
            p1 = int((W2 - W1) / 2)
            pred = pred[:, p1:p1 + W1, :]
        else:
            p1 = int((H2 - H1) / 2)
            pred = pred[p1:p1 + H1, :, :]

    out = tar_image.astype(np.float32).copy()
    h, w = y2 - y1, x2 - x1
    pred = cv2.resize(pred, (w, h))

    if feather <= 0:
        out[y1:y2, x1:x2, :] = pred
        return np.clip(out, 0, 255).astype(np.uint8)

    alpha = np.ones((h, w), np.float32)
    f = min(feather, h // 2, w // 2)
    if f > 0:
        ramp = np.linspace(0.0, 1.0, f, dtype=np.float32)
        alpha[:f, :] *= ramp[:, None]
        alpha[-f:, :] *= ramp[::-1][:, None]
        alpha[:, :f] *= ramp[None, :]
        alpha[:, -f:] *= ramp[::-1][None, :]
    a = alpha[:, :, None]
    out[y1:y2, x1:x2, :] = pred * a + out[y1:y2, x1:x2, :] * (1 - a)
    return np.clip(out, 0, 255).astype(np.uint8)
