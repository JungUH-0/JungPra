# ============================================================
# Keras 3 - keras2와 동일 구조 + AdamW + ReduceLROnPlateau
#
#   이미지        128 x 128 x 3
#   배치          32
#   옵티마이저     AdamW (lr=1e-3, weight_decay=1e-4)
#   스케줄러       ReduceLROnPlateau (factor=0.5, patience=2, min_lr=1e-6)
#   epoch         최대 30 (EarlyStopping patience=7, restore_best_weights)
#   증강          RandomFlip(horizontal) / RandomRotation(0.1 = ±36°) / RandomZoom(0.1)
#   BatchNorm     Conv 블록 3개 각각 뒤 (Conv -> ReLU -> BN 순서)
#   초기화        he_normal (Conv 3개 모두 명시)
#   Dropout       0.5 (Flatten 뒤 1개)
#
#   * EarlyStopping patience(7)를 ReduceLROnPlateau patience(2)보다
#     충분히 크게 둔 이유: 학습률을 낮춘 직후 바로 종료되면
#     감소 효과를 쓰지 못하기 때문
# ============================================================

import os
import keras
from keras import layers
import matplotlib.pyplot as plt

DATA_DIR = "/content/food11"
IMG_SIZE = (128, 128)
BATCH_SIZE = 32
NUM_CLASSES = 11

train_ds = keras.utils.image_dataset_from_directory(
    os.path.join(DATA_DIR, "training"),
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
)
val_ds = keras.utils.image_dataset_from_directory(
    os.path.join(DATA_DIR, "validation"),
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
)
test_ds = keras.utils.image_dataset_from_directory(
    os.path.join(DATA_DIR, "evaluation"),
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
)

rescale = layers.Rescaling(1.0 / 255)
train_ds = train_ds.map(lambda x, y: (rescale(x), y))
val_ds = val_ds.map(lambda x, y: (rescale(x), y))
test_ds = test_ds.map(lambda x, y: (rescale(x), y))

model = keras.Sequential([
    keras.Input(shape=(128, 128, 3)),
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.1),

    layers.Conv2D(32, kernel_size=3, activation="relu", kernel_initializer="he_normal"),
    layers.BatchNormalization(),
    layers.MaxPooling2D(pool_size=2),

    layers.Conv2D(64, kernel_size=3, activation="relu", kernel_initializer="he_normal"),
    layers.BatchNormalization(),
    layers.MaxPooling2D(pool_size=2),

    layers.Conv2D(128, kernel_size=3, activation="relu", kernel_initializer="he_normal"),
    layers.BatchNormalization(),
    layers.MaxPooling2D(pool_size=2),

    layers.Flatten(),
    layers.Dropout(0.5),
    layers.Dense(NUM_CLASSES, activation="softmax"),
])
model.summary()

model.compile(
    optimizer=keras.optimizers.AdamW(learning_rate=1e-3, weight_decay=1e-4),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

early_stop = keras.callbacks.EarlyStopping(
    monitor="val_loss", patience=7, restore_best_weights=True
)
reduce_lr = keras.callbacks.ReduceLROnPlateau(
    monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6
)

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=30,
    callbacks=[early_stop, reduce_lr],
)

test_loss, test_acc = model.evaluate(test_ds)
print(f"Test accuracy: {test_acc:.4f}")


# ============================================================
# 학습 곡선 저장 (PPT 삽입용)
# ============================================================
MODEL_NAME = "Keras CNN (3 Conv + BN)"
OPTIMIZER_NAME = "AdamW + ReduceLR"
SETTINGS = "lr=1e-3  ·  wd=1e-4  ·  batch=32  ·  augment  ·  EarlyStop p=7"
OUTFILE = "curve_keras3.png"

ACCENT, DARKGY, GRID, TEXT, MUTED = "#16785C", "#3A4353", "#DDD9D2", "#14181F", "#6B7482"

h = history.history
ep = list(range(1, len(h["accuracy"]) + 1))

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(1, 2, figsize=(10, 3.7), dpi=170)
fig.suptitle(f"{MODEL_NAME}  ·  {OPTIMIZER_NAME}", fontsize=14.5, color=TEXT, y=0.96)
fig.text(0.5, 0.875, SETTINGS, ha="center", fontsize=10, color=MUTED)

panels = [
    (axes[0], h["accuracy"], h["val_accuracy"], "Accuracy"),
    (axes[1], h["loss"], h["val_loss"], "Loss"),
]
step = max(1, len(ep) // 10)
for ax, tr, va, ylab in panels:
    ax.plot(ep, tr, color=ACCENT, lw=2.2, marker="o", ms=4.5, label="Train")
    ax.plot(ep, va, color=DARKGY, lw=2.2, ls="--", marker="s", ms=4, label="Validation")
    ax.set_xlabel("Epoch", fontsize=10.5, color=MUTED)
    ax.set_ylabel(ylab, fontsize=11.5, color=TEXT)
    ax.set_xticks(ep[::step])
    ax.grid(True, color=GRID, lw=0.8, alpha=0.9)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9.5)
    ax.legend(frameon=False, fontsize=10, labelcolor=TEXT)

fig.tight_layout()
fig.subplots_adjust(top=0.80)
fig.savefig(OUTFILE, facecolor="white")
plt.show()

print(f"\n[최종] test accuracy {test_acc*100:.1f}%  ·  test loss {test_loss:.4f}")
print(f"[정지] {len(ep)} epoch에서 종료 (한도 30)")
print(f"[그래프] {OUTFILE}")

try:
    from google.colab import files
    files.download(OUTFILE)
except Exception:
    pass
