# ============================================================
# PyTorch 2 - 3 Conv + BatchNorm + 증강 + EarlyStopping
#
#   이미지        128 x 128 x 3
#   배치          32
#   옵티마이저     Adam (lr=1e-3)
#   epoch         최대 30 (직접 구현한 EarlyStopping, patience=5)
#   증강          RandomHorizontalFlip / RandomRotation(10 = ±10°)
#   BatchNorm     Conv 블록 3개 각각 뒤 (Conv -> ReLU -> BN 순서, Keras와 통일)
#   초기화        PyTorch 기본 (Kaiming/He 계열이라 별도 지정 불필요)
#   Dropout       없음
#   분류 헤드     Flatten -> Linear(128*14*14, 128) -> ReLU -> Linear(128, 11)
# ============================================================

import copy
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import matplotlib.pyplot as plt

DATA_DIR = "/content/food11"
IMG_SIZE = 128
BATCH_SIZE = 32
NUM_CLASSES = 11

train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ToTensor(),
])
eval_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
])

training_data = datasets.ImageFolder(root=f"{DATA_DIR}/training", transform=train_transform)   # train만 증강
val_data = datasets.ImageFolder(root=f"{DATA_DIR}/validation", transform=eval_transform)
test_data = datasets.ImageFolder(root=f"{DATA_DIR}/evaluation", transform=eval_transform)

train_dataloader = DataLoader(training_data, batch_size=BATCH_SIZE, shuffle=True)
val_dataloader = DataLoader(val_data, batch_size=BATCH_SIZE)
test_dataloader = DataLoader(test_data, batch_size=BATCH_SIZE)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using {device} device")


class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool = nn.MaxPool2d(2, 2)
        self.relu = nn.ReLU()
        # 128 -> conv 126 -> pool 63 -> conv 61 -> pool 30 -> conv 28 -> pool 14
        self.fc1 = nn.Linear(128 * 14 * 14, 128)
        self.fc2 = nn.Linear(128, NUM_CLASSES)

    def forward(self, x):
        x = self.pool(self.bn1(self.relu(self.conv1(x))))
        x = self.pool(self.bn2(self.relu(self.conv2(x))))
        x = self.pool(self.bn3(self.relu(self.conv3(x))))
        x = torch.flatten(x, 1)
        x = self.relu(self.fc1(x))
        return self.fc2(x)


model = CNN().to(device)
print(model)

loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)


def train(dataloader, model, loss_fn, optimizer):
    """epoch 단위 평균 loss와 정확도를 반환 (그래프용)"""
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    model.train()
    total_loss, correct = 0, 0
    for batch, (X, y) in enumerate(dataloader):
        X, y = X.to(device), y.to(device)
        pred = model(X)
        loss = loss_fn(pred, y)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

        total_loss += loss.item()
        correct += (pred.argmax(1) == y).type(torch.float).sum().item()

        if batch % 50 == 0:
            loss_val, current = loss.item(), (batch + 1) * len(X)
            print(f"loss: {loss_val:>7f}  [{current:>5d}/{size:>5d}]")
    return total_loss / num_batches, correct / size


def test(dataloader, model, loss_fn):
    """평균 loss와 정확도를 반환"""
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    model.eval()
    test_loss, correct = 0, 0
    with torch.no_grad():
        for X, y in dataloader:
            X, y = X.to(device), y.to(device)
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()
    test_loss /= num_batches
    correct /= size
    print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")
    return test_loss, correct


hist = {"train_acc": [], "train_loss": [], "val_acc": [], "val_loss": []}

best_val_loss = float("inf")
best_state = None
patience, counter = 5, 0

for t in range(30):
    print(f"Epoch {t + 1}\n-------------------------------")
    tr_loss, tr_acc = train(train_dataloader, model, loss_fn, optimizer)
    val_loss, val_acc = test(val_dataloader, model, loss_fn)

    # Keras처럼 epoch 단위 요약을 한 줄로 출력
    print(
        f"[Epoch {t + 1:>2}]  "
        f"accuracy: {tr_acc:.4f} - loss: {tr_loss:.4f}  |  "
        f"val_accuracy: {val_acc:.4f} - val_loss: {val_loss:.4f}\n"
    )

    hist["train_loss"].append(tr_loss)
    hist["train_acc"].append(tr_acc)
    hist["val_loss"].append(val_loss)
    hist["val_acc"].append(val_acc)

    if val_loss < best_val_loss:
        best_val_loss = val_loss
        best_state = copy.deepcopy(model.state_dict())
        counter = 0
    else:
        counter += 1
        if counter >= patience:
            print(f"Early stopping at epoch {t + 1}")
            break

model.load_state_dict(best_state)
print("Final evaluation on held-out test set:")
test_loss, test_acc = test(test_dataloader, model, loss_fn)
print("Done!")


# ============================================================
# 학습 곡선 저장 (PPT 삽입용)
# ============================================================
MODEL_NAME = "PyTorch CNN (3 Conv + BN)"
OPTIMIZER_NAME = "Adam"
SETTINGS = "lr=1e-3  ·  batch=32  ·  augment  ·  EarlyStop p=5"
OUTFILE = "curve_torch2.png"

ACCENT, DARKGY, GRID, TEXT, MUTED = "#16785C", "#3A4353", "#DDD9D2", "#14181F", "#6B7482"

ep = list(range(1, len(hist["train_acc"]) + 1))

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(1, 2, figsize=(10, 3.7), dpi=170)
fig.suptitle(f"{MODEL_NAME}  ·  {OPTIMIZER_NAME}", fontsize=14.5, color=TEXT, y=0.96)
fig.text(0.5, 0.875, SETTINGS, ha="center", fontsize=10, color=MUTED)

panels = [
    (axes[0], hist["train_acc"], hist["val_acc"], "Accuracy"),
    (axes[1], hist["train_loss"], hist["val_loss"], "Loss"),
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
