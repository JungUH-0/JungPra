import os
import re
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, Subset

# ──────────────────────────────────────────────
# 설정값 ai허브 학습
# ──────────────────────────────────────────────
BASE_DIR      = r"D:\JungPra\pythonpra\signlan"
VIDEO_DIR     = os.path.join(BASE_DIR, "npy_output")
MODEL_SAVE    = os.path.join(BASE_DIR, "aihub_model.pth")

MAX_FRAMES    = 30
LANDMARK_DIM  = 84

BATCH_SIZE    = 32
EPOCHS        = 300
LEARNING_RATE = 0.001
RANDOM_SEED   = 42
EARLY_STOP    = 50
RESUME        = False

# ── 학습할 단어 목록 (23개) ──────────────────
TARGET_WORDS = [
    '감사', '좋다', '싫다', '가다', '오다',
    '듣다', '슬프다', '행복', '친구', '밥',
    '사람', '엄마', '형', '맞다', '빠르다',
    '느리다', '병원', '화나다', '웃다', '걷다',
    '자다', '일어나다', '서다'
]


# ──────────────────────────────────────────────
# Dataset
# ──────────────────────────────────────────────
class SignLanguageDataset(Dataset):
    def __init__(self, video_dir, augment=False):
        self.augment   = augment
        self.data_list = []
        self.classes   = sorted(TARGET_WORDS)
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}

        npy_files = sorted([f for f in os.listdir(video_dir) if f.endswith('.npy')])

        if not npy_files:
            print("❌ npy_output 폴더에 .npy 파일이 없습니다.")
            return

        skipped = 0
        for fname in npy_files:
            name = os.path.splitext(fname)[0]
            m    = re.match(r'^(.+)_\d+_[UDLRF]$', name)
            word = m.group(1) if m else name

            # TARGET_WORDS에 없으면 스킵
            if word not in self.class_to_idx:
                skipped += 1
                continue

            seq = np.load(os.path.join(video_dir, fname))
            self.data_list.append((seq, self.class_to_idx[word]))

        print(f"📦 클래스 수: {len(self.classes)}개")
        print(f"📦 샘플 수:   {len(self.data_list)}개")
        print(f"📦 스킵:      {skipped}개")
        print(f"📦 클래스당 평균 샘플: {len(self.data_list)/len(self.classes):.1f}개")
        print(f"📦 Augmentation: {'ON' if augment else 'OFF'}")

    def __len__(self):
        return len(self.data_list)

    def _augment(self, seq):
        seq = seq + np.random.normal(0, 0.02, seq.shape).astype(np.float32)
        seq = seq * np.random.uniform(0.9, 1.1)
        if np.random.rand() < 0.5:
            seq = seq.copy()
            for i in range(0, seq.shape[1], 2):
                seq[:, i] = 1.0 - seq[:, i]
        return np.clip(seq, 0.0, 1.0)

    def __getitem__(self, idx):
        seq, label = self.data_list[idx]
        seq = seq.copy()
        if self.augment:
            seq = self._augment(seq)
        return torch.tensor(seq, dtype=torch.float32), torch.tensor(label, dtype=torch.long)


# ──────────────────────────────────────────────
# 모델
# ──────────────────────────────────────────────
class SignLanguageLSTM(nn.Module):
    def __init__(self, num_classes, input_dim=LANDMARK_DIM):
        super().__init__()
        self.input_norm = nn.LayerNorm(input_dim)
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=256,
            num_layers=3,
            batch_first=True,
            dropout=0.3,
            bidirectional=True,
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(256 * 2, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        x, _ = self.lstm(self.input_norm(x))
        x    = x[:, -1, :]
        return self.classifier(x)


# ──────────────────────────────────────────────
# 학습
# ──────────────────────────────────────────────
def train():
    torch.manual_seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n⚙️  학습 장치: {device}")
    if device.type == "cuda":
        print(f"   GPU: {torch.cuda.get_device_name(0)}")

    full_dataset = SignLanguageDataset(VIDEO_DIR, augment=False)
    num_classes  = len(full_dataset.classes)

    if len(full_dataset) == 0:
        return

    generator  = torch.Generator().manual_seed(RANDOM_SEED)
    indices    = torch.randperm(len(full_dataset), generator=generator).tolist()
    val_size   = max(1, int(len(full_dataset) * 0.2))
    train_size = len(full_dataset) - val_size

    train_dataset = SignLanguageDataset(VIDEO_DIR, augment=True)
    val_dataset   = Subset(SignLanguageDataset(VIDEO_DIR, augment=False), indices[train_size:])

    print(f"📊 Train: {len(train_dataset)}개 | Val: {val_size}개\n")

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,  num_workers=4, pin_memory=True)
    val_loader   = DataLoader(val_dataset,   batch_size=BATCH_SIZE, shuffle=False, num_workers=4, pin_memory=True)

    model     = SignLanguageLSTM(num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    start_epoch = 1
    best_acc    = 0.0
    no_improve  = 0

    if RESUME and os.path.exists(MODEL_SAVE):
        print(f"🔄 저장된 모델 발견! 이어서 학습...")
        ckpt = torch.load(MODEL_SAVE, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model"])
        best_acc    = ckpt.get("val_acc", 0.0)
        start_epoch = ckpt.get("epoch", 0) + 1
        if "optimizer" in ckpt: optimizer.load_state_dict(ckpt["optimizer"])
        if "scheduler" in ckpt: scheduler.load_state_dict(ckpt["scheduler"])
        print(f"   ✅ {ckpt.get('epoch')}에포크부터 | 최고 Val Acc: {best_acc:.1f}%\n")
    else:
        print(f"🆕 처음부터 학습 시작\n")

    print(f"🚀 학습 시작! ({start_epoch} ~ {EPOCHS} 에포크)\n{'='*60}")

    for epoch in range(start_epoch, EPOCHS + 1):
        model.train()
        train_loss = train_correct = train_total = 0

        for X, y in train_loader:
            X, y = X.to(device), y.to(device)
            optimizer.zero_grad()
            out  = model(X)
            loss = criterion(out, y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            train_loss    += loss.item()
            train_correct += (out.argmax(1) == y).sum().item()
            train_total   += y.size(0)

        model.eval()
        val_correct = val_total = 0
        with torch.no_grad():
            for X, y in val_loader:
                X, y = X.to(device), y.to(device)
                out  = model(X)
                val_correct += (out.argmax(1) == y).sum().item()
                val_total   += y.size(0)

        train_acc = train_correct / train_total * 100
        val_acc   = val_correct   / val_total   * 100
        avg_loss  = train_loss    / len(train_loader)

        print(f"Epoch [{epoch:03d}/{EPOCHS}]  "
              f"Loss: {avg_loss:.4f}  "
              f"Train: {train_acc:.1f}%  │  "
              f"Val: {val_acc:.1f}%")

        if val_acc > best_acc:
            best_acc   = val_acc
            no_improve = 0
            torch.save({
                "epoch":     epoch,
                "model":     model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "scheduler": scheduler.state_dict(),
                "classes":   full_dataset.classes,
                "val_acc":   val_acc,
            }, MODEL_SAVE)
            print(f"   💾 모델 저장! (Val Acc: {val_acc:.1f}%)")
        else:
            no_improve += 1

        if no_improve >= EARLY_STOP:
            print(f"\n⏹️  {EARLY_STOP} 에포크 개선 없음 → 조기 종료")
            break

        scheduler.step()

    print(f"\n🎉 학습 완료! 최고 Val Acc: {best_acc:.1f}%")
    print(f"💾 저장 위치: {MODEL_SAVE}")


if __name__ == "__main__":
    train()