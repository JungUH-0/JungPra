# import os
# import cv2
# import numpy as np
# import torch
# import torch.nn as nn
# import mediapipe as mp
# from collections import deque, Counter
# from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
# from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
# from mediapipe.tasks.python.core.base_options import BaseOptions
# from PIL import ImageFont, ImageDraw, Image

# # ──────────────────────────────────────────────
# # 설정값
# # ──────────────────────────────────────────────
# BASE_DIR     = r"D:\JungPra\pythonpra\signlan"
# MODEL_PATH   = os.path.join(BASE_DIR, "mynum_model.pth")
# HAND_MODEL   = os.path.join(BASE_DIR, "hand_landmarker.task")

# FONT_PATHS = [
#     r"C:\Windows\Fonts\malgun.ttf",
#     r"C:\Windows\Fonts\gulim.ttc",
# ]

# MAX_FRAMES   = 30
# LANDMARK_DIM = 126
# CONF_THRESH  = 0.5
# STABLE_COUNT = 5


# # ──────────────────────────────────────────────
# # 한글 폰트
# # ──────────────────────────────────────────────
# def load_font(size):
#     for path in FONT_PATHS:
#         if os.path.exists(path):
#             return ImageFont.truetype(path, size)
#     return ImageFont.load_default()

# FONT_LARGE  = load_font(120)
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
#         x    = x[:, -1, :]
#         return self.classifier(x)


# def load_model():
#     ckpt        = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
#     classes     = ckpt["classes"]
#     model       = SignLanguageLSTM(len(classes))
#     model.load_state_dict(ckpt["model"])
#     model.eval()
#     print(f"✅ 모델 로드 | 클래스: {classes} | Val Acc: {ckpt.get('val_acc',0):.1f}%")
#     return model, classes


# def load_detector():
#     options = HandLandmarkerOptions(
#         base_options=BaseOptions(model_asset_path=HAND_MODEL),
#         running_mode=VisionTaskRunningMode.IMAGE,
#         num_hands=2,
#         min_hand_detection_confidence=0.5,
#         min_hand_presence_confidence=0.5,
#     )
#     return HandLandmarker.create_from_options(options)


# # ──────────────────────────────────────────────
# # 관절 추출 (x,y,z → 126개)
# # ──────────────────────────────────────────────
# def extract_landmarks(frame, detector):
#     rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
#     result   = detector.detect(mp_image)

#     left  = np.zeros(21 * 3, dtype=np.float32)
#     right = np.zeros(21 * 3, dtype=np.float32)

#     if result.hand_landmarks and result.handedness:
#         for hand_lm, handedness in zip(result.hand_landmarks, result.handedness):
#             coords = np.array(
#                 [[lm.x, lm.y, lm.z] for lm in hand_lm],
#                 dtype=np.float32
#             ).flatten()
#             if handedness[0].category_name == "Left":
#                 left = coords
#             else:
#                 right = coords

#         h, w = frame.shape[:2]
#         for hand_lm in result.hand_landmarks:
#             pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lm]
#             connections = [
#                 (0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
#                 (0,9),(9,10),(10,11),(11,12),(0,13),(13,14),(14,15),(15,16),
#                 (0,17),(17,18),(18,19),(19,20),(5,9),(9,13),(13,17)
#             ]
#             for a, b in connections:
#                 cv2.line(frame, pts[a], pts[b], (0,255,100), 2, cv2.LINE_AA)
#             for pt in pts:
#                 cv2.circle(frame, pt, 5, (0,200,255), -1, cv2.LINE_AA)

#     detected = result.hand_landmarks is not None and len(result.hand_landmarks) > 0
#     return np.concatenate([left, right]), detected


# def draw_progress_bar(frame, progress, x, y, w, h):
#     cv2.rectangle(frame, (x, y), (x+w, y+h), (50,50,50), -1)
#     fill_w = int(w * progress)
#     if fill_w > 0:
#         cv2.rectangle(frame, (x, y), (x+fill_w, y+h), (0,200,100), -1)
#     cv2.rectangle(frame, (x, y), (x+w, y+h), (100,100,100), 1)


# # ──────────────────────────────────────────────
# # 메인
# # ──────────────────────────────────────────────
# def run():
#     print("🚀 숫자 수어 인식 테스트 시작!")
#     print("   종료: Q | 초기화: R\n")

