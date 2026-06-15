# import os
# import re
# import cv2
# import numpy as np
# import torch
# import torch.nn as nn
# from torch.utils.data import Dataset, DataLoader, Subset
# from PIL import ImageFont, ImageDraw, Image

# # ──────────────────────────────────────────────
# # 설정값
# # ──────────────────────────────────────────────
# BASE_DIR      = r"D:\JungPra\pythonpra\signlan"
# VIDEO_DIR     = os.path.join(BASE_DIR, "mynum_preprocessed")
# MP4_DIR       = os.path.join(BASE_DIR, "mynum")
# MODEL_SAVE    = os.path.join(BASE_DIR, "mynum_model.pth")

# MAX_FRAMES    = 30
# LANDMARK_DIM  = 126

# BATCH_SIZE    = 4
# EPOCHS        = 300
# LEARNING_RATE = 0.001
# RANDOM_SEED   = 42
# EARLY_STOP    = 50
# RESUME        = False

# TARGET_WORDS  = ['1', '2', '3', '4', '5']

# FONT_PATHS = [
#     r"C:\Windows\Fonts\malgun.ttf",
#     r"C:\Windows\Fonts\gulim.ttc",
# ]


# # ──────────────────────────────────────────────
# # 한글 폰트
# # ──────────────────────────────────────────────
# def load_font(size):
#     for path in FONT_PATHS:
#         if os.path.exists(path):
#             return ImageFont.truetype(path, size)
#     return ImageFont.load_default()

# FONT_LARGE  = load_font(55)
# FONT_MEDIUM = load_font(32)
# FONT_SMALL  = load_font(22)

# def draw_korean(frame, text, pos, font, color=(255,255,255), shadow=True):
#     img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
#     draw    = ImageDraw.Draw(img_pil)
#     x, y   = pos
#     if shadow:
#         draw.text((x+2, y+2), text, font=font, fill=(0,0,0))
#     draw.text((x, y), text, font=font, fill=(color[2], color[1], color[0]))
#     return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


# # ──────────────────────────────────────────────
# # Dataset
# # ──────────────────────────────────────────────
# class SignLanguageDataset(Dataset):
#     def __init__(self, video_dir, augment=False):
#         self.augment      = augment
#         self.data_list    = []
#         self.classes      = sorted(TARGET_WORDS)
#         self.class_to_idx = {c: i for i, c in enumerate(self.classes)}

#         npy_files = sorted([f for f in os.listdir(video_dir) if f.endswith('.npy')])

#         if not npy_files:
#             print("❌ mynum_preprocessed 폴더에 .npy 파일이 없습니다.")
#             return

#         skipped = 0
#         for fname in npy_files:
#             name = os.path.splitext(fname)[0]
#             m    = re.match(r'^(.+)_\d+$', name)
#             word = m.group(1) if m else name

#             if word not in self.class_to_idx:
#                 skipped += 1
#                 continue

#             seq = np.load(os.path.join(video_dir, fname))
#             # mp4 경로도 같이 저장
#             mp4_path = os.path.join(MP4_DIR, fname.replace('.npy', '.mp4'))
#             self.data_list.append((seq, self.class_to_idx[word], word, mp4_path))

#         print(f"📦 클래스 수: {len(self.classes)}개 {self.classes}")
#         print(f"📦 샘플 수:   {len(self.data_list)}개")
#         print(f"📦 Augmentation: {'ON' if augment else 'OFF'}")

#     def __len__(self):
#         return len(self.data_list)

#     def _augment(self, seq):
#         seq = seq + np.random.normal(0, 0.02, seq.shape).astype(np.float32)
#         seq = seq * np.random.uniform(0.9, 1.1)
#         if np.random.rand() < 0.5:
#             seq = seq.copy()
#             for i in range(0, seq.shape[1], 3):
#                 seq[:, i] = 1.0 - seq[:, i]
#         return np.clip(seq, 0.0, 1.0)

#     def __getitem__(self, idx):
#         seq, label, word, mp4_path = self.data_list[idx]
#         seq = seq.copy()
#         if self.augment:
#             seq = self._augment(seq)
#         return torch.tensor(seq, dtype=torch.float32), torch.tensor(label, dtype=torch.long), word, mp4_path


