# import os
# import cv2
# import numpy as np
# import torch
# import torch.nn as nn
# from torch.utils.data import Dataset, DataLoader, random_split

# # ──────────────────────────────────────────────
# # 설정값
# # ──────────────────────────────────────────────
# BASE_DIR      = r"D:\JungPra\pythonpra\signlan"
# VIDEO_DIR     = os.path.join(BASE_DIR, "preprocessed_videos")
# MODEL_SAVE    = os.path.join(BASE_DIR, "sign_model.pth")

# MAX_FRAMES    = 30      # 모든 영상을 이 프레임 수로 통일 (짧으면 패딩, 길면 자름)
# IMG_SIZE      = 224
# BATCH_SIZE    = 8
# EPOCHS        = 20
# LEARNING_RATE = 0.001


# # ──────────────────────────────────────────────
# # Dataset
# # ──────────────────────────────────────────────
# class SignLanguageDataset(Dataset):
#     def __init__(self, video_dir, max_frames=MAX_FRAMES):
#         self.max_frames = max_frames
#         self.classes    = sorted([
#             d for d in os.listdir(video_dir)
#             if os.path.isdir(os.path.join(video_dir, d))
#         ])
#         self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
#         self.data_list    = []

#         for class_name in self.classes:
#             class_path = os.path.join(video_dir, class_name)
#             frames = sorted([
#                 os.path.join(class_path, f)
#                 for f in os.listdir(class_path)
#                 if f.endswith('.jpg')
#             ])
#             if frames:
#                 self.data_list.append((frames, self.class_to_idx[class_name]))

#         print(f"📦 클래스 수: {len(self.classes)}개")
#         print(f"📦 총 샘플 수: {len(self.data_list)}개")
#         print(f"📦 클래스 목록: {self.classes}")

#     def __len__(self):
#         return len(self.data_list)

#     def _load_frame(self, path):
#         with open(path, 'rb') as f:
#             buf = np.frombuffer(f.read(), dtype=np.uint8)
#         img = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)
#         if img is None:
#             img = np.zeros((IMG_SIZE, IMG_SIZE), dtype=np.float32)
#         return img.astype(np.float32) / 255.0  # 0~1 정규화

#     def __getitem__(self, idx):
#         frame_paths, label = self.data_list[idx]

#         # ── 핵심 수정: 프레임 수를 MAX_FRAMES로 통일 ──
#         # 1) 프레임이 MAX_FRAMES보다 많으면 균등 샘플링
#         if len(frame_paths) >= self.max_frames:
#             indices = np.linspace(0, len(frame_paths) - 1, self.max_frames, dtype=int)
#             frame_paths = [frame_paths[i] for i in indices]
        
#         frames = [self._load_frame(p) for p in frame_paths]

#         # 2) 프레임이 MAX_FRAMES보다 적으면 0으로 패딩
#         while len(frames) < self.max_frames:
#             frames.append(np.zeros((IMG_SIZE, IMG_SIZE), dtype=np.float32))

#         # (MAX_FRAMES, H, W) → (MAX_FRAMES, 1, H, W)
#         tensor = torch.tensor(np.stack(frames), dtype=torch.float32).unsqueeze(1)
#         return tensor, torch.tensor(label, dtype=torch.long)


# # ──────────────────────────────────────────────
# # 모델: CNN (공간 특징 추출) + LSTM (시간 순서 학습)
# # ──────────────────────────────────────────────
# class SignLanguageCNNLSTM(nn.Module):
#     def __init__(self, num_classes):
#         super().__init__()

#         # CNN: 각 프레임에서 손 모양 특징 추출
#         self.cnn = nn.Sequential(
#             nn.Conv2d(1, 32, kernel_size=3, padding=1),   # (1,224,224) → (32,224,224)
#             nn.BatchNorm2d(32),
#             nn.ReLU(),
#             nn.MaxPool2d(2),                               # → (32,112,112)

#             nn.Conv2d(32, 64, kernel_size=3, padding=1),  # → (64,112,112)
#             nn.BatchNorm2d(64),
#             nn.ReLU(),
#             nn.MaxPool2d(2),                               # → (64,56,56)

#             nn.Conv2d(64, 128, kernel_size=3, padding=1), # → (128,56,56)
#             nn.BatchNorm2d(128),
#             nn.ReLU(),
#             nn.AdaptiveAvgPool2d((4, 4)),                  # → (128,4,4) = 2048
#         )