#     model, classes = load_model()
#     detector       = load_detector()

#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened():
#         print("❌ 웹캠을 열 수 없습니다.")
#         return

#     cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

#     frame_seq    = deque(maxlen=MAX_FRAMES)
#     result_buf   = deque(maxlen=STABLE_COUNT)
#     current_num  = ""
#     current_conf = 0.0
#     history      = []

#     # 각 클래스별 확률 저장
#     all_probs    = {c: 0.0 for c in classes}

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break

#         frame = cv2.flip(frame, 1)
#         frame = cv2.resize(frame, (1280, 720))
#         h, w  = frame.shape[:2]

#         coords, hand_detected = extract_landmarks(frame, detector)

#         overlay = frame.copy()
#         cv2.rectangle(overlay, (0,0), (w,60), (20,20,20), -1)
#         cv2.rectangle(overlay, (0,h-160), (w,h), (20,20,20), -1)
#         cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

#         if hand_detected:
#             frame_seq.append(coords)

#             if len(frame_seq) == MAX_FRAMES:
#                 seq = torch.tensor(np.array(frame_seq)[np.newaxis], dtype=torch.float32)
#                 with torch.no_grad():
#                     probs     = torch.softmax(model(seq), dim=1)[0]
#                     idx       = probs.argmax().item()
#                     conf      = float(probs[idx])
#                     all_probs = {c: float(probs[i]) for i, c in enumerate(classes)}

#                 result_buf.append(classes[idx] if conf >= CONF_THRESH else "")
#                 counts   = Counter(result_buf)
#                 top, cnt = counts.most_common(1)[0]

#                 if top and cnt >= STABLE_COUNT // 2 + 1:
#                     if top != current_num:
#                         current_num  = top
#                         current_conf = conf
#                         history.insert(0, top)
#                         history = history[:5]
#                     else:
#                         current_conf = conf

#             progress = len(frame_seq) / MAX_FRAMES
#             draw_progress_bar(frame, progress, 10, h-148, w-20, 14)
#             frame = draw_korean(frame, f"수집: {len(frame_seq)}/{MAX_FRAMES}",
#                                 (10, h-155), FONT_SMALL, (150,150,150), shadow=False)
#         else:
#             frame_seq.clear()
#             frame = draw_korean(frame, "손을 보여주세요",
#                                 (10, h-120), FONT_MEDIUM, (100,100,255))

#         # ── 상단 타이틀 ──
#         frame = draw_korean(frame, "숫자 수어 인식", (10, 8), FONT_MEDIUM, (255,200,0))

#         # ── 숫자 크게 표시 ──
#         if current_num:
#             frame = draw_korean(frame, current_num,
#                                 (w//2 - 40, h//2 - 120), FONT_LARGE, (0,255,150))
#             draw_progress_bar(frame, current_conf, 10, h-50, w-20, 20)
#             frame = draw_korean(frame, f"신뢰도: {current_conf*100:.1f}%",
#                                 (10, h-68), FONT_SMALL, (200,200,200), shadow=False)

#         # ── 각 클래스별 확률 바 ──
#         bar_x = w - 250
#         frame = draw_korean(frame, "클래스별 확률:", (bar_x, 65), FONT_SMALL, (150,150,150), shadow=False)
#         for i, c in enumerate(sorted(classes)):
#             prob  = all_probs.get(c, 0.0)
#             bar_w = int(200 * prob)
#             color = (0,255,150) if c == current_num else (100,100,200)
#             cv2.rectangle(frame, (bar_x, 90+i*40), (bar_x+bar_w, 90+i*40+25), color, -1)
#             cv2.rectangle(frame, (bar_x, 90+i*40), (bar_x+200, 90+i*40+25), (80,80,80), 1)
#             frame = draw_korean(frame, f"{c}: {prob*100:.1f}%",
#                                 (bar_x+5, 90+i*40), FONT_SMALL, (255,255,255), shadow=False)

#         # ── 인식 기록 ──
#         if history:
#             frame = draw_korean(frame, "최근:", (10, 65), FONT_SMALL, (150,150,150), shadow=False)
#         for i, num in enumerate(history[:5]):
#             alpha = max(80, 220-i*35)
#             frame = draw_korean(frame, num, (10+i*60, 90),
#                                 FONT_MEDIUM, (alpha,alpha,alpha))