# # ──────────────────────────────────────────────
# # 모델
# # ──────────────────────────────────────────────
# class SignLanguageLSTM(nn.Module):
#     def __init__(self, num_classes, input_dim=LANDMARK_DIM):
#         super().__init__()
#         self.input_norm = nn.LayerNorm(input_dim)
#         self.lstm = nn.LSTM(
#             input_size=input_dim,
#             hidden_size=256,
#             num_layers=3,
#             batch_first=True,
#             dropout=0.3,
#             bidirectional=True,
#         )
#         self.classifier = nn.Sequential(
#             nn.Dropout(0.5),
#             nn.Linear(256 * 2, 256),
#             nn.ReLU(),
#             nn.Dropout(0.3),
#             nn.Linear(256, num_classes),
#         )

#     def forward(self, x):
#         x, _ = self.lstm(self.input_norm(x))
#         mid = x.size(1)
#         x    = x[:, mid/2, :]
#         return self.classifier(x)


# # ──────────────────────────────────────────────
# # 시각화 창
# # ──────────────────────────────────────────────
# class TrainVisualizer:
#     def __init__(self, classes):
#         self.classes     = classes
#         self.win_name    = "Training Visualizer  |  Q: 종료"
#         self.loss_history = []
#         self.train_history = []
#         self.val_history   = []
#         self.batch_results = []  # [(정답, 예측, 정오), ...]
#         self.current_frame = None
#         self.epoch    = 0
#         self.epochs   = 0
#         self.canvas_w = 1280
#         self.canvas_h = 720

#     def update_batch(self, mp4_paths, true_words, pred_words):
#         """배치마다 첫 번째 샘플의 영상 + 예측 결과 업데이트"""
#         self.batch_results = list(zip(true_words, pred_words))

#         # 첫 번째 샘플 mp4에서 중간 프레임 추출
#         mp4_path = mp4_paths[0]
#         if os.path.exists(mp4_path):
#             cap = cv2.VideoCapture(mp4_path)
#             total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#             cap.set(cv2.CAP_PROP_POS_FRAMES, total // 2)
#             ret, frame = cap.read()
#             cap.release()
#             if ret:
#                 self.current_frame = cv2.resize(frame, (480, 360))

#     def update_epoch(self, epoch, epochs, loss, train_acc, val_acc):
#         self.epoch = epoch
#         self.epochs = epochs
#         self.loss_history.append(loss)
#         self.train_history.append(train_acc)
#         self.val_history.append(val_acc)

#     def draw(self):
#         canvas = np.zeros((self.canvas_h, self.canvas_w, 3), dtype=np.uint8)
#         canvas[:] = (30, 30, 30)

#         # ── 상단 타이틀 ──────────────────────────
#         canvas = draw_korean(canvas, f"SignBridge 학습 시각화",
#                              (10, 8), FONT_MEDIUM, (255, 200, 0))
#         canvas = draw_korean(canvas,
#                              f"Epoch [{self.epoch:03d}/{self.epochs}]",
#                              (500, 8), FONT_MEDIUM, (200, 200, 200))

#         # ── 왼쪽: 현재 학습 영상 ─────────────────
#         if self.current_frame is not None:
#             canvas[55:415, 10:490] = self.current_frame
#         else:
#             cv2.rectangle(canvas, (10, 55), (490, 415), (60,60,60), -1)
#             canvas = draw_korean(canvas, "영상 없음", (180, 210), FONT_MEDIUM, (100,100,100))

#         canvas = draw_korean(canvas, "현재 학습 샘플", (10, 420), FONT_SMALL, (150,150,150), shadow=False)

#         # ── 왼쪽 하단: 배치 예측 결과 ────────────
#         canvas = draw_korean(canvas, "배치 예측 결과:", (10, 450), FONT_SMALL, (200,200,200), shadow=False)
#         for i, (true, pred) in enumerate(self.batch_results[:6]):
#             correct = true == pred
#             color   = (0, 255, 100) if correct else (0, 80, 255)
#             mark    = "✓" if correct else "✗"
#             canvas  = draw_korean(canvas,
#                                   f"  {mark} 정답: {true}  예측: {pred}",
#                                   (10, 478 + i * 34), FONT_SMALL, color, shadow=False)

#         # ── 오른쪽: 그래프 ───────────────────────
#         gx, gy, gw, gh = 510, 55, 760, 300  # 그래프 영역

