"""
이상 탐지 3종(PaDiM / PatchCore / EfficientAD) 벤치마크 공용 모듈

benchmark.py 와 inspect_ckpt.py 가 함께 import 한다.
경로, 캐시 환경 변수, 모델·Engine 팩토리, 보조 함수를 한곳에 모아
학습과 판정이 반드시 같은 설정으로 모델을 만들도록 한다.

주의
    이 파일을 import 하면 작업 폴더가 anomaly_benchmark 로 바뀐다.
    환경 변수 지정은 anomalib import 보다 먼저 실행되어야 하므로 이 파일 맨 위에 둔다.
"""

import os
from pathlib import Path

# ----------------------------------------------------------------------
# 경로 설정
# ----------------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

BASE_DIR = Path(script_dir)
DATASET_DIR = BASE_DIR / "dataset"
MODELS_DIR = BASE_DIR / "models"
REAL_DIR = BASE_DIR / "real_images"
CKPT_DIR = BASE_DIR / "checkpoints"
RESULTS_DIR = BASE_DIR / "results"
ANOMALIB_OUT_DIR = RESULTS_DIR / "anomalib"   # Engine 이 만드는 학습 출력
SCORES_DIR = RESULTS_DIR / "scores"
PLOTS_DIR = RESULTS_DIR / "plots"
INSPECT_DIR = RESULTS_DIR / "inspect"

