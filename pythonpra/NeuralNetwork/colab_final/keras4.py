# ============================================================
# Keras 4 - keras1과 옵티마이저만 다른 대조군
#
#   keras1 : Adam
#   keras4 : SGD + momentum 0.9     <-- 이 한 줄만 다름
#
#   나머지는 전부 동일 (2 Conv / 증강 없음 / BatchNorm 없음 /
#   Dropout 0.5 / 15 epoch 고정 / lr=1e-3 / batch=32)
#   -> 두 곡선을 나란히 놓으면 순수한 옵티마이저 A/B가 된다
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
    layers.Conv2D(32, kernel_size=3, activation="relu"),
    layers.MaxPooling2D(pool_size=2),
    layers.Conv2D(64, kernel_size=3, activation="relu"),
    layers.MaxPooling2D(pool_size=2),
    layers.Flatten(),
    layers.Dropout(0.5),
    layers.Dense(NUM_CLASSES, activation="softmax"),
])
model.summary()

model.compile(
    optimizer=keras.optimizers.SGD(learning_rate=1e-3, momentum=0.9),   # keras1은 "adam"
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

history = model.fit(train_ds, validation_data=val_ds, epochs=15)

test_loss, test_acc = model.evaluate(test_ds)
print(f"Test accuracy: {test_acc:.4f}")


# ============================================================
# 학습 곡선 저장 (PPT 삽입용)
# ============================================================
MODEL_NAME = "Keras CNN (2 Conv)"
OPTIMIZER_NAME = "SGD + momentum 0.9"
SETTINGS = "lr=1e-3  ·  batch=32  ·  epochs=15  ·  no augmentation"
OUTFILE = "curve_keras4.png"

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
print(f"[대조] keras1(Adam) 결과와 나란히 비교할 것")
print(f"[그래프] {OUTFILE}")

try:
    from google.colab import files
    files.download(OUTFILE)
except Exception:
    pass