#         # LSTM: 프레임 시퀀스에서 동작 흐름 학습
#         self.lstm = nn.LSTM(
#             input_size=128 * 4 * 4,   # CNN 출력 크기
#             hidden_size=256,
#             num_layers=2,
#             batch_first=True,
#             dropout=0.3
#         )

#         # 최종 분류기
#         self.classifier = nn.Sequential(
#             nn.Dropout(0.5),
#             nn.Linear(256, 128),
#             nn.ReLU(),
#             nn.Linear(128, num_classes)
#         )

#     def forward(self, x):
#         # x: (Batch, Seq, 1, H, W)
#         B, S, C, H, W = x.shape

#         # CNN은 프레임 단위로 처리 → 배치+시퀀스 차원 합치기
#         x = x.view(B * S, C, H, W)       # (B*S, 1, H, W)
#         x = self.cnn(x)                   # (B*S, 128, 4, 4)
#         x = x.view(B, S, -1)             # (B, S, 2048)

#         # LSTM으로 시간 흐름 학습
#         x, _ = self.lstm(x)              # (B, S, 256)
#         x = x[:, -1, :]                  # 마지막 타임스텝만 사용 (B, 256)

#         return self.classifier(x)        # (B, num_classes)


# # ──────────────────────────────────────────────
# # 학습 루프
# # ──────────────────────────────────────────────
# def train():
#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     print(f"\n⚙️  학습 장치: {device}")
#     if device.type == "cuda":
#         print(f"   GPU: {torch.cuda.get_device_name(0)}")

#     # 데이터셋 로드
#     dataset = SignLanguageDataset(VIDEO_DIR)
#     num_classes = len(dataset.classes)

#     if len(dataset) == 0:
#         print("❌ 학습 데이터가 없습니다. preprocessed_videos 폴더를 확인하세요.")
#         return

#     # train 80% / val 20% 분리
#     val_size   = max(1, int(len(dataset) * 0.2))
#     train_size = len(dataset) - val_size
#     train_set, val_set = random_split(dataset, [train_size, val_size])

#     train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
#     val_loader   = DataLoader(val_set,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

#     print(f"\n📊 Train: {train_size}개 | Val: {val_size}개")

#     # 모델 / 손실함수 / 옵티마이저
#     model     = SignLanguageCNNLSTM(num_classes).to(device)
#     criterion = nn.CrossEntropyLoss()
#     optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
#     scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.5)

#     best_val_acc = 0.0

#     print(f"\n🚀 학습 시작! (총 {EPOCHS} 에포크)\n{'='*55}")

#     for epoch in range(1, EPOCHS + 1):
#         # ── Train ────────────────────────────────
#         model.train()
#         train_loss = train_correct = train_total = 0

#         for X, y in train_loader:
#             X, y = X.to(device), y.to(device)
#             optimizer.zero_grad()
#             out  = model(X)
#             loss = criterion(out, y)
#             loss.backward()
#             optimizer.step()

#             train_loss    += loss.item()
#             preds          = out.argmax(dim=1)
#             train_correct += (preds == y).sum().item()
#             train_total   += y.size(0)

#         # ── Validation ───────────────────────────
#         model.eval()
#         val_loss = val_correct = val_total = 0

#         with torch.no_grad():
#             for X, y in val_loader:
#                 X, y = X.to(device), y.to(device)
#                 out  = model(X)
#                 loss = criterion(out, y)

#                 val_loss    += loss.item()
#                 preds        = out.argmax(dim=1)
#                 val_correct += (preds == y).sum().item()
#                 val_total   += y.size(0)

#         train_acc = train_correct / train_total * 100
#         val_acc   = val_correct   / val_total   * 100
#         avg_train = train_loss    / len(train_loader)
#         avg_val   = val_loss      / len(val_loader)

#         print(f"Epoch [{epoch:02d}/{EPOCHS}]  "
#               f"Train Loss: {avg_train:.4f}  Acc: {train_acc:.1f}%  │  "
#               f"Val Loss: {avg_val:.4f}  Acc: {val_acc:.1f}%")

#         # 최고 성능 모델 저장
#         if val_acc > best_val_acc:
#             best_val_acc = val_acc
#             torch.save({
#                 "epoch":      epoch,
#                 "model":      model.state_dict(),
#                 "classes":    dataset.classes,
#                 "val_acc":    val_acc,
#             }, MODEL_SAVE)
#             print(f"   💾 모델 저장! (Val Acc: {val_acc:.1f}%)")