#         frame = draw_korean(frame, "Q: 종료  R: 초기화",
#                             (10, h-25), FONT_SMALL, (100,100,100), shadow=False)

#         cv2.imshow("숫자 수어 인식 테스트", frame)

#         key = cv2.waitKey(1) & 0xFF
#         if key == ord('q'):
#             break
#         elif key == ord('r'):
#             frame_seq.clear()
#             result_buf.clear()
#             current_num  = ""
#             current_conf = 0.0
#             all_probs    = {c: 0.0 for c in classes}
#             print("🔄 초기화!")

#     cap.release()
#     cv2.destroyAllWindows()
#     detector.close()
#     print("👋 종료!")


# if __name__ == "__main__":
#     run()










# --------------------------------------------------------------------------
# 벡터값 적용전
# import os
# import cv2
# import numpy as np
# import torch
# import torch.nn as nn
# import mediapipe as mp
# from collections import deque, Counter
# from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
# from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
# from mediapipe.tasks.python.core.base_options import BaseOptions
# from PIL import ImageFont, ImageDraw, Image

# # ──────────────────────────────────────────────
# # 설정값 신규모델 le_class 변경 관절 42개포인트로 변경
# # ──────────────────────────────────────────────
# BASE_DIR     = r"D:\JungPra\pythonpra\signlan"
# MODEL_PATH   = os.path.join(BASE_DIR, "newnumber_model_signbridge.pth")
# HAND_MODEL   = os.path.join(BASE_DIR, "hand_landmarker.task")

# FONT_PATHS = [
#     r"C:\Windows\Fonts\malgun.ttf",
#     r"C:\Windows\Fonts\gulim.ttc",
# ]

# MAX_FRAMES   = 30
# FEATURE_DIM  = 42    # x,y × 21관절 (SignBridge 형식)
# CONF_THRESH  = 0.5
# STABLE_COUNT = 5


# # ──────────────────────────────────────────────
# # 한글 폰트
# # ──────────────────────────────────────────────
# def load_font(size):
#     for path in FONT_PATHS:
#         if os.path.exists(path):
#             return ImageFont.truetype(path, size)
#     return ImageFont.load_default()

# FONT_LARGE  = load_font(120)
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
# # 모델 (SignBridge SignLSTM 구조)
# # ──────────────────────────────────────────────
# class SignLSTM(nn.Module):
#     def __init__(self, input_dim, num_classes):
#         super().__init__()
#         self.lstm1 = nn.LSTM(input_dim, 128, batch_first=True)
#         self.drop1 = nn.Dropout(0.3)
#         self.lstm2 = nn.LSTM(128, 64, batch_first=True)
#         self.drop2 = nn.Dropout(0.3)
#         self.fc1   = nn.Linear(64, 64)
#         self.relu  = nn.ReLU()
#         self.fc2   = nn.Linear(64, num_classes)

#     def forward(self, x):
#         x, _ = self.lstm1(x)
#         x     = self.drop1(x)
#         x, _ = self.lstm2(x)
#         x     = self.drop2(x[:, -1, :])
#         x     = self.relu(self.fc1(x))
#         return self.fc2(x)


# def load_model():
#     ckpt        = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
#     classes     = ckpt["le_classes"]   # SignBridge 형식
#     num_classes = len(classes)
#     model       = SignLSTM(FEATURE_DIM, num_classes)
#     model.load_state_dict(ckpt["model"])
#     model.eval()
#     print(f"✅ 모델 로드 완료 | 클래스: {classes} | Val Acc: {ckpt.get('val_acc',0):.1f}%")
#     return model, classes


# def load_detector():
#     options = HandLandmarkerOptions(
#         base_options=BaseOptions(model_asset_path=HAND_MODEL),
#         running_mode=VisionTaskRunningMode.IMAGE,
#         num_hands=2,
#         min_hand_detection_confidence=0.5,
#         min_hand_presence_confidence=0.5,
#     )
#     return HandLandmarker.create_from_options(options)


# # ──────────────────────────────────────────────
# # 관절 추출 (x,y × 21관절 = 42개, 오른손 우선)
# # ──────────────────────────────────────────────
# def extract_landmarks(frame, detector):
#     rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
#     result   = detector.detect(mp_image)

