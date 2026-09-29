"""CGIv2 — AnyDoor 가중치는 그대로 쓰고 전처리·후처리만 우리가 짠다.

경계는 하나다.

    [전처리]  마스크 생성 · 객체 정규화 · 배치 마스크      우리 영역
       |
    process_pairs                                          규약 (숫자를 지킨다)
       |
    [가중치 라인]  DINOv2 -> ControlNet -> U-Net -> DDIM -> VAE
       |                                                   손대지 않음
    crop_back 역변환                                        규약
       |
    [후처리]  블렌딩 · 색 정합 · 그림자 · 평가              우리 영역

가중치 라인을 건드리면 안 되는 이유는 하나로 요약된다 — 조건 경로가 DINOv2
하나뿐이라 대체 경로가 없다. 인코더를 바꾸는 순간 projector·U-Net 크로스
어텐션·ControlNet 이 전부 무의미해지고 VAE 84M 만 남는다 (전체의 3.4%).
"""
from .anydoor import AnyDoorEngine
from .face_restore import FaceTransplanter
from .pairs import PairBuilder, crop_back
from .pipeline import Compositor, Result, Settings, load_pair

__all__ = [
    "AnyDoorEngine",
    "PairBuilder",
    "crop_back",
    "Compositor",
    "Settings",
    "Result",
    "load_pair",
    "FaceTransplanter",
]