#         scheduler.step()

#     print(f"\n🎉 학습 완료! 최고 Val Acc: {best_val_acc:.1f}%")
#     print(f"💾 모델 저장 위치: {MODEL_SAVE}")


# if __name__ == "__main__":
#     train()


import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split

# ──────────────────────────────────────────────
# 설정값
# ──────────────────────────────────────────────
BASE_DIR      = r"D:\JungPra\pythonpra\signlan"
VIDEO_DIR     = os.path.join(BASE_DIR, "preprocessed_videos")
MODEL_SAVE    = os.path.join(BASE_DIR, "sign_model.pth")

MAX_FRAMES    = 30
IMG_SIZE      = 224
BATCH_SIZE    = 4       # 데이터 적으니 배치 작게
EPOCHS        = 150     # 데이터 적으니 에포크 많이
LEARNING_RATE = 0.0005  # 학습률 낮춰서 안정적으로


# ──────────────────────────────────────────────
# Data Augmentation (같은 데이터를 변형해서 불리기)
# ──────────────────────────────────────────────
def augment_frame(img: np.ndarray) -> np.ndarray:
    """프레임 1장에 랜덤 변형을 적용합니다."""

    # 1. 50% 확률로 좌우 반전
    if np.random.rand() < 0.5:
        img = np.fliplr(img)

    # 2. 밝기 랜덤 조절 (±20%)
    brightness = np.random.uniform(0.8, 1.2)
    img = np.clip(img * brightness, 0.0, 1.0)

    # 3. 랜덤 회전 (-15° ~ +15°)
    angle = np.random.uniform(-15, 15)
    h, w  = img.shape
    M     = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    img   = cv2.warpAffine(img, M, (w, h))

    # 4. 랜덤 줌 (약간 확대 후 크롭)
    scale = np.random.uniform(0.9, 1.1)
    new_h, new_w = int(h * scale), int(w * scale)
    resized = cv2.resize(img, (new_w, new_h))
    # 중앙 크롭해서 원래 크기로
    start_y = max(0, (new_h - h) // 2)
    start_x = max(0, (new_w - w) // 2)
    cropped = resized[start_y:start_y + h, start_x:start_x + w]
    img = cv2.resize(cropped, (w, h))  # 혹시 크기 안 맞으면 보정

    return img.astype(np.float32)


# ──────────────────────────────────────────────
# Dataset
# ──────────────────────────────────────────────
class SignLanguageDataset(Dataset):
    def __init__(self, video_dir, max_frames=MAX_FRAMES, augment=False):
        self.max_frames = max_frames
        self.augment    = augment
        self.classes    = sorted([
            d for d in os.listdir(video_dir)
            if os.path.isdir(os.path.join(video_dir, d))
        ])
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.data_list    = []

        for class_name in self.classes:
            class_path = os.path.join(video_dir, class_name)
            frames = sorted([
                os.path.join(class_path, f)
                for f in os.listdir(class_path)
                if f.endswith('.jpg')
            ])
            if frames:
                self.data_list.append((frames, self.class_to_idx[class_name]))

        print(f"📦 클래스 수: {len(self.classes)}개")
        print(f"📦 샘플 수: {len(self.data_list)}개")
        print(f"📦 Augmentation: {'ON' if augment else 'OFF'}")

    def __len__(self):
        return len(self.data_list)

    def _load_frame(self, path):
        with open(path, 'rb') as f:
            buf = np.frombuffer(f.read(), dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return np.zeros((IMG_SIZE, IMG_SIZE), dtype=np.float32)
        return img.astype(np.float32) / 255.0

    def __getitem__(self, idx):
        frame_paths, label = self.data_list[idx]

        # 프레임 수 통일 (균등 샘플링 or 패딩)
        if len(frame_paths) >= self.max_frames:
            indices     = np.linspace(0, len(frame_paths) - 1, self.max_frames, dtype=int)
            frame_paths = [frame_paths[i] for i in indices]

        frames = [self._load_frame(p) for p in frame_paths]

        while len(frames) < self.max_frames:
            frames.append(np.zeros((IMG_SIZE, IMG_SIZE), dtype=np.float32))

        # Augmentation은 Train에서만 적용
        if self.augment:
            frames = [augment_frame(f) for f in frames]

        tensor = torch.tensor(np.stack(frames), dtype=torch.float32).unsqueeze(1)
        return tensor, torch.tensor(label, dtype=torch.long)


# ──────────────────────────────────────────────
# 모델: CNN + LSTM
# ──────────────────────────────────────────────
class SignLanguageCNNLSTM(nn.Module):
    def __init__(self, num_classes):
        super().__init__()

        self.cnn = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4)),
        )

        self.lstm = nn.LSTM(
            input_size=128 * 4 * 4,
            hidden_size=256,
            num_layers=2,
            batch_first=True,
            dropout=0.3
        )

        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        B, S, C, H, W = x.shape
        x = x.view(B * S, C, H, W)
        x = self.cnn(x)
        x = x.view(B, S, -1)
        x, _ = self.lstm(x)
        x = x[:, -1, :]
        return self.classifier(x)