#     coords   = np.zeros(21 * 2, dtype=np.float32)
#     detected = False

#     if result.hand_landmarks and result.handedness:
#         right_lm = None
#         left_lm  = None
#         for hand_lm, handedness in zip(result.hand_landmarks, result.handedness):
#             if handedness[0].category_name == "Right":
#                 right_lm = hand_lm
#             else:
#                 left_lm  = hand_lm

#         target = right_lm if right_lm is not None else left_lm
#         if target is not None:
#             coords   = np.array([[lm.x, lm.y] for lm in target], dtype=np.float32).flatten()
#             detected = True

#         # 관절 화면에 그리기
#         h, w = frame.shape[:2]
#         for hand_lm in result.hand_landmarks:
#             pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lm]
#             connections = [
#                 (0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
#                 (0,9),(9,10),(10,11),(11,12),(0,13),(13,14),(14,15),(15,16),
#                 (0,17),(17,18),(18,19),(19,20),(5,9),(9,13),(13,17)
#             ]
#             for a, b in connections:
#                 cv2.line(frame, pts[a], pts[b], (0,255,100), 2, cv2.LINE_AA)
#             for pt in pts:
#                 cv2.circle(frame, pt, 5, (0,200,255), -1, cv2.LINE_AA)

#     return coords, detected


# def draw_progress_bar(frame, progress, x, y, w, h):
#     cv2.rectangle(frame, (x, y), (x+w, y+h), (50,50,50), -1)
#     fill_w = int(w * progress)
#     if fill_w > 0:
#         cv2.rectangle(frame, (x, y), (x+fill_w, y+h), (0,200,100), -1)
#     cv2.rectangle(frame, (x, y), (x+w, y+h), (100,100,100), 1)


# # ──────────────────────────────────────────────
# # 메인
# # ──────────────────────────────────────────────
# def run():
#     print("🚀 숫자 수어 인식 테스트 시작!")
#     print("   종료: Q | 초기화: R\n")

#     model, classes = load_model()
#     detector       = load_detector()

#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened():
#         print("❌ 웹캠을 열 수 없습니다.")
#         return

#     cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

#     frame_seq    = deque(maxlen=MAX_FRAMES)
#     result_buf   = deque(maxlen=STABLE_COUNT)
#     current_num  = ""
#     current_conf = 0.0
#     history      = []
#     all_probs    = {c: 0.0 for c in classes}

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break

#         frame = cv2.flip(frame, 1)
#         frame = cv2.resize(frame, (1280, 720))
#         h, w  = frame.shape[:2]

#         coords, hand_detected = extract_landmarks(frame, detector)

#         overlay = frame.copy()
#         cv2.rectangle(overlay, (0,0), (w,60), (20,20,20), -1)
#         cv2.rectangle(overlay, (0,h-160), (w,h), (20,20,20), -1)
#         cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

#         if hand_detected:
#             frame_seq.append(coords)

#             if len(frame_seq) >= 15:
#                 seq = torch.tensor(np.array(frame_seq)[np.newaxis], dtype=torch.float32)
#                 with torch.no_grad():
#                     probs     = torch.softmax(model(seq), dim=1)[0]
#                     idx       = probs.argmax().item()
#                     conf      = float(probs[idx])
#                     all_probs = {c: float(probs[i]) for i, c in enumerate(classes)}

#                 result_buf.append(classes[idx] if conf >= CONF_THRESH else "")
#                 counts   = Counter(result_buf)
#                 top, cnt = counts.most_common(1)[0]

#                 if top and cnt >= STABLE_COUNT // 2 + 1:
#                     if top != current_num:
#                         current_num  = top
#                         current_conf = conf
#                         history.insert(0, top)
#                         history = history[:5]
#                     else:
#                         current_conf = conf

#             progress = len(frame_seq) / MAX_FRAMES
#             draw_progress_bar(frame, progress, 10, h-148, w-20, 14)
#             frame = draw_korean(frame, f"수집: {len(frame_seq)}/{MAX_FRAMES}",
#                                 (10, h-155), FONT_SMALL, (150,150,150), shadow=False)
#         else:
#             frame_seq.clear()  # 완전 초기화 유지
#             result_buf.clear()  # 예측 버퍼도 초기화
#             current_num  = ""   # 표시 초기화
#             current_conf = 0.0
#             frame = draw_korean(frame, "손을 보여주세요",
#                         (10, h-120), FONT_MEDIUM, (100,100,255))

