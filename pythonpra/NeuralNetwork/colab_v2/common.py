# ============================================================
# Food-11 실험 v2 — 공통 하네스
#
#   설정 하나(Config)에서 두 프레임워크 모델이 파생된다.
#   조건을 바꾸려면 Config를 바꾸는 수밖에 없어서
#   한쪽만 고치는 실수가 구조적으로 불가능하다.
#
#   콜랩에서 셀 하나에 통째로 붙여넣고 실행.
# ============================================================

import csv
import json
import os
import random
import time
from dataclasses import dataclass, asdict, replace, fields

import numpy as np

DATA_DIR = "/content/food11"
RESULTS_CSV = "/content/drive/MyDrive/food11_v2_results.csv"  # 런타임 끊겨도 남도록
NUM_CLASSES = 11
SEEDS = [0, 1, 2]


# ============================================================
# 1. 설정 — 모든 값을 명시한다
#
#   v1에서 "고정한 조건"과 "그냥 기본값을 쓴 것"이 섞였던 게
#   설계 지적의 뿌리였다. 여기서는 기본값에 기대지 않는다.
# ============================================================

@dataclass(frozen=True)
class Config:
    # --- 데이터 ---
    img_size: int = 128
    batch_size: int = 32

    # --- 증강 (도 단위로 통일. 각 어댑터가 변환한다) ---
    aug_flip: bool = True
    aug_rotate_deg: float = 10.0   # Keras는 /360 해서 넘긴다
    aug_zoom: float = 0.0          # 0이면 끔

    # --- 모델 ---
    conv_channels: tuple = (32, 64, 128)
    kernel: int = 3
    padding: int = 0               # 명시. 0이면 128->126
    pool: int = 2
    use_batchnorm: bool = True
    head_hidden: int = 0           # 0이면 Flatten->Dense 직결 (두 프레임워크 통일)
    dropout: float = 0.5           # Flatten 뒤
    spatial_dropout: float = 0.0   # Conv 블록 뒤. v1에 없던 축

    # --- 두 프레임워크를 맞추기 위해 명시하는 값들 ---
    #     기본값에 맡기면 서로 다른 값이 적용된다. 아래 6개가 그 목록.
    bn_momentum: float = 0.1       # PyTorch 관례(배치당 갱신 비율).
                                   # Keras에는 1 - 값 을 넘긴다
    bn_eps: float = 1e-5           # Keras 기본 1e-3, PyTorch 1e-5 -> 후자로 통일
    adam_eps: float = 1e-8         # Keras 기본 1e-7, PyTorch 1e-8 -> 후자로 통일

    # --- 학습 ---
    optimizer: str = "adam"        # sgd | sgd_momentum | adam | adamw
    lr: float = 1e-3
    momentum: float = 0.9
    weight_decay: float = 0.0
    epochs: int = 30
    es_patience: int = 7
    es_monitor: str = "val_loss"   # val_loss | val_accuracy
    lr_sched: bool = False         # ReduceLROnPlateau
    lr_sched_factor: float = 0.5
    lr_sched_patience: int = 2

    # --- 재현 ---
    seed: int = 0

    def id(self) -> str:
        """조건을 사람이 읽을 수 있는 짧은 이름으로."""
        parts = [self.optimizer, f"lr{self.lr:g}"]
        if self.weight_decay:    parts.append(f"wd{self.weight_decay:g}")
        if self.aug_flip or self.aug_rotate_deg: parts.append("aug")
        if self.use_batchnorm:   parts.append("bn")
        if self.dropout:         parts.append(f"do{self.dropout:g}")
        if self.spatial_dropout: parts.append(f"sdo{self.spatial_dropout:g}")
        if self.lr_sched:        parts.append("sched")
        return "_".join(parts)


BASELINE = Config()  # Phase 3의 기준점


# ============================================================
# 2. 시드 — v1이 하나도 안 잡았던 부분
# ============================================================

def set_all_seeds(seed: int):
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    try:
        import tensorflow as tf
        tf.keras.utils.set_random_seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


# ============================================================
# 3. 차원 계산 — 두 프레임워크가 같은 값을 쓰도록 한곳에서
# ============================================================

def flatten_dim(cfg: Config) -> int:
    """Conv/Pool을 거친 뒤 Flatten 크기. 파라미터 수 검사의 근거."""
    s = cfg.img_size
    for _ in cfg.conv_channels:
        s = s + 2 * cfg.padding - cfg.kernel + 1   # Conv
        s = s // cfg.pool                          # Pool (버림)
    return cfg.conv_channels[-1] * s * s


