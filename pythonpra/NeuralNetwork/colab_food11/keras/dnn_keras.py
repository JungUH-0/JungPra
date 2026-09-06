# Google Colab 실행용: Food-11 데이터셋 (Google Drive 업로드 상태)
from google.colab import drive
drive.mount('/content/drive')

import os
import keras
from keras import layers

DATA_DIR = "/content/drive/MyDrive/food11"
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
    layers.Flatten(),
    layers.Dense(256, activation="relu"),
    layers.Dense(128, activation="relu"),
    layers.Dense(NUM_CLASSES, activation="softmax"),
])
model.summary()

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

model.fit(train_ds, validation_data=val_ds, epochs=5)

test_loss, test_acc = model.evaluate(test_ds)
print(f"Test accuracy: {test_acc:.4f}")