#         cv2.rectangle(canvas, (gx, gy), (gx+gw, gy+gh), (50,50,50), -1)
#         cv2.rectangle(canvas, (gx, gy), (gx+gw, gy+gh), (80,80,80), 1)

#         canvas = draw_korean(canvas, "Loss / Accuracy 그래프",
#                              (gx+5, gy-28), FONT_SMALL, (200,200,200), shadow=False)

#         def draw_curve(history, color, max_val=100.0):
#             if len(history) < 2:
#                 return
#             pts = []
#             for i, v in enumerate(history):
#                 x = gx + int(i / max(len(history)-1, 1) * (gw-20)) + 10
#                 y = gy + gh - int(v / max_val * (gh-20)) - 10
#                 pts.append((x, y))
#             for i in range(len(pts)-1):
#                 cv2.line(canvas, pts[i], pts[i+1], color, 2, cv2.LINE_AA)
#             cv2.circle(canvas, pts[-1], 4, color, -1)

#         # Loss (최대값 기준 정규화)
#         if self.loss_history:
#             max_loss = max(self.loss_history) or 1.0
#             normalized = [v / max_loss * 100 for v in self.loss_history]
#             draw_curve(normalized, (0, 100, 255))   # 파란색

#         draw_curve(self.train_history, (0, 200, 100))   # 초록색
#         draw_curve(self.val_history,   (0, 200, 255))   # 하늘색

#         # 범례
#         legend_y = gy + gh + 10
#         cv2.rectangle(canvas, (gx, legend_y), (gx+15, legend_y+12), (0,100,255), -1)
#         canvas = draw_korean(canvas, "Loss", (gx+20, legend_y-5), FONT_SMALL, (0,100,255), shadow=False)
#         cv2.rectangle(canvas, (gx+80, legend_y), (gx+95, legend_y+12), (0,200,100), -1)
#         canvas = draw_korean(canvas, "Train Acc", (gx+100, legend_y-5), FONT_SMALL, (0,200,100), shadow=False)
#         cv2.rectangle(canvas, (gx+200, legend_y), (gx+215, legend_y+12), (0,200,255), -1)
#         canvas = draw_korean(canvas, "Val Acc", (gx+220, legend_y-5), FONT_SMALL, (0,200,255), shadow=False)

#         # ── 오른쪽 하단: 현재 수치 ───────────────
#         if self.loss_history:
#             info_y = gy + gh + 50
#             last_loss  = self.loss_history[-1]
#             last_train = self.train_history[-1] if self.train_history else 0
#             last_val   = self.val_history[-1]   if self.val_history   else 0
#             best_val   = max(self.val_history)   if self.val_history   else 0

#             canvas = draw_korean(canvas, f"Loss: {last_loss:.4f}",
#                                  (gx, info_y), FONT_MEDIUM, (0,100,255))
#             canvas = draw_korean(canvas, f"Train: {last_train:.1f}%",
#                                  (gx+200, info_y), FONT_MEDIUM, (0,200,100))
#             canvas = draw_korean(canvas, f"Val: {last_val:.1f}%",
#                                  (gx+420, info_y), FONT_MEDIUM, (0,200,255))
#             canvas = draw_korean(canvas, f"최고 Val: {best_val:.1f}%",
#                                  (gx+600, info_y), FONT_MEDIUM, (255,200,0))

#         cv2.imshow(self.win_name, canvas)
#         key = cv2.waitKey(1) & 0xFF
#         if key == ord('q'):
#             return False
#         return True

#     def close(self):
#         cv2.destroyAllWindows()


# # ──────────────────────────────────────────────
# # 학습
# # ──────────────────────────────────────────────
# def train():
#     torch.manual_seed(RANDOM_SEED)
#     np.random.seed(RANDOM_SEED)

#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     print(f"\n⚙️  학습 장치: {device}")
#     if device.type == "cuda":
#         print(f"   GPU: {torch.cuda.get_device_name(0)}")

#     full_dataset = SignLanguageDataset(VIDEO_DIR, augment=False)
#     num_classes  = len(full_dataset.classes)

#     if len(full_dataset) == 0:
#         return

#     generator  = torch.Generator().manual_seed(RANDOM_SEED)
#     indices    = torch.randperm(len(full_dataset), generator=generator).tolist()
#     val_size   = max(1, int(len(full_dataset) * 0.2))
#     train_size = len(full_dataset) - val_size

