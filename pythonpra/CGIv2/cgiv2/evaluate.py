"""평가 — AnyDoor 에 아예 없는 것.

원본 저장소에는 평가 코드가 없다. 논문 수치를 낼 때는 별도로 돌렸을 것이다.
그런데 평가가 없으면 "개선했다"를 말할 수 없다. 샘플러를 건드리든 파인튜닝을
하든, 좋아졌는지 나빠졌는지 판정할 수단이 먼저 있어야 한다.

지표 둘은 이미 CGI 기술선정 문서에 설계돼 있었다. 여기서는 구현만 한다.

    정체성   DINOv2 임베딩 코사인 (참조 크롭 vs 생성 크롭)
    텍스트   OCR 편집거리 (로고·라벨 보존)

그리고 하나를 더한다.

    이음매   경계 안쪽/바깥쪽 LAB 평균 거리 (postproc.seam_score)

DINOv2 는 공짜다 — AnyDoor 가 조건 인코더로 이미 로드하고 있다. 따로 띄울
필요가 없다.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def _crop_to_mask(image: np.ndarray, mask: np.ndarray, pad: float = 0.1) -> np.ndarray:
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return image
    y1, y2, x1, x2 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    py, px = int((y2 - y1) * pad), int((x2 - x1) * pad)
    H, W = mask.shape
    return image[max(0, y1 - py):min(H, y2 + py), max(0, x1 - px):min(W, x2 + px)]


def cutout(image: np.ndarray, mask: np.ndarray, pad_value: int = 255) -> np.ndarray:
    """배경을 흰색으로 지우고 bbox 로 자른 뒤 정사각 패딩한다.

    **이게 정체성 비교의 전제다.** 그냥 잘라서 넣으면 DINOv2 의 CLS 토큰이
    정체성이 아니라 **장면**을 잰다. 참조는 "크림색 스튜디오의 인물", 생성물은
    "콜로세움 앞 인물" 이라 같은 사람이어도 코사인이 0 근처로 나온다.

    process_pairs 가 참조를 다루는 방식과 똑같이 맞춘다 — 마스크로 배경 제거,
    bbox 크롭, 흰 배경 정사각 패딩. 조건 인코더가 실제로 보는 표현과 같은
    표현에서 재는 것이 맞다.
    """
    m = mask.astype(np.uint8)
    if m.sum() == 0:
        return image
    m3 = np.stack([m] * 3, -1)
    cut = image * m3 + np.ones_like(image) * pad_value * (1 - m3)

    ys, xs = np.nonzero(m)
    y1, y2, x1, x2 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    cut = cut[y1:y2, x1:x2]

    h, w = cut.shape[:2]
    if h != w:
        s = abs(h - w)
        a, b = s // 2, s - s // 2
        pad = ((0, 0), (a, b), (0, 0)) if h > w else ((a, b), (0, 0), (0, 0))
        cut = np.pad(cut, pad, "constant", constant_values=pad_value)
    return cut.astype(np.uint8)


class IdentityScorer:
    """DINOv2 임베딩 코사인.

    같은 사람 두 장이 다른 사람 두 장보다 높게 나오면 지표가 작동하는 것이다.
    쓰기 전에 그 확인을 한 번 하는 편이 좋다.
    """

    def __init__(self, engine=None, dinov2_root: str | Path | None = None,
                 weight: str | Path | None = None, device: str = "cuda"):
        """engine 을 주면 AnyDoor 가 이미 로드한 DINOv2 를 재사용한다.

        안 주면 독립 로드한다. 독립 로드는 AnyDoor 없이 평가만 먼저 만들 때
        쓴다 — 파이프라인이 완성되기 전에 팀이 병렬로 작업할 수 있다.
        """
        import torch
        self._torch = torch
        self.device = device

        if engine is not None:
            self.model = engine.model.cond_stage_model.model
            self.mean = engine.model.cond_stage_model.image_mean.to(device)
            self.std = engine.model.cond_stage_model.image_std.to(device)
            self.owns = False
            return

        import sys
        root = Path(dinov2_root).resolve()
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        import hubconf  # noqa: PLC0415

        m = hubconf.dinov2_vitg14(pretrained=False)
        m.load_state_dict(torch.load(str(weight), map_location="cpu"), strict=False)
        self.model = m.to(device).eval()
        self.mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1).to(device)
        self.std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1).to(device)
        self.owns = True

    def embed(self, rgb: np.ndarray) -> "np.ndarray":
        torch = self._torch
        x = cv2.resize(rgb.astype(np.uint8), (224, 224)).astype(np.float32) / 255.0
        t = torch.from_numpy(x).permute(2, 0, 1).unsqueeze(0).to(self.device)
        t = (t - self.mean) / self.std
        t = t.to(next(self.model.parameters()).dtype)
        with torch.no_grad():
            f = self.model.forward_features(t)["x_norm_clstoken"]
        v = f[0].float().cpu().numpy()
        return v / (np.linalg.norm(v) + 1e-8)

    def score(self, ref_rgb, ref_mask, gen_rgb, gen_mask, *, segment=None) -> float:
        """참조 물체와 생성 물체의 코사인 유사도. 1 에 가까울수록 정체성 보존.

        양쪽 다 cutout 으로 배경을 지워 장면 차이를 없앤다. 이걸 안 하면
        정체성이 아니라 배경을 재게 된다.

        segment 는 생성물에서 실제 물체 실루엣을 뽑는 함수다
        (f(rgb) -> 0/1 마스크). 주지 않으면 gen_mask(= 배치 사각형)를 쓰는데,
        그 안에 배경이 섞여 점수가 깎인다. scripts/rescore.py 가 BiRefNet 을
        넘겨 이 문제를 없앤다.

        **값 자체보다 calibrate() 로 잡은 기준선과의 거리로 읽어야 한다.**
        """
        a = self.embed(cutout(ref_rgb, ref_mask))
        if segment is not None:
            crop = _crop_to_mask(gen_rgb, gen_mask, pad=0.05)
            gm = segment(crop)
            b = self.embed(cutout(crop, gm))
        else:
            b = self.embed(cutout(gen_rgb, gen_mask))
        return float(np.dot(a, b))

    def calibrate(self, items: list[tuple[np.ndarray, np.ndarray]],
                  max_pairs: int = 60) -> dict:
        """지표의 상한/바닥을 잡는다. 숫자를 해석하려면 이게 먼저다.

        items 는 (rgb, mask) 목록이다. 같은 이미지에 서로 다른 증강을 준 쌍이
        상한, 다른 객체끼리가 바닥이다. 0.259 가 "낮다"인지 "이 지표에서는
        보통"인지는 이 두 값 사이 어디에 있느냐로만 말할 수 있다.
        """
        import itertools
        import random

        embs = [self.embed(cutout(img, m)) for img, m in items]

        same = []
        for img, m in items[:max_pairs]:
            flipped = self.embed(cutout(img[:, ::-1].copy(), m[:, ::-1].copy()))
            same.append(float(np.dot(self.embed(cutout(img, m)), flipped)))

        idx = list(itertools.combinations(range(len(embs)), 2))
        random.Random(0).shuffle(idx)
        diff = [float(np.dot(embs[i], embs[j])) for i, j in idx[:max_pairs]]

        return {
            "same_object": {"mean": float(np.mean(same)), "n": len(same)},
            "different_object": {"mean": float(np.mean(diff)),
                                 "std": float(np.std(diff)), "n": len(diff)},
        }


class FaceScorer:
    """SFace 얼굴 정체성 — DINOv2 와 달리 **얼굴만** 잰다.

    이게 왜 따로 필요한가.
        DINOv2 코사인은 인물 컷아웃 전체를 잰다. 옷 색·체형·자세·실루엣이
        면적의 대부분이고 얼굴은 몇 %다. 그래서 얼굴이 뭉개져도 0.88 이 나온다.
        "내 사진을 넣는다" 가 목적이면 그 지표는 목적을 안 재고 있는 것이다.

    구성
        YuNet   얼굴 검출 + 랜드마크 5점 (눈 2, 코 1, 입꼬리 2)
        SFace   랜드마크로 정렬한 112x112 얼굴 -> 128차원 임베딩

    OpenCV 에 내장된 API 라 추가 패키지가 없다. ONNX 파일 둘만 있으면 된다.

    판정 기준 (OpenCV 문서)
        코사인 >= 0.363  같은 사람
        코사인 <  0.363  다른 사람

    **주의** — 얼굴을 못 찾으면 None 을 돌려준다. 전신 합성에서는 얼굴이
    작아 검출 자체가 실패할 수 있고, 그 실패율도 하나의 결과다.
    """

    SAME_PERSON = 0.363          # OpenCV 권장 코사인 임계값

    def __init__(self, det_onnx: str | Path, rec_onnx: str | Path,
                 score_threshold: float = 0.6, nms: float = 0.3, topk: int = 500):
        self.det = cv2.FaceDetectorYN_create(
            str(det_onnx), "", (320, 320), score_threshold, nms, topk)
        self.rec = cv2.FaceRecognizerSF_create(str(rec_onnx), "")

    def detect(self, rgb: np.ndarray, upscale_small: bool = True):
        """가장 점수 높은 얼굴 한 개의 검출 행을 돌려준다. 없으면 None.

        전신 사진은 얼굴이 작아 원본 해상도에서 놓치기 쉽다. 놓치면 상단
        절반을 2배로 키워 다시 본다 (좌표는 원본 기준으로 되돌린다).
        """
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        H, W = bgr.shape[:2]
        self.det.setInputSize((W, H))
        _, faces = self.det.detect(bgr)
        if faces is not None and len(faces):
            return bgr, faces[int(np.argmax(faces[:, -1]))]

        if not upscale_small:
            return bgr, None

        # 상단 60% 를 2배로 — 서 있는 인물은 얼굴이 위쪽에 있다
        top = bgr[: int(H * 0.6)]
        big = cv2.resize(top, (top.shape[1] * 2, top.shape[0] * 2))
        self.det.setInputSize((big.shape[1], big.shape[0]))
        _, faces = self.det.detect(big)
        if faces is None or not len(faces):
            return bgr, None
        f = faces[int(np.argmax(faces[:, -1]))].copy()
        f[:14] /= 2.0            # bbox 4 + 랜드마크 10 좌표를 원본 배율로
        return bgr, f

    def embed(self, rgb: np.ndarray) -> np.ndarray | None:
        bgr, face = self.detect(rgb)
        if face is None:
            return None
        aligned = self.rec.alignCrop(bgr, face)
        f = self.rec.feature(aligned)
        return np.asarray(f).ravel()

    def score(self, ref_rgb: np.ndarray, gen_rgb: np.ndarray) -> float | None:
        """참조 얼굴과 생성 얼굴의 코사인. 얼굴을 못 찾으면 None."""
        a, b = self.embed(ref_rgb), self.embed(gen_rgb)
        if a is None or b is None:
            return None
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def face_px(self, rgb: np.ndarray) -> float | None:
        """검출된 얼굴의 높이(픽셀). 얼굴이 몇 px 인지가 곧 정보량이다."""
        _, face = self.detect(rgb)
        return None if face is None else float(face[3])


def text_score(ref_rgb, ref_mask, gen_rgb, gen_mask, reader=None) -> float | None:
    """OCR 편집거리 기반 텍스트 보존도 (0~1). reader 가 없으면 None.

    로고·라벨이 뭉개지는 문제를 수치로 본다. easyocr 이 있으면 쓰고 없으면
    건너뛴다 — 추가 의존성을 강제하지 않는다.
    """
    if reader is None:
        try:
            import easyocr  # noqa: PLC0415
            reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        except Exception:
            return None

    def read(img, m):
        crop = _crop_to_mask(img, m)
        try:
            out = reader.readtext(crop, detail=0)
        except Exception:
            return ""
        return "".join(out).lower().replace(" ", "")

    a, b = read(ref_rgb, ref_mask), read(gen_rgb, gen_mask)
    if not a:
        return None
    d = _levenshtein(a, b)
    return max(0.0, 1.0 - d / max(len(a), 1))


def _levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def evaluate_one(
    scorer: IdentityScorer,
    ref_rgb, ref_mask, gen_rgb, gen_mask,
    *, with_text: bool = False,
) -> dict:
    """한 장에 대한 지표 묶음."""
    from .postproc import seam_score  # noqa: PLC0415

    out = {
        "identity": scorer.score(ref_rgb, ref_mask, gen_rgb, gen_mask),
        "seam": seam_score(gen_rgb, gen_mask),
    }
    if with_text:
        t = text_score(ref_rgb, ref_mask, gen_rgb, gen_mask)
        if t is not None:
            out["text"] = t
    return out


def summarize(rows: list[dict]) -> dict:
    """행 묶음을 평균/표준편차로 접는다. 객체군별로 나눠 부르면 된다."""
    keys = {k for r in rows for k in r if isinstance(r.get(k), (int, float))}
    out = {}
    for k in sorted(keys):
        v = np.array([r[k] for r in rows if k in r], np.float64)
        out[k] = {"mean": float(v.mean()), "std": float(v.std()), "n": int(v.size)}
    return out