# ──────────────────────────────────────────────
# 학습
# ──────────────────────────────────────────────
def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n⚙️  학습 장치: {device}")
    if device.type == "cuda":
        print(f"   GPU: {torch.cuda.get_device_name(0)}")

    # 데이터 적으면 val 분리 없이 전체로 학습
    full_dataset = SignLanguageDataset(VIDEO_DIR, augment=False)
    num_classes  = len(full_dataset.classes)

    if len(full_dataset) == 0:
        print("❌ 데이터가 없습니다.")
        return

    # 샘플이 5개 이하면 val 분리 안 함 (데이터가 너무 적음)
    if len(full_dataset) <= 5:
        print("⚠️  샘플이 너무 적어 validation 없이 전체 데이터로 학습합니다.")
        train_dataset = SignLanguageDataset(VIDEO_DIR, augment=True)
        val_dataset   = SignLanguageDataset(VIDEO_DIR, augment=False)  # 동일 데이터로 확인만
        use_val       = False
    else:
        val_size      = max(1, int(len(full_dataset) * 0.2))
        train_size    = len(full_dataset) - val_size
        # augment=True는 train만
        train_dataset = SignLanguageDataset(VIDEO_DIR, augment=True)
        val_dataset   = SignLanguageDataset(VIDEO_DIR, augment=False)
        # 인덱스 분리
        indices       = torch.randperm(len(full_dataset)).tolist()
        train_indices = indices[:train_size]
        val_indices   = indices[train_size:]
        from torch.utils.data import Subset
        train_dataset = Subset(train_dataset, train_indices)
        val_dataset   = Subset(val_dataset,   val_indices)
        use_val       = True
        print(f"📊 Train: {train_size}개 | Val: {val_size}개")

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
    val_loader   = DataLoader(val_dataset,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model     = SignLanguageCNNLSTM(num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    best_acc     = 0.0
    no_improve   = 0
    EARLY_STOP   = 30   # 30 에포크 동안 개선 없으면 조기 종료

    print(f"\n🚀 학습 시작! ({EPOCHS} 에포크)\n{'='*60}")

    for epoch in range(1, EPOCHS + 1):
        # ── Train ──
        model.train()
        train_loss = train_correct = train_total = 0

        for X, y in train_loader:
            X, y = X.to(device), y.to(device)
            optimizer.zero_grad()
            out  = model(X)
            loss = criterion(out, y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)  # 그래디언트 폭발 방지
            optimizer.step()

            train_loss    += loss.item()
            train_correct += (out.argmax(1) == y).sum().item()
            train_total   += y.size(0)

        # ── Val ──
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
              f"Train Acc: {train_acc:.1f}%  │  "
              f"Val Acc: {val_acc:.1f}%")

        # 최고 모델 저장
        if val_acc > best_acc:
            best_acc   = val_acc
            no_improve = 0
            torch.save({
                "epoch":   epoch,
                "model":   model.state_dict(),
                "classes": full_dataset.classes,
                "val_acc": val_acc,
            }, MODEL_SAVE)
            print(f"   💾 모델 저장! (Val Acc: {val_acc:.1f}%)")
        else:
            no_improve += 1

        # 조기 종료
        if no_improve >= EARLY_STOP:
            print(f"\n⏹️  {EARLY_STOP} 에포크 동안 개선 없음 → 조기 종료")
            break

        scheduler.step()

    print(f"\n🎉 학습 완료! 최고 Val Acc: {best_acc:.1f}%")
    print(f"💾 저장 위치: {MODEL_SAVE}")


if __name__ == "__main__":
    train()