#     train_dataset = SignLanguageDataset(VIDEO_DIR, augment=True)
#     val_dataset   = Subset(SignLanguageDataset(VIDEO_DIR, augment=False), indices[train_size:])

#     print(f"📊 Train: {len(train_dataset)}개 | Val: {val_size}개\n")

#     train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
#     val_loader   = DataLoader(val_dataset,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

#     model     = SignLanguageLSTM(num_classes).to(device)
#     criterion = nn.CrossEntropyLoss()
#     optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
#     scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

#     viz       = TrainVisualizer(full_dataset.classes)

#     start_epoch = 1
#     best_acc    = 0.0
#     no_improve  = 0

#     if RESUME and os.path.exists(MODEL_SAVE):
#         print(f"🔄 저장된 모델 발견! 이어서 학습...")
#         ckpt = torch.load(MODEL_SAVE, map_location=device, weights_only=False)
#         model.load_state_dict(ckpt["model"])
#         best_acc    = ckpt.get("val_acc", 0.0)
#         start_epoch = ckpt.get("epoch", 0) + 1
#         if "optimizer" in ckpt: optimizer.load_state_dict(ckpt["optimizer"])
#         if "scheduler" in ckpt: scheduler.load_state_dict(ckpt["scheduler"])
#         print(f"   ✅ {ckpt.get('epoch')}에포크부터 | 최고 Val Acc: {best_acc:.1f}%\n")
#     else:
#         print(f"🆕 처음부터 학습 시작\n")

#     print(f"🚀 학습 시작! ({start_epoch} ~ {EPOCHS} 에포크)\n{'='*60}")

#     for epoch in range(start_epoch, EPOCHS + 1):
#         model.train()
#         train_loss = train_correct = train_total = 0

#         for X, y, true_words, mp4_paths in train_loader:
#             X, y = X.to(device), y.to(device)
#             optimizer.zero_grad()
#             out  = model(X)
#             loss = criterion(out, y)
#             loss.backward()
#             nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
#             optimizer.step()

#             train_loss    += loss.item()
#             train_correct += (out.argmax(1) == y).sum().item()
#             train_total   += y.size(0)

#             # 배치 예측 결과 시각화
#             pred_idxs  = out.argmax(1).cpu().tolist()
#             pred_words = [full_dataset.classes[i] for i in pred_idxs]
#             viz.update_batch(mp4_paths, list(true_words), pred_words)
#             if not viz.draw():
#                 viz.close()
#                 return

#         model.eval()
#         val_correct = val_total = 0
#         with torch.no_grad():
#             for X, y, _, __ in val_loader:
#                 X, y = X.to(device), y.to(device)
#                 out  = model(X)
#                 val_correct += (out.argmax(1) == y).sum().item()
#                 val_total   += y.size(0)

#         train_acc = train_correct / train_total * 100
#         val_acc   = val_correct   / val_total   * 100
#         avg_loss  = train_loss    / len(train_loader)

#         viz.update_epoch(epoch, EPOCHS, avg_loss, train_acc, val_acc)
#         viz.draw()

#         print(f"Epoch [{epoch:03d}/{EPOCHS}]  "
#               f"Loss: {avg_loss:.4f}  "
#               f"Train: {train_acc:.1f}%  │  "
#               f"Val: {val_acc:.1f}%")

#         if val_acc > best_acc:
#             best_acc   = val_acc
#             no_improve = 0
#             torch.save({
#                 "epoch":     epoch,
#                 "model":     model.state_dict(),
#                 "optimizer": optimizer.state_dict(),
#                 "scheduler": scheduler.state_dict(),
#                 "classes":   full_dataset.classes,
#                 "val_acc":   val_acc,
#             }, MODEL_SAVE)
#             print(f"   💾 모델 저장! (Val Acc: {val_acc:.1f}%)")
#         else:
#             no_improve += 1

#         if no_improve >= EARLY_STOP:
#             print(f"\n⏹️  {EARLY_STOP} 에포크 개선 없음 → 조기 종료")
#             break

#         scheduler.step()

#     viz.close()
#     print(f"\n🎉 학습 완료! 최고 Val Acc: {best_acc:.1f}%")
#     print(f"💾 저장 위치: {MODEL_SAVE}")