def expected_params(cfg: Config) -> int:
    """두 프레임워크가 맞춰야 할 목표 파라미터 수.

    BatchNorm은 학습 파라미터(gamma, beta)만 센다.
    Keras는 통계 버퍼까지 파라미터로 세므로 비교할 때 빼야 한다.
    """
    total, c_in = 0, 3
    for c_out in cfg.conv_channels:
        total += cfg.kernel * cfg.kernel * c_in * c_out + c_out
        if cfg.use_batchnorm:
            total += 2 * c_out
        c_in = c_out
    f = flatten_dim(cfg)
    if cfg.head_hidden:
        total += f * cfg.head_hidden + cfg.head_hidden
        total += cfg.head_hidden * NUM_CLASSES + NUM_CLASSES
    else:
        total += f * NUM_CLASSES + NUM_CLASSES
    return total


# ============================================================
# 4. Keras 쪽
# ============================================================

def build_keras(cfg: Config):
    import keras
    from keras import layers

    L = [keras.Input(shape=(cfg.img_size, cfg.img_size, 3))]

    if cfg.aug_flip:
        L.append(layers.RandomFlip("horizontal"))
    if cfg.aug_rotate_deg:
        # 단위 변환: Keras는 2*pi의 비율로 받는다.
        # 빈칸 채움도 맞춘다 — Keras 기본은 reflect인데 torchvision의
        # 회전은 reflect를 지원하지 않으므로 양쪽을 constant(검정)로 통일한다.
        L.append(layers.RandomRotation(cfg.aug_rotate_deg / 360.0,
                                       fill_mode="constant", fill_value=0.0))
    if cfg.aug_zoom:
        L.append(layers.RandomZoom(cfg.aug_zoom,
                                   fill_mode="constant", fill_value=0.0))

    pad = "same" if cfg.padding else "valid"
    init = dict(kernel_initializer="he_normal", bias_initializer="zeros")

    for c in cfg.conv_channels:
        L.append(layers.Conv2D(c, cfg.kernel, padding=pad,
                               activation="relu", **init))
        if cfg.use_batchnorm:
            # Keras의 momentum은 "유지 비율"이라 PyTorch와 의미가 반대다
            L.append(layers.BatchNormalization(
                momentum=1.0 - cfg.bn_momentum, epsilon=cfg.bn_eps))
        L.append(layers.MaxPooling2D(cfg.pool))
        if cfg.spatial_dropout:
            L.append(layers.SpatialDropout2D(cfg.spatial_dropout))

    L.append(layers.Flatten())
    if cfg.head_hidden:
        L.append(layers.Dense(cfg.head_hidden, activation="relu", **init))
    if cfg.dropout:
        L.append(layers.Dropout(cfg.dropout))
    # softmax를 넣지 않는다 — PyTorch와 같이 logit을 내보내고
    # 손실함수에서 from_logits=True로 처리한다 (수치적으로도 더 안정적)
    L.append(layers.Dense(NUM_CLASSES, **init))
    return keras.Sequential(L)


def keras_optimizer(cfg: Config):
    import keras
    if cfg.optimizer == "sgd":
        return keras.optimizers.SGD(learning_rate=cfg.lr, momentum=0.0)
    if cfg.optimizer == "sgd_momentum":
        return keras.optimizers.SGD(learning_rate=cfg.lr, momentum=cfg.momentum)
    if cfg.optimizer == "adam":
        return keras.optimizers.Adam(learning_rate=cfg.lr, epsilon=cfg.adam_eps)
    if cfg.optimizer == "adamw":
        return keras.optimizers.AdamW(learning_rate=cfg.lr,
                                      weight_decay=cfg.weight_decay,
                                      epsilon=cfg.adam_eps)
    raise ValueError(cfg.optimizer)


def keras_data(cfg: Config):
    import keras
    from keras import layers

    def load(split, shuffle):
        ds = keras.utils.image_dataset_from_directory(
            os.path.join(DATA_DIR, split),
            image_size=(cfg.img_size, cfg.img_size),
            batch_size=cfg.batch_size,
            shuffle=shuffle,
            seed=cfg.seed,
        )
        rescale = layers.Rescaling(1.0 / 255)
        return ds.map(lambda x, y: (rescale(x), y))

    return (load("training", True),
            load("validation", False),   # PyTorch와 맞춤 (v1은 여기가 어긋났다)
            load("evaluation", False))


# ============================================================
# 5. PyTorch 쪽
# ============================================================