#         # ── 상단 타이틀 ──
#         frame = draw_korean(frame, "숫자 수어 인식", (10, 8), FONT_MEDIUM, (255,200,0))

#         # ── 숫자 크게 표시 ──
#         if current_num:
#             frame = draw_korean(frame, current_num,
#                                 (w//2 - 40, h//2 - 120), FONT_LARGE, (0,255,150))
#             draw_progress_bar(frame, current_conf, 10, h-50, w-20, 20)
#             frame = draw_korean(frame, f"신뢰도: {current_conf*100:.1f}%",
#                                 (10, h-68), FONT_SMALL, (200,200,200), shadow=False)

#         # ── 클래스별 확률 바 ──
#         bar_x = w - 250
#         frame = draw_korean(frame, "클래스별 확률:", (bar_x, 65), FONT_SMALL, (150,150,150), shadow=False)
#         for i, c in enumerate(sorted(classes)):
#             prob  = all_probs.get(c, 0.0)
#             bar_w = int(200 * prob)
#             color = (0,255,150) if c == current_num else (100,100,200)
#             cv2.rectangle(frame, (bar_x, 90+i*40), (bar_x+bar_w, 90+i*40+25), color, -1)
#             cv2.rectangle(frame, (bar_x, 90+i*40), (bar_x+200, 90+i*40+25), (80,80,80), 1)
#             frame = draw_korean(frame, f"{c}: {prob*100:.1f}%",
#                                 (bar_x+5, 90+i*40), FONT_SMALL, (255,255,255), shadow=False)

#         # ── 인식 기록 ──
#         if history:
#             frame = draw_korean(frame, "최근:", (10, 65), FONT_SMALL, (150,150,150), shadow=False)
#         for i, num in enumerate(history[:5]):
#             alpha = max(80, 220-i*35)
#             frame = draw_korean(frame, num, (10+i*60, 90),
#                                 FONT_MEDIUM, (alpha,alpha,alpha))

#         frame = draw_korean(frame, "Q: 종료  R: 초기화",
#                             (10, h-25), FONT_SMALL, (100,100,100), shadow=False)

#         cv2.imshow("숫자 수어 인식 테스트", frame)

#         key = cv2.waitKey(1) & 0xFF
#         if key == ord('q'):
#             break
#         elif key == ord('r'):
#             frame_seq.clear()
#             result_buf.clear()
#             current_num  = ""
#             current_conf = 0.0
#             all_probs    = {c: 0.0 for c in classes}
#             print("🔄 초기화!")

#     cap.release()
#     cv2.destroyAllWindows()
#     detector.close()
#     print("👋 종료!")


# if __name__ == "__main__":
#     run()



import os
import cv2
import numpy as np
import torch
import torch.nn as nn
import mediapipe as mp
from collections import deque, Counter
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
from mediapipe.tasks.python.core.base_options import BaseOptions
from PIL import ImageFont, ImageDraw, Image

# ──────────────────────────────────────────────
# 설정값
# ──────────────────────────────────────────────
BASE_DIR     = r"D:\JungPra\pythonpra\signlan"
MODEL_PATH   = os.path.join(BASE_DIR, "newnumber_model_signbridge.pth")
HAND_MODEL   = os.path.join(BASE_DIR, "hand_landmarker.task")

FONT_PATHS = [
    r"C:\Windows\Fonts\malgun.ttf",
    r"C:\Windows\Fonts\gulim.ttc",
]

MAX_FRAMES   = 30
FEATURE_DIM  = 55    # Vector+Angle 형식
CONF_THRESH  = 0.5
STABLE_COUNT = 5

# ── Vector+Angle 관련 상수 ──────────────────
BONE_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
]

ANGLE_PAIRS = [
    (0,1),(1,2),(2,3),
    (4,5),(5,6),(6,7),
    (8,9),(9,10),(10,11),
    (12,13),(13,14),(14,15),
    (16,17),(17,18),(18,19),
]


# ──────────────────────────────────────────────
# 한글 폰트
# ──────────────────────────────────────────────
def load_font(size):
    for path in FONT_PATHS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