# if __name__ == "__main__":
#     train()

import os
import re
import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, Subset
from PIL import ImageFont, ImageDraw, Image

# ──────────────────────────────────────────────
# 설정값 현재 만든 app에 맞게 모델 변경
# ──────────────────────────────────────────────
BASE_DIR      = r"D:\JungPra\pythonpra\signlan"
VIDEO_DIR     = os.path.join(BASE_DIR, "mynum_preprocessed")
MP4_DIR       = os.path.join(BASE_DIR, "mynum")
MODEL_SAVE    = os.path.join(BASE_DIR, "number_model_signbridge.pth")

MAX_FRAMES    = 30
FEATURE_DIM   = 42   # SignBridge 형식: x,y × 21관절

BATCH_SIZE    = 4
EPOCHS        = 300
LEARNING_RATE = 0.001
RANDOM_SEED   = 42
EARLY_STOP    = 50
RESUME        = False

TARGET_WORDS  = ['1', '2', '3', '4', '5']

FONT_PATHS = [
    r"C:\Windows\Fonts\malgun.ttf",
    r"C:\Windows\Fonts\gulim.ttc",
]


# ──────────────────────────────────────────────
# 한글 폰트
# ──────────────────────────────────────────────
def load_font(size):
    for path in FONT_PATHS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

FONT_LARGE  = load_font(55)
FONT_MEDIUM = load_font(32)
FONT_SMALL  = load_font(22)

def draw_korean(frame, text, pos, font, color=(255,255,255), shadow=True):
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw    = ImageDraw.Draw(img_pil)
    x, y   = pos
    if shadow:
        draw.text((x+2, y+2), text, font=font, fill=(0,0,0))
    draw.text((x, y), text, font=font, fill=(color[2], color[1], color[0]))
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


# ──────────────────────────────────────────────
# Dataset
# ──────────────────────────────────────────────
class SignLanguageDataset(Dataset):
    def __init__(self, video_dir, augment=False):
        self.augment      = augment
        self.data_list    = []
        self.classes      = sorted(TARGET_WORDS)
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}

        npy_files = sorted([f for f in os.listdir(video_dir) if f.endswith('.npy')])

        if not npy_files:
            print("❌ mynum_preprocessed 폴더에 .npy 파일이 없습니다.")
            return

        skipped = 0
        for fname in npy_files:
            name = os.path.splitext(fname)[0]
            m    = re.match(r'^(.+)_\d+$', name)
            word = m.group(1) if m else name

            if word not in self.class_to_idx:
                skipped += 1
                continue

            seq      = np.load(os.path.join(video_dir, fname))
            mp4_path = os.path.join(MP4_DIR, fname.replace('.npy', '.mp4'))
            self.data_list.append((seq, self.class_to_idx[word], word, mp4_path))

        print(f"📦 클래스 수: {len(self.classes)}개 {self.classes}")
        print(f"📦 샘플 수:   {len(self.data_list)}개")
        print(f"📦 스킵:      {skipped}개")
        print(f"📦 Augmentation: {'ON' if augment else 'OFF'}")

    def __len__(self):
        return len(self.data_list)

    def _augment(self, seq):
        seq = seq + np.random.normal(0, 0.02, seq.shape).astype(np.float32)
        seq = seq * np.random.uniform(0.9, 1.1)
        if np.random.rand() < 0.5:
            seq = seq.copy()
            for i in range(0, seq.shape[1], 2):  # x,y라 2씩
                seq[:, i] = 1.0 - seq[:, i]
        return np.clip(seq, 0.0, 1.0)

    def __getitem__(self, idx):
        seq, label, word, mp4_path = self.data_list[idx]
        seq = seq.copy()
        if self.augment:
            seq = self._augment(seq)
        return torch.tensor(seq, dtype=torch.float32), torch.tensor(label, dtype=torch.long), word, mp4_path