def build_torch(cfg: Config):
    import torch
    from torch import nn

    layers_ = []
    c_in = 3
    for c in cfg.conv_channels:
        layers_.append(nn.Conv2d(c_in, c, cfg.kernel, padding=cfg.padding))
        layers_.append(nn.ReLU())
        if cfg.use_batchnorm:
            layers_.append(nn.BatchNorm2d(c, eps=cfg.bn_eps,
                                          momentum=cfg.bn_momentum))
        layers_.append(nn.MaxPool2d(cfg.pool, cfg.pool))
        if cfg.spatial_dropout:
            layers_.append(nn.Dropout2d(cfg.spatial_dropout))
        c_in = c

    layers_.append(nn.Flatten())
    f = flatten_dim(cfg)
    if cfg.head_hidden:
        layers_.append(nn.Linear(f, cfg.head_hidden))
        layers_.append(nn.ReLU())
        f = cfg.head_hidden
    if cfg.dropout:
        layers_.append(nn.Dropout(cfg.dropout))
    layers_.append(nn.Linear(f, NUM_CLASSES))   # logit 그대로

    model = nn.Sequential(*layers_)
    apply_he_init(model)
    return model


def apply_he_init(model):
    """Keras의 he_normal + bias zeros에 맞춘다.

    PyTorch 기본은 kaiming_uniform_(a=sqrt(5))인데, 이는 He가 아니다.
    fan_in=288에서 표준편차가 0.034로, 진짜 He(0.083)보다 2.45배 작다.
    bias도 기본은 uniform(+-1/sqrt(fan_in))이라 zeros가 아니다.
    """
    from torch import nn
    for m in model.modules():
        if isinstance(m, (nn.Conv2d, nn.Linear)):
            nn.init.kaiming_normal_(m.weight, mode="fan_in", nonlinearity="relu")
            if m.bias is not None:
                nn.init.zeros_(m.bias)


def torch_optimizer(cfg: Config, model):
    import torch
    p = model.parameters()
    if cfg.optimizer == "sgd":
        return torch.optim.SGD(p, lr=cfg.lr, momentum=0.0)
    if cfg.optimizer == "sgd_momentum":
        return torch.optim.SGD(p, lr=cfg.lr, momentum=cfg.momentum)
    if cfg.optimizer == "adam":
        return torch.optim.Adam(p, lr=cfg.lr)
    if cfg.optimizer == "adamw":
        return torch.optim.AdamW(p, lr=cfg.lr, weight_decay=cfg.weight_decay)
    raise ValueError(cfg.optimizer)


def torch_data(cfg: Config):
    import torch
    from torch.utils.data import DataLoader
    from torchvision import datasets, transforms

    base = [transforms.Resize((cfg.img_size, cfg.img_size))]
    aug = list(base)
    if cfg.aug_flip:
        aug.append(transforms.RandomHorizontalFlip())
    if cfg.aug_rotate_deg or cfg.aug_zoom:
        # 회전과 확대/축소를 RandomAffine 하나로 처리한다.
        #   - RandomResizedCrop은 scale이 면적 비율(<=1)이라 확대를 못 한다
        #   - RandomAffine은 scale>1을 받아 Keras RandomZoom과 대응된다
        #   - fill=0 으로 Keras 쪽 constant 채움과 맞춘다
        aug.append(transforms.RandomAffine(
            degrees=cfg.aug_rotate_deg,
            scale=(1 - cfg.aug_zoom, 1 + cfg.aug_zoom) if cfg.aug_zoom else None,
            fill=0))
    aug.append(transforms.ToTensor())
    base.append(transforms.ToTensor())

    train_tf, eval_tf = transforms.Compose(aug), transforms.Compose(base)
    g = torch.Generator().manual_seed(cfg.seed)

    def load(split, tf, shuffle):
        ds = datasets.ImageFolder(os.path.join(DATA_DIR, split), transform=tf)
        return DataLoader(ds, batch_size=cfg.batch_size, shuffle=shuffle,
                          generator=g if shuffle else None,
                          num_workers=2, pin_memory=True)

    return (load("training", train_tf, True),
            load("validation", eval_tf, False),
            load("evaluation", eval_tf, False))


# ============================================================
# 6. 파라미터 일치 검사 — 통과 못 하면 실험이 시작되지 않는다
# ============================================================

def count_keras(model) -> int:
    """학습 파라미터만. BatchNorm 통계 버퍼는 제외."""
    return int(sum(np.prod(w.shape) for w in model.trainable_weights))


def count_torch(model) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def keras_shapes(model) -> list:
    """Keras 가중치 shape를 PyTorch 표기로 바꿔 순서대로.

    Conv  (kh, kw, in, out) -> (out, in, kh, kw)
    Dense (in, out)         -> (out, in)
    """
    out = []
    for w in model.trainable_weights:
        s = tuple(int(d) for d in w.shape)
        if len(s) == 4:
            s = (s[3], s[2], s[0], s[1])
        elif len(s) == 2:
            s = (s[1], s[0])
        out.append(s)
    return out


def torch_shapes(model) -> list:
    return [tuple(p.shape) for p in model.parameters() if p.requires_grad]


def assert_param_match(cfg: Config, verbose=True):
    """개수만이 아니라 층별 shape까지 비교한다.

    개수가 같아도 구조가 다를 수 있다. v1에서 초기화 표준편차가 2.45배
    달랐던 것처럼, 총합 검사로는 안 잡히는 차이가 실재한다.
    """
    km, tm = build_keras(cfg), build_torch(cfg)
    ks, ts = keras_shapes(km), torch_shapes(tm)
    k, t, e = count_keras(km), count_torch(tm), expected_params(cfg)

    if verbose:
        print(f"[파라미터] Keras {k:,} · PyTorch {t:,} · 예상 {e:,}")
        print(f"[가중치 텐서] Keras {len(ks)}개 · PyTorch {len(ts)}개")

    if ks != ts:
        lines = ["두 모델의 구조가 다르다 (층별 shape 불일치):"]
        for i in range(max(len(ks), len(ts))):
            a = ks[i] if i < len(ks) else None
            b = ts[i] if i < len(ts) else None
            mark = "  " if a == b else "<-"
            lines.append(f"  {i:>2} Keras {str(a):<22} PyTorch {str(b):<22}{mark}")
        raise AssertionError("\n".join(lines))

    if k != t:
        raise AssertionError(
            f"파라미터 수가 다르다: Keras {k:,} vs PyTorch {t:,}\n"
            f"  이 상태로 비교하면 v1과 같은 실수를 반복한다."
        )
    if k != e:
        print(f"  ⚠ 예상값과 다름 ({k:,} vs {e:,}) — flatten_dim 계산 확인")
    if verbose:
        print("  ✓ 층별 shape·파라미터 수 일치")
    return k


def compare_init(cfg: Config, n=3):
    """초기화 분포까지 같은지 실제 가중치로 확인한다.

    파라미터 수와 shape가 같아도 초기값 분포가 다르면 다른 모델이다.
    """
    import numpy as np
    km, tm = build_keras(cfg), build_torch(cfg)
    kw = [w for w in km.trainable_weights if len(w.shape) == 4]
    tw = [p for p in tm.parameters() if p.dim() == 4]
    print(f"{'층':<6}{'Keras std':>12}{'PyTorch std':>14}{'비율':>9}")
    print("-" * 41)
    for i, (a, b) in enumerate(zip(kw[:n], tw[:n])):
        sa = float(np.std(np.asarray(a)))
        sb = float(b.detach().std())
        print(f"conv{i+1:<2}{sa:>12.5f}{sb:>14.5f}{sb/sa:>9.2f}")
    print("\n비율이 1.00 근처면 통일된 것. v1은 0.41이었다.")


# ============================================================
# 7. 결과 기록 — 한 줄씩 즉시 디스크로
# ============================================================

CSV_COLS = (["phase", "cfg_id", "framework", "n_params",
             "epochs_ran", "stopped_by",
             "train_acc", "val_acc", "test_acc",
             "train_loss", "val_loss", "test_loss",
             "per_class_recall", "lr_history", "wall_sec"]
            + [f.name for f in fields(Config)])


def append_result(row: dict):
    new = not os.path.exists(RESULTS_CSV)
    os.makedirs(os.path.dirname(RESULTS_CSV), exist_ok=True)
    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as fp:
        w = csv.DictWriter(fp, fieldnames=CSV_COLS, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow(row)
    print(f"[기록] {row['cfg_id']} / {row['framework']} / seed={row['seed']}"
          f"  test={row['test_acc']:.4f}")


def per_class_recall(y_true, y_pred) -> list:
    """클래스별 재현율. v1에 없던 지표 — 정확도 하나로만 봤다."""
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    out = []
    for c in range(NUM_CLASSES):
        m = y_true == c
        out.append(round(float((y_pred[m] == c).mean()), 4) if m.any() else None)
    return out
