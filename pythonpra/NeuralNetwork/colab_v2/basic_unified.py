# ============================================================
# 기준선 — 헤드만 통일
#
#   v1(keras1 / torch1)에서 딱 하나만 바꿨다:
#     PyTorch 쪽 은닉 Linear(57600,128)를 빼고 Dropout(0.5)을 넣어
#     두 프레임워크의 분류 헤드를 Flatten -> Dropout -> Dense(11)로 통일.
#     v1은 653,003 대 7,393,739로 11.3배 벌어져 있었다.
#
#   나머지는 전부 각 프레임워크 기본값 그대로 둔다.
#   초기화, bias, Adam epsilon, 출력 형태 — 손대지 않았다.
#
#   2 Conv (32, 64) · BatchNorm 없음 · 증강 없음
#   Adam lr=1e-3 · batch 32 · epoch 5 · 시드 0
#
#   기대값: 두 셀 모두 파라미터 653,003
# ============================================================


# ─────────────────────────────────────────────
# 셀 0 — 데이터 복사 (최초 1회, 런타임 끊기면 다시)
# ─────────────────────────────────────────────
# !cp -r /content/drive/MyDrive/food11 /content/food11


# ─────────────────────────────────────────────
# 셀 1 — Keras
# ─────────────────────────────────────────────
import numpy as np
import keras
from keras import layers
import matplotlib.pyplot as plt

DATA_DIR = "/content/food11"
IMG, BATCH, EPOCHS, SEED = 128, 32, 5, 0
NUM_CLASSES = 11

keras.utils.set_random_seed(SEED)


def load(split, shuffle):
    ds = keras.utils.image_dataset_from_directory(
        f"{DATA_DIR}/{split}", image_size=(IMG, IMG),
        batch_size=BATCH, shuffle=shuffle, seed=SEED)
    rescale = layers.Rescaling(1.0 / 255)
    return ds.map(lambda x, y: (rescale(x), y))


train_ds = load("training", True)
val_ds = load("validation", False)
test_ds = load("evaluation", False)

# 128 -> conv 126 -> pool 63 -> conv 61 -> pool 30
model = keras.Sequential([
    keras.Input(shape=(IMG, IMG, 3)),

    layers.Conv2D(32, 3, activation="relu"),
    layers.MaxPooling2D(2),

    layers.Conv2D(64, 3, activation="relu"),
    layers.MaxPooling2D(2),

    layers.Flatten(),
    layers.Dropout(0.5),
    layers.Dense(NUM_CLASSES, activation="softmax"),
])

n_params = int(sum(np.prod(w.shape) for w in model.trainable_weights))
print(f"학습 파라미터: {n_params:,}")

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-3),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

history = model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS)
test_loss, test_acc = model.evaluate(test_ds)
print(f"\n[Keras] test acc {test_acc:.4f} · loss {test_loss:.4f} "
      f"· 파라미터 {n_params:,}")


# ---- 학습 곡선 ----
def plot_curves(ep, tr_acc, va_acc, tr_loss, va_loss, title, subtitle, outfile):
    ACCENT, DARKGY = "#16785C", "#3A4353"
    GRID, TEXT, MUTED = "#DDD9D2", "#14181F", "#6B7482"
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7), dpi=170)
    fig.suptitle(title, fontsize=14.5, color=TEXT, y=0.96)
    fig.text(0.5, 0.875, subtitle, ha="center", fontsize=10, color=MUTED)

    step = max(1, len(ep) // 10)
    for ax, tr, va, ylab in ((axes[0], tr_acc, va_acc, "Accuracy"),
                             (axes[1], tr_loss, va_loss, "Loss")):
        ax.plot(ep, tr, color=ACCENT, lw=2.2, marker="o", ms=4.5, label="Train")
        ax.plot(ep, va, color=DARKGY, lw=2.2, ls="--", marker="s", ms=4,
                label="Validation")
        ax.set_xlabel("Epoch", fontsize=10.5, color=MUTED)
        ax.set_ylabel(ylab, fontsize=11.5, color=TEXT)
        ax.set_xticks(ep[::step])
        ax.grid(True, color=GRID, lw=0.8, alpha=0.9)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GRID)
        ax.tick_params(colors=MUTED, labelsize=9.5)
        ax.legend(frameon=False, fontsize=10, labelcolor=TEXT)

    fig.tight_layout()
    fig.subplots_adjust(top=0.80)
    fig.savefig(outfile, facecolor="white")
    plt.show()
    print(f"[그래프] {outfile}")


h = history.history
plot_curves(
    list(range(1, len(h["accuracy"]) + 1)),
    h["accuracy"], h["val_accuracy"], h["loss"], h["val_loss"],
    "Keras CNN (2 Conv)  ·  Adam",
    "lr=1e-3  ·  batch=32  ·  epochs=5  ·  no augmentation  ·  head unified",
    "curve_v2_keras_basic.png",
)


# ─────────────────────────────────────────────
# 셀 2 — PyTorch
# ─────────────────────────────────────────────
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import matplotlib.pyplot as plt

DATA_DIR = "/content/food11"
IMG, BATCH, EPOCHS, SEED = 128, 32, 5, 0
NUM_CLASSES = 11

np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)

tf_ = transforms.Compose([
    transforms.Resize((IMG, IMG)),
    transforms.ToTensor(),          # 0~1 변환 + HWC -> CHW
])
g = torch.Generator().manual_seed(SEED)


def load(split, shuffle):
    ds = datasets.ImageFolder(f"{DATA_DIR}/{split}", transform=tf_)
    return DataLoader(ds, batch_size=BATCH, shuffle=shuffle,
                      generator=g if shuffle else None,
                      num_workers=2, pin_memory=True)