for _d in (DATASET_DIR, MODELS_DIR, CKPT_DIR, RESULTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# timm / huggingface_hub / torch.hub 의 가중치 저장 위치를 models/ 로 고정한다.
# 이 값들은 import 시점에 읽히므로 anomalib 보다 먼저 지정해야 한다.
os.environ.setdefault("HF_HUB_CACHE", str(MODELS_DIR))
os.environ.setdefault("TORCH_HOME", str(MODELS_DIR))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import numpy as np

from anomalib.data import MVTecAD, PredictDataset
from anomalib.engine import Engine
from anomalib.models import EfficientAd, Padim, Patchcore

# ----------------------------------------------------------------------
# EfficientAD Teacher 가중치 저장 위치를 models/ 로 돌린다.
# anomalib 은 platformdirs 의 사용자 캐시(AppData\Local\anomalib\...)에 받는데
# 환경 변수로는 바꿀 수 없다. efficient_ad 모듈이 import 해 둔 함수 이름을 교체한다.
# (Imagenette 는 EfficientAd 생성자의 imagenet_dir 인자로 지정하므로 패치가 필요 없다)
# ----------------------------------------------------------------------
import anomalib.models.image.efficient_ad.lightning_model as _effad_module

_effad_module.get_pretrained_weights_dir = lambda: MODELS_DIR

# ----------------------------------------------------------------------
# anomalib 2.6.2 버그 우회: max_steps 로 학습하면 Engine 이 붙이는 MaxStepsProgressCallback 이
# 진행바 객체의 클래스를 함수 안의 지역 클래스로 바꾸는데, 이 때문에 체크포인트 저장 시
# "Can't get local object ... _FixedRichProgressBar" (pickle 오류)로 실패한다.
# 이 콜백은 진행바의 "Epoch X/-2" 표시만 고치는 외관용이므로 아무 동작 없는 콜백으로 교체한다.
# (학습 결과에는 영향 없음. 진행바 epoch 표시만 원래대로 나온다)
# ----------------------------------------------------------------------
import anomalib.engine.engine as _engine_module
from lightning.pytorch import Callback as _Callback


class _NoopProgressCallback(_Callback):
    pass


_engine_module.MaxStepsProgressCallback = _NoopProgressCallback

# ----------------------------------------------------------------------
# 실험 고정값 (명세 3장: 변경 금지)
# ----------------------------------------------------------------------
CATEGORY = "hazelnut"
TRAIN_COUNTS = (100, 200, 300)
SEED = 42

# 세 모델 · 학습 · 판정이 모두 이 해상도를 쓴다.
# 세 모델의 기본 전처리는 모두 Resize 이며 크롭은 쓰지 않는다.
IMAGE_SIZE = (256, 256)

MODEL_NAMES = ("padim", "patchcore", "efficientad")

# 모델별 설정. 판정(inspect_ckpt.py)은 학습 때와 같은 값을 써야 하므로
# 바꿀 일이 있으면 여기 한 곳만 바꾸고, 결과 CSV 의 notes 에도 기록한다.
PADIM_CONFIG = dict(backbone="resnet18", layers=["layer1", "layer2", "layer3"])
PATCHCORE_CONFIG = dict(
    backbone="wide_resnet50_2",
    layers=["layer2", "layer3"],
    coreset_sampling_ratio=0.1,
    num_neighbors=9,
)
EFFICIENTAD_CONFIG = dict(model_size="small")   # anomalib 의 EfficientAdModelSize: "small" / "medium"
EFFICIENTAD_STEPS = 70_000                      # 논문 기준. benchmark.py 인자로 줄일 수 있다.
IMAGENETTE_DIR = DATASET_DIR / "imagenette"     # EfficientAD 보조 데이터 (자동 다운로드)


# ----------------------------------------------------------------------
# 데이터 / 체크포인트 경로
# ----------------------------------------------------------------------
def category_name(count: int | None) -> str:
    """장수에 해당하는 카테고리 폴더 이름. None 이면 원본 hazelnut 전체."""
    return CATEGORY if count is None else f"{CATEGORY}_{count}"


def build_datamodule(
    count: int | None, train_batch_size: int = 8, eval_batch_size: int = 8, num_workers: int = 4
) -> MVTecAD:
    """dataset/hazelnut[_N] 를 읽는 데이터 모듈. 폴더가 없으면 다운로드가 시작되므로 먼저 막는다."""
    path = DATASET_DIR / category_name(count)
    if not path.is_dir():
        raise FileNotFoundError(
            f"데이터셋 폴더가 없다: {path}\n"
            "split_dataset.py 를 먼저 실행한다."
        )
    return MVTecAD(
        root=DATASET_DIR,
        category=category_name(count),
        train_batch_size=train_batch_size,
        eval_batch_size=eval_batch_size,
        num_workers=num_workers,
    )


def run_tag(model_name: str, count: int | None, seed: int | None = None) -> str:
    """실행 식별자: {model}_{count}. count=None 이면 full, 기본 시드가 아니면 _s{seed} 를 붙인다."""
    tag = f"{model_name}_{'full' if count is None else count}"
    return tag if seed is None or seed == SEED else f"{tag}_s{seed}"


def ckpt_path(model_name: str, count: int | None, seed: int | None = None) -> Path:
    """체크포인트 사본 위치: checkpoints/{model}_{count}.ckpt (count=None 이면 full)."""
    return CKPT_DIR / f"{run_tag(model_name, count, seed)}.ckpt"


# ----------------------------------------------------------------------
# 모델 / Engine 팩토리
# ----------------------------------------------------------------------
def build_model(name: str):
    """모델 이름으로 세 모델 중 하나를 만든다. 학습과 판정이 같은 함수를 쓴다.

    전처리는 세 모델 모두 IMAGE_SIZE 로 리사이즈만 하도록 명시한다.
    백본 가중치는 학습/추론이 시작될 때 models/ 로 내려받아진다.
    """
    name = name.lower()
    if name == "padim":
        return Padim(
            **PADIM_CONFIG,
            pre_processor=Padim.configure_pre_processor(image_size=IMAGE_SIZE),
        )
    if name == "patchcore":
        return Patchcore(
            **PATCHCORE_CONFIG,
            pre_processor=Patchcore.configure_pre_processor(image_size=IMAGE_SIZE),
        )
    if name == "efficientad":
        return EfficientAd(
            **EFFICIENTAD_CONFIG,
            imagenet_dir=IMAGENETTE_DIR,
            pre_processor=EfficientAd.configure_pre_processor(image_size=IMAGE_SIZE),
        )
    raise ValueError(f"알 수 없는 모델: {name} (선택: {', '.join(MODEL_NAMES)})")


def build_engine(name: str, efficientad_steps: int = EFFICIENTAD_STEPS, **kwargs) -> Engine:
    """모델별 Engine. 학습 반복 인자가 모델마다 다르므로 분리한다.

    padim / patchcore  역전파 학습이 없어 1 epoch 로 충분하다. (늘려도 결과 동일)
    efficientad        실제 학습이라 max_steps 로 반복 수를 정한다.
                       max_epochs=-1 로 두어 max_steps 만으로 종료되게 한다.
    """
    name = name.lower()
    kwargs.setdefault("default_root_dir", ANOMALIB_OUT_DIR)
    if name in ("padim", "patchcore"):
        return Engine(max_epochs=1, **kwargs)
    if name == "efficientad":
        return Engine(max_epochs=-1, max_steps=efficientad_steps, **kwargs)
    raise ValueError(f"알 수 없는 모델: {name} (선택: {', '.join(MODEL_NAMES)})")


def model_notes(name: str, efficientad_steps: int = EFFICIENTAD_STEPS) -> str:
    """결과 CSV 의 notes 칸에 적을 설정 요약."""
    name = name.lower()
    cfg = {"padim": PADIM_CONFIG, "patchcore": PATCHCORE_CONFIG, "efficientad": EFFICIENTAD_CONFIG}[name]
    text = ";".join(f"{k}={v}" for k, v in cfg.items())
    if name == "efficientad":
        text += f";max_steps={efficientad_steps}"
    return f"{text};image_size={IMAGE_SIZE[0]}x{IMAGE_SIZE[1]}"


# ----------------------------------------------------------------------
# 보조 함수 (patchcore_anomaly_detection.py 와 동일)
# ----------------------------------------------------------------------
def _as_list(value):
    """스칼라와 배치 출력을 동일한 형태로 취급한다."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    arr = np.asarray(value)
    return arr.tolist() if arr.ndim > 0 else [arr]


def _resize_map(anomaly_map: np.ndarray, shape) -> np.ndarray:
    """이상 맵을 원본 이미지 크기로 확대한다."""
    try:
        import cv2

        return cv2.resize(anomaly_map, (shape[1], shape[0]))
    except ImportError:
        ys = (np.linspace(0, anomaly_map.shape[0] - 1, shape[0])).astype(int)
        xs = (np.linspace(0, anomaly_map.shape[1] - 1, shape[1])).astype(int)
        return anomaly_map[np.ix_(ys, xs)]
