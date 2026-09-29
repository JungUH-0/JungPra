"""마스크 생성 — AnyDoor 가 비워둔 자리.

AnyDoor 는 마스크를 만들지 않는다. readme.md:111 이 "사용자가 대상 객체의
마스크를 직접 표시해야 한다" 고 명시하고, 코드 주석은 SAM 웹데모 링크를
안내한다. iseg/ 가 있지만 거친 마스크를 **정제**할 뿐 빈손에서 만들지 못한다
(forward(image, coarse_mask) 가 마스크를 인자로 받는다).

중요 — 알파에 공을 들일 이유가 없다.
    process_pairs 는 어디서도 연속 알파를 쓰지 않는다.

        ref_mask = (mask > 128).astype(np.uint8)
        ref_mask_compose = (cv2.resize(...) > 128).astype(np.uint8)

    매팅으로 뽑은 0~1 알파는 전부 이진화에서 버려진다. 경계의 부드러움은
    확산 과정이 다시 만들어내는 것이지 매팅에서 오지 않는다. 마스크 품질은
    **연결성과 면적 비율**로만 평가하면 된다.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


class BiRefNetMasker:
    """BiRefNet 으로 전경 마스크를 뽑는다.

    _HR-matting 변종을 기본으로 쓴다. 2048 로 학습된 모델이라 가는 구조
    (가방 어깨끈, 시계 줄)가 살아남을 확률이 높다. 그게 여기서 중요한 이유는
    끈이 끊기면 mask_score 가 0.90 아래로 떨어져 관문에서 탈락하기 때문이다.
    """

    def __init__(
        self,
        model_name: str = "ZhengPeng7/BiRefNet_HR-matting",
        size: int | None = None,
        device: str = "cuda",
        half: bool = True,
    ):
        import torch
        from torchvision import transforms
        from transformers import AutoModelForImageSegmentation

        self.device = device
        self.half = half and device.startswith("cuda")
        # 모델명이 해상도를 결정한다. _HR 계열은 2048 로 학습됐다.
        self.size = size or (2048 if "_HR" in model_name else 1024)

        self.model = AutoModelForImageSegmentation.from_pretrained(
            model_name, trust_remote_code=True
        ).to(device).eval()
        if self.half:
            self.model = self.model.half()

        self.tf = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        self._torch = torch

    def alpha(self, rgb: np.ndarray) -> np.ndarray:
        """0~1 연속 알파. 진단용이다 — 파이프라인은 binary() 를 쓴다."""
        x = self.tf(cv2.resize(rgb, (self.size, self.size))).unsqueeze(0).to(self.device)
        if self.half:
            x = x.half()
        with self._torch.no_grad():
            pred = self.model(x)[-1].sigmoid().float().cpu()[0, 0].numpy()
        return cv2.resize(pred, (rgb.shape[1], rgb.shape[0]))

    def binary(self, rgb: np.ndarray, thresh: float = 0.5,
               keep_largest: bool = False) -> np.ndarray:
        """0/1 uint8 마스크. 파이프라인이 실제로 쓰는 것.

        keep_largest 는 가장 큰 덩어리만 남긴다. mask_score 를 억지로 1.0 으로
        만들 수 있지만, **가방 어깨끈처럼 얇게 이어진 부분이 잘려나간다.**
        기본은 끈다 — 관문을 통과시키려고 객체를 훼손하면 본말전도다.
        """
        m = (self.alpha(rgb) > thresh).astype(np.uint8)
        if keep_largest and m.sum() > 0:
            n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
            if n > 1:
                k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
                m = (lab == k).astype(np.uint8)
        return m


class DeepLabV3Masker:
    """torchvision DeepLabV3 — 사람 전용 (COCO 21클래스 중 index 15).

    BiRefNet 과 달리 **클래스를 안다.** 사람 외의 살리언트 객체(가구, 소품)를
    같이 잡지 않는다. 대신 경계가 BiRefNet 보다 거칠고 머리카락 같은 가는
    구조가 뭉개진다.

    사람 합성에서는 이게 장점일 수도 있다 — 스튜디오 컷에 의자나 소품이 같이
    잡히면 process_pairs 의 연결성 관문에서 떨어지기 때문이다.
    """

    PERSON = 15

    def __init__(self, device: str = "cuda", size: int = 720):
        import torch
        from torchvision.models.segmentation import (
            DeepLabV3_ResNet101_Weights, deeplabv3_resnet101,
        )

        self.device, self.size = device, size
        w = DeepLabV3_ResNet101_Weights.DEFAULT
        self.model = deeplabv3_resnet101(weights=w).to(device).eval()
        self.tf = w.transforms()
        self._torch = torch

    def binary(self, rgb: np.ndarray, cls: int | None = None) -> np.ndarray:
        torch = self._torch
        H, W = rgb.shape[:2]
        small = cv2.resize(rgb, (self.size, int(H * self.size / W)))
        x = self.tf(torch.from_numpy(small).permute(2, 0, 1)).unsqueeze(0).to(self.device)
        with torch.no_grad():
            out = self.model(x)["out"][0]
        lab = out.argmax(0).byte().cpu().numpy()
        m = (lab == (self.PERSON if cls is None else cls)).astype(np.uint8)
        return (cv2.resize(m, (W, H), interpolation=cv2.INTER_NEAREST) > 0).astype(np.uint8)


class SAM2Masker:
    """SAM 2 — 점 프롬프트로 고른 객체만 분할한다.

    BiRefNet 은 "가장 눈에 띄는 것" 을 잡고, DeepLabV3 는 "사람" 을 잡는다.
    SAM 2 는 **우리가 가리킨 것** 을 잡는다. 여러 물체가 있는 사진에서
    원하는 것만 고를 수 있는 유일한 도구다.

    점을 안 주면 프레임 중앙 세로축에 세 점을 찍는다. 스튜디오 인물 컷처럼
    피사체가 가운데 서 있는 경우를 가정한 것이다.
    """

    def __init__(self, model_id: str = "facebook/sam2.1-hiera-large",
                 device: str = "cuda"):
        from sam2.sam2_image_predictor import SAM2ImagePredictor
        self.p = SAM2ImagePredictor.from_pretrained(model_id, device=device)

    def binary(self, rgb: np.ndarray, points=None) -> np.ndarray:
        H, W = rgb.shape[:2]
        if points is None:
            cx = W * 0.5
            points = [(cx, H * 0.35), (cx, H * 0.55), (cx, H * 0.75)]
        pts = np.array(points, np.float32)
        lbl = np.ones(len(pts), np.int32)

        self.p.set_image(rgb)
        masks, scores, _ = self.p.predict(
            point_coords=pts, point_labels=lbl, multimask_output=True)
        return (masks[int(np.argmax(scores))] > 0).astype(np.uint8)


def get_masker(tool: str, **kw):
    """도구 이름으로 마스커를 만든다. 전부 같은 계약을 지킨다.

        binary(RGB uint8 (H,W,3)) -> 0/1 uint8 (H,W)

    이 계약만 맞으면 어느 도구든 파이프라인에 꽂힌다. 등록부의 🟢 등급이란
    뜻이 이것이다 — 가중치와 아무 관계가 없다.
    """
    t = tool.lower()
    if t in {"birefnet", "birefnet_hr", "hr"}:
        return BiRefNetMasker(model_name="ZhengPeng7/BiRefNet_HR-matting", **kw)
    if t in {"birefnet_1024", "birefnet_std", "std"}:
        return BiRefNetMasker(model_name="ZhengPeng7/BiRefNet", **kw)
    if t in {"deeplabv3", "deeplab"}:
        return DeepLabV3Masker(**kw)
    if t in {"sam2", "sam"}:
        return SAM2Masker(**kw)
    raise ValueError(f"모르는 도구: {tool}")


def bridge_thin_parts(mask: np.ndarray, radius: int = 3) -> np.ndarray:
    """끊긴 가는 부분을 이어붙인다 (닫힘 연산).

    가방 어깨끈·시계 줄이 몇 픽셀 끊겨 mask_score 가 0.90 아래로 떨어질 때
    쓴다. 반지름을 키우면 붙지만 형태가 뭉툭해지므로, check_gates 가 통과할
    최소값을 찾는 식으로 쓰는 것이 맞다.
    """
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1,) * 2)
    return cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, k)


def load_mask(path: str | Path) -> np.ndarray:
    """PNG 마스크를 0/1 로 읽는다."""
    m = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if m is None:
        raise FileNotFoundError(path)
    return (m > 128).astype(np.uint8)


def mask_from_rgba(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """알파 채널이 있는 PNG 에서 (RGB, 0/1 마스크) 를 뽑는다.

    SAM 웹데모가 내보내는 형식이다. AnyDoor README 가 안내하는 경로이기도 하다.
    """
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(path)
    if img.shape[2] != 4:
        raise ValueError(f"알파 채널이 없습니다: {path}")
    mask = (img[:, :, 3] > 128).astype(np.uint8)
    rgb = cv2.cvtColor(img[:, :, :3].copy(), cv2.COLOR_BGR2RGB)
    return rgb, mask