train_dl = load("training", True)
val_dl = load("validation", False)
test_dl = load("evaluation", False)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using {device} device")

# 128 -> conv 126 -> pool 63 -> conv 61 -> pool 30
# v1에는 여기에 Linear(57600, 128)이 있고 Dropout이 없었다. 그 둘만 바꿨다.
model = nn.Sequential(
    nn.Conv2d(3, 32, 3), nn.ReLU(), nn.MaxPool2d(2, 2),
    nn.Conv2d(32, 64, 3), nn.ReLU(), nn.MaxPool2d(2, 2),
    nn.Flatten(),
    nn.Dropout(0.5),
    nn.Linear(64 * 30 * 30, NUM_CLASSES),
).to(device)

n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"학습 파라미터: {n_params:,}")

loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)


def evaluate(dataloader):
    model.eval()
    total, correct, n = 0.0, 0, 0
    with torch.no_grad():
        for X, y in dataloader:
            X, y = X.to(device), y.to(device)
            pred = model(X)
            total += loss_fn(pred, y).item() * y.size(0)
            correct += (pred.argmax(1) == y).sum().item()
            n += y.size(0)
    return total / n, correct / n


hist = {"train_acc": [], "train_loss": [], "val_acc": [], "val_loss": []}

for epoch in range(EPOCHS):
    model.train()
    total, correct, n = 0.0, 0, 0
    for X, y in train_dl:
        X, y = X.to(device), y.to(device)
        pred = model(X)
        loss = loss_fn(pred, y)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        total += loss.item() * y.size(0)
        correct += (pred.argmax(1) == y).sum().item()
        n += y.size(0)
    train_loss, train_acc = total / n, correct / n

    val_loss, val_acc = evaluate(val_dl)
    print(f"Epoch {epoch+1}/{EPOCHS}  "
          f"accuracy: {train_acc:.4f} - loss: {train_loss:.4f}  |  "
          f"val_accuracy: {val_acc:.4f} - val_loss: {val_loss:.4f}")

    hist["train_acc"].append(train_acc)
    hist["train_loss"].append(train_loss)
    hist["val_acc"].append(val_acc)
    hist["val_loss"].append(val_loss)

test_loss, test_acc = evaluate(test_dl)
print(f"\n[PyTorch] test acc {test_acc:.4f} · loss {test_loss:.4f} "
      f"· 파라미터 {n_params:,}")


# ---- 학습 곡선 ----
# 셀 1을 안 돌렸을 수도 있으므로 여기서도 정의해 둔다
def plot_curves(ep, tr_acc, va_acc, tr_loss, va_loss, title, subtitle, outfile):
    ACCENT, DARKGY = "#16785C", "#3A4353"
    GRID, TEXT, MUTED = "#DDD9D2", "#14181F", "#6B7482"
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7), dpi=170)
    fig.suptitle(title, fontsize=14.5, color=TEXT, y=0.96)
    fig.text(0.5, 0.875, subtitle, ha="center", fontsize=10, color=MUTED)

    step = max(1, len(ep) // 10)
    for ax, tr, va, ylab in ((axes[0], tr_acc, va_acc, "Accuracy"),
                             (axes[1], tr_loss, va_loss, "Loss")):
        ax.plot(ep, tr, color=ACCENT, lw=2.2, marker="o", ms=4.5, label="Train")
        ax.plot(ep, va, color=DARKGY, lw=2.2, ls="--", marker="s", ms=4,
                label="Validation")
        ax.set_xlabel("Epoch", fontsize=10.5, color=MUTED)
        ax.set_ylabel(ylab, fontsize=11.5, color=TEXT)
        ax.set_xticks(ep[::step])
        ax.grid(True, color=GRID, lw=0.8, alpha=0.9)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GRID)
        ax.tick_params(colors=MUTED, labelsize=9.5)
        ax.legend(frameon=False, fontsize=10, labelcolor=TEXT)

    fig.tight_layout()
    fig.subplots_adjust(top=0.80)
    fig.savefig(outfile, facecolor="white")
    plt.show()
    print(f"[그래프] {outfile}")


plot_curves(
    list(range(1, EPOCHS + 1)),
    hist["train_acc"], hist["val_acc"], hist["train_loss"], hist["val_loss"],
    "PyTorch CNN (2 Conv)  ·  Adam",
    "lr=1e-3  ·  batch=32  ·  epochs=5  ·  no augmentation  ·  head unified",
    "curve_v2_torch_basic.png",
)


# ============================================================
# 차이가 나면 여기서부터 하나씩 (한 번에 하나만)
#
#   1) 초기화     Keras Glorot / PyTorch kaiming_uniform(a=sqrt5)
#                 -> 둘 다 He normal 로
#                 std(Keras 대 PyTorch)는 층마다 다르다
#                   Conv1 0.080 대 0.111 · Conv2 0.048 대 0.034
#                   Dense 0.0059 대 0.0024
#                 넷 중 차이가 가장 크다
#
#   2) 출력 형태  Keras softmax+from_logits=False / PyTorch logit
#                 -> Keras도 logit + from_logits=True 로
#                 정확도는 안 바뀌고 loss 계산 경로만 통일된다
#
#   3) bias       Keras zeros / PyTorch uniform(+-1/sqrt(fan_in))
#
#   4) Adam eps   Keras 1e-7 / PyTorch 1e-8
#
#   차이가 안 나면 아무것도 더 넣을 필요 없다.
# ============================================================