FONT_LARGE  = load_font(120)
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
# Vector+Angle 특징 추출
# ──────────────────────────────────────────────
def extract_vector_angle_features(coords_42):
    """42차원 x,y 좌표 → 55차원 방향벡터+각도 변환"""
    coords_42 = np.asarray(coords_42, dtype=np.float32)
    points    = coords_42.reshape(21, 2)

    # 뼈대 방향 벡터 (20개 × 2 = 40개)
    bone_vectors = np.array(
        [points[child] - points[parent] for parent, child in BONE_CONNECTIONS],
        dtype=np.float32,
    )
    lengths      = np.linalg.norm(bone_vectors, axis=1, keepdims=True)
    unit_vectors = bone_vectors / np.maximum(lengths, 1e-6)

    # 관절 각도 (15개)
    angles = []
    for first_idx, second_idx in ANGLE_PAIRS:
        v1  = unit_vectors[first_idx]
        v2  = unit_vectors[second_idx]
        dot = np.clip(np.dot(v1, v2), -1.0, 1.0)
        angles.append(np.arccos(dot) / np.pi)

    return np.concatenate([unit_vectors.flatten(), np.array(angles, dtype=np.float32)])


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


def load_model():
    ckpt        = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
    classes     = ckpt["le_classes"]
    num_classes = len(classes)
    model       = SignLSTM(FEATURE_DIM, num_classes)
    model.load_state_dict(ckpt["model"])
    model.eval()
    print(f"✅ 모델 로드 완료 | 클래스: {classes} | Val Acc: {ckpt.get('val_acc',0):.1f}%")
    print(f"   특징 타입: {ckpt.get('feature_type', 'unknown')} ({ckpt.get('feature_dim', FEATURE_DIM)}차원)")
    return model, classes


def load_detector():
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=HAND_MODEL),
        running_mode=VisionTaskRunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
    )
    return HandLandmarker.create_from_options(options)


# ──────────────────────────────────────────────
# 관절 추출 → Vector+Angle 변환 (55차원)
# ──────────────────────────────────────────────
def extract_landmarks(frame, detector):
    rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result   = detector.detect(mp_image)

    coords_42 = np.zeros(42, dtype=np.float32)
    detected  = False

    if result.hand_landmarks and result.handedness:
        right_lm = None
        left_lm  = None
        for hand_lm, handedness in zip(result.hand_landmarks, result.handedness):
            if handedness[0].category_name == "Right":
                right_lm = hand_lm
            else:
                left_lm  = hand_lm

        target = right_lm if right_lm is not None else left_lm
        if target is not None:
            coords_42 = np.array([[lm.x, lm.y] for lm in target], dtype=np.float32).flatten()
            detected  = True

        # 관절 화면에 그리기
        h, w = frame.shape[:2]
        for hand_lm in result.hand_landmarks:
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lm]
            connections = [
                (0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
                (0,9),(9,10),(10,11),(11,12),(0,13),(13,14),(14,15),(15,16),
                (0,17),(17,18),(18,19),(19,20),(5,9),(9,13),(13,17)
            ]
            for a, b in connections:
                cv2.line(frame, pts[a], pts[b], (0,255,100), 2, cv2.LINE_AA)
            for pt in pts:
                cv2.circle(frame, pt, 5, (0,200,255), -1, cv2.LINE_AA)

    # 42차원 좌표 → 55차원 Vector+Angle 변환
    features_55 = extract_vector_angle_features(coords_42)
    return features_55, detected


def draw_progress_bar(frame, progress, x, y, w, h):
    cv2.rectangle(frame, (x, y), (x+w, y+h), (50,50,50), -1)
    fill_w = int(w * progress)
    if fill_w > 0:
        cv2.rectangle(frame, (x, y), (x+fill_w, y+h), (0,200,100), -1)
    cv2.rectangle(frame, (x, y), (x+w, y+h), (100,100,100), 1)


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def run():
    print("🚀 숫자 수어 인식 테스트 시작! (Vector+Angle 버전)")
    print("   종료: Q | 초기화: R\n")

    model, classes = load_model()
    detector       = load_detector()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 웹캠을 열 수 없습니다.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    frame_seq    = deque(maxlen=MAX_FRAMES)
    result_buf   = deque(maxlen=STABLE_COUNT)
    current_num  = ""
    current_conf = 0.0
    history      = []
    all_probs    = {c: 0.0 for c in classes}

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (1280, 720))
        h, w  = frame.shape[:2]

        features, hand_detected = extract_landmarks(frame, detector)

        overlay = frame.copy()
        cv2.rectangle(overlay, (0,0), (w,60), (20,20,20), -1)
        cv2.rectangle(overlay, (0,h-160), (w,h), (20,20,20), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        if hand_detected:
            frame_seq.append(features)

            if len(frame_seq) >= 15:
                seq = torch.tensor(np.array(frame_seq)[np.newaxis], dtype=torch.float32)
                with torch.no_grad():
                    probs     = torch.softmax(model(seq), dim=1)[0]
                    idx       = probs.argmax().item()
                    conf      = float(probs[idx])
                    all_probs = {c: float(probs[i]) for i, c in enumerate(classes)}

                result_buf.append(classes[idx] if conf >= CONF_THRESH else "")
                counts   = Counter(result_buf)
                top, cnt = counts.most_common(1)[0]

                if top and cnt >= STABLE_COUNT // 2 + 1:
                    if top != current_num:
                        current_num  = top
                        current_conf = conf
                        history.insert(0, top)
                        history = history[:5]
                    else:
                        current_conf = conf

            progress = len(frame_seq) / MAX_FRAMES
            draw_progress_bar(frame, progress, 10, h-148, w-20, 14)
            frame = draw_korean(frame, f"수집: {len(frame_seq)}/{MAX_FRAMES}",
                                (10, h-155), FONT_SMALL, (150,150,150), shadow=False)
        else:
            frame_seq.clear()
            result_buf.clear()
            current_num  = ""
            current_conf = 0.0
            frame = draw_korean(frame, "손을 보여주세요",
                                (10, h-120), FONT_MEDIUM, (100,100,255))

        # ── 상단 타이틀 ──
        frame = draw_korean(frame, "숫자 수어 인식 (Vector+Angle)", (10, 8), FONT_MEDIUM, (255,200,0))

        # ── 숫자 크게 표시 ──
        if current_num:
            frame = draw_korean(frame, current_num,
                                (w//2 - 40, h//2 - 120), FONT_LARGE, (0,255,150))
            draw_progress_bar(frame, current_conf, 10, h-50, w-20, 20)
            frame = draw_korean(frame, f"신뢰도: {current_conf*100:.1f}%",
                                (10, h-68), FONT_SMALL, (200,200,200), shadow=False)

        # ── 클래스별 확률 바 ──
        bar_x = w - 250
        frame = draw_korean(frame, "클래스별 확률:", (bar_x, 65), FONT_SMALL, (150,150,150), shadow=False)
        for i, c in enumerate(sorted(classes)):
            prob  = all_probs.get(c, 0.0)
            bar_w = int(200 * prob)
            color = (0,255,150) if c == current_num else (100,100,200)
            cv2.rectangle(frame, (bar_x, 90+i*35), (bar_x+bar_w, 90+i*35+22), color, -1)
            cv2.rectangle(frame, (bar_x, 90+i*35), (bar_x+200, 90+i*35+22), (80,80,80), 1)
            frame = draw_korean(frame, f"{c}: {prob*100:.1f}%",
                                (bar_x+5, 90+i*35), FONT_SMALL, (255,255,255), shadow=False)

        # ── 인식 기록 ──
        if history:
            frame = draw_korean(frame, "최근:", (10, 65), FONT_SMALL, (150,150,150), shadow=False)
        for i, num in enumerate(history[:5]):
            alpha = max(80, 220-i*35)
            frame = draw_korean(frame, num, (10+i*60, 90),
                                FONT_MEDIUM, (alpha,alpha,alpha))

        frame = draw_korean(frame, "Q: 종료  R: 초기화",
                            (10, h-25), FONT_SMALL, (100,100,100), shadow=False)

        cv2.imshow("숫자 수어 인식 테스트 (Vector+Angle)", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            frame_seq.clear()
            result_buf.clear()
            current_num  = ""
            current_conf = 0.0
            all_probs    = {c: 0.0 for c in classes}
            print("🔄 초기화!")

    cap.release()
    cv2.destroyAllWindows()
    detector.close()
    print("👋 종료!")


if __name__ == "__main__":
    run()