# ──────────────────────────────────────────────
# 모델 (SignBridge SignLSTM 구조)
# ──────────────────────────────────────────────
class SignLSTM(nn.Module):
    def __init__(self, input_dim, num_classes):
        super().__init__()
        self.lstm1 = nn.LSTM(input_dim, 128, batch_first=True)
        self.drop1 = nn.Dropout(0.3)
        self.lstm2 = nn.LSTM(128, 64, batch_first=True)
        self.drop2 = nn.Dropout(0.3)
        self.fc1   = nn.Linear(64, 64)
        self.relu  = nn.ReLU()
        self.fc2   = nn.Linear(64, num_classes)

    def forward(self, x):
        x, _ = self.lstm1(x)
        x     = self.drop1(x)
        x, _ = self.lstm2(x)
        x     = self.drop2(x[:, -1, :])
        x     = self.relu(self.fc1(x))
        return self.fc2(x)


# ──────────────────────────────────────────────
# 시각화
# ──────────────────────────────────────────────
class TrainVisualizer:
    def __init__(self, classes):
        self.classes       = classes
        self.win_name      = "SignBridge 숫자 학습  |  Q: 종료"
        self.loss_history  = []
        self.train_history = []
        self.val_history   = []
        self.batch_results = []
        self.current_frame = None
        self.epoch         = 0
        self.epochs        = 0

    def update_batch(self, mp4_paths, true_words, pred_words):
        self.batch_results = list(zip(true_words, pred_words))
        mp4_path = mp4_paths[0]
        if os.path.exists(mp4_path):
            cap   = cv2.VideoCapture(mp4_path)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, total // 2)
            ret, frame = cap.read()
            cap.release()
            if ret:
                self.current_frame = cv2.resize(frame, (480, 360))

    def update_epoch(self, epoch, epochs, loss, train_acc, val_acc):
        self.epoch  = epoch
        self.epochs = epochs
        self.loss_history.append(loss)
        self.train_history.append(train_acc)
        self.val_history.append(val_acc)

    def draw(self):
        canvas = np.zeros((720, 1280, 3), dtype=np.uint8)
        canvas[:] = (30, 30, 30)

        canvas = draw_korean(canvas, "SignBridge 숫자 학습 시각화",
                             (10, 8), FONT_MEDIUM, (255,200,0))
        canvas = draw_korean(canvas, f"Epoch [{self.epoch:03d}/{self.epochs}]",
                             (500, 8), FONT_MEDIUM, (200,200,200))

        # ── 왼쪽: 영상 ──
        if self.current_frame is not None:
            canvas[55:415, 10:490] = self.current_frame
        else:
            cv2.rectangle(canvas, (10,55), (490,415), (60,60,60), -1)
            canvas = draw_korean(canvas, "영상 없음", (180,210), FONT_MEDIUM, (100,100,100))

        canvas = draw_korean(canvas, "현재 학습 샘플", (10,420), FONT_SMALL, (150,150,150), shadow=False)

        canvas = draw_korean(canvas, "배치 예측 결과:", (10,450), FONT_SMALL, (200,200,200), shadow=False)
        for i, (true, pred) in enumerate(self.batch_results[:6]):
            correct = true == pred
            color   = (0,255,100) if correct else (0,80,255)
            mark    = "✓" if correct else "✗"
            canvas  = draw_korean(canvas, f"  {mark} 정답: {true}  예측: {pred}",
                                  (10, 478+i*34), FONT_SMALL, color, shadow=False)

        # ── 오른쪽: 그래프 ──
        gx, gy, gw, gh = 510, 55, 760, 300
        cv2.rectangle(canvas, (gx,gy), (gx+gw,gy+gh), (50,50,50), -1)
        cv2.rectangle(canvas, (gx,gy), (gx+gw,gy+gh), (80,80,80), 1)
        canvas = draw_korean(canvas, "Loss / Accuracy 그래프",
                             (gx+5,gy-28), FONT_SMALL, (200,200,200), shadow=False)

        def draw_curve(history, color, max_val=100.0):
            if len(history) < 2: return
            pts = []
            for i, v in enumerate(history):
                x = gx + int(i / max(len(history)-1,1) * (gw-20)) + 10
                y = gy + gh - int(v / max_val * (gh-20)) - 10
                pts.append((x,y))
            for i in range(len(pts)-1):
                cv2.line(canvas, pts[i], pts[i+1], color, 2, cv2.LINE_AA)
            cv2.circle(canvas, pts[-1], 4, color, -1)

        if self.loss_history:
            max_loss   = max(self.loss_history) or 1.0
            normalized = [v/max_loss*100 for v in self.loss_history]
            draw_curve(normalized, (0,100,255))
        draw_curve(self.train_history, (0,200,100))
        draw_curve(self.val_history,   (0,200,255))

        legend_y = gy + gh + 10
        cv2.rectangle(canvas, (gx, legend_y), (gx+15, legend_y+12), (0,100,255), -1)
        canvas = draw_korean(canvas, "Loss",      (gx+20,  legend_y-5), FONT_SMALL, (0,100,255),  shadow=False)
        cv2.rectangle(canvas, (gx+80, legend_y), (gx+95, legend_y+12), (0,200,100), -1)
        canvas = draw_korean(canvas, "Train Acc", (gx+100, legend_y-5), FONT_SMALL, (0,200,100),  shadow=False)
        cv2.rectangle(canvas, (gx+200,legend_y), (gx+215,legend_y+12), (0,200,255), -1)
        canvas = draw_korean(canvas, "Val Acc",   (gx+220, legend_y-5), FONT_SMALL, (0,200,255),  shadow=False)

        if self.loss_history:
            info_y     = gy + gh + 50
            last_loss  = self.loss_history[-1]
            last_train = self.train_history[-1] if self.train_history else 0
            last_val   = self.val_history[-1]   if self.val_history   else 0
            best_val   = max(self.val_history)  if self.val_history   else 0

            canvas = draw_korean(canvas, f"Loss: {last_loss:.4f}",     (gx,     info_y), FONT_MEDIUM, (0,100,255))
            canvas = draw_korean(canvas, f"Train: {last_train:.1f}%",  (gx+200, info_y), FONT_MEDIUM, (0,200,100))
            canvas = draw_korean(canvas, f"Val: {last_val:.1f}%",      (gx+420, info_y), FONT_MEDIUM, (0,200,255))
            canvas = draw_korean(canvas, f"최고 Val: {best_val:.1f}%", (gx+600, info_y), FONT_MEDIUM, (255,200,0))

        cv2.imshow(self.win_name, canvas)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return False
        return True

    def close(self):
        cv2.destroyAllWindows()


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

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
    val_loader   = DataLoader(val_dataset,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model     = SignLSTM(FEATURE_DIM, num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
    viz       = TrainVisualizer(full_dataset.classes)

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

        for X, y, true_words, mp4_paths in train_loader:
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

            pred_idxs  = out.argmax(1).cpu().tolist()
            pred_words = [full_dataset.classes[i] for i in pred_idxs]
            viz.update_batch(mp4_paths, list(true_words), pred_words)
            if not viz.draw():
                viz.close()
                return

        model.eval()
        val_correct = val_total = 0
        with torch.no_grad():
            for X, y, _, __ in val_loader:
                X, y = X.to(device), y.to(device)
                out  = model(X)
                val_correct += (out.argmax(1) == y).sum().item()
                val_total   += y.size(0)

        train_acc = train_correct / train_total * 100
        val_acc   = val_correct   / val_total   * 100
        avg_loss  = train_loss    / len(train_loader)

        viz.update_epoch(epoch, EPOCHS, avg_loss, train_acc, val_acc)
        viz.draw()

        print(f"Epoch [{epoch:03d}/{EPOCHS}]  "
              f"Loss: {avg_loss:.4f}  "
              f"Train: {train_acc:.1f}%  │  "
              f"Val: {val_acc:.1f}%")

        if val_acc > best_acc:
            best_acc   = val_acc
            no_improve = 0
            torch.save({
                "epoch":      epoch,
                "model":      model.state_dict(),
                "optimizer":  optimizer.state_dict(),
                "scheduler":  scheduler.state_dict(),
                "le_classes": full_dataset.classes,  # SignBridge 형식
                "val_acc":    val_acc,
            }, MODEL_SAVE)
            print(f"   💾 모델 저장! (Val Acc: {val_acc:.1f}%)")
        else:
            no_improve += 1

        if no_improve >= EARLY_STOP:
            print(f"\n⏹️  {EARLY_STOP} 에포크 개선 없음 → 조기 종료")
            break

        scheduler.step()

    viz.close()
    print(f"\n🎉 학습 완료! 최고 Val Acc: {best_acc:.1f}%")
    print(f"💾 저장 위치: {MODEL_SAVE}")
    print(f"📌 SignBridge 연동 준비 완료!")


if __name__ == "__main__":
    train()