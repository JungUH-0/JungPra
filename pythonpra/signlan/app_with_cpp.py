# SignBridge - Flask 서버 (C++ 카메라 연동 버전)
# C++ camera_server.cpp 에서 프레임 받아서 AI 처리

from flask import Flask, jsonify, request, send_from_directory
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import pickle, json, time, base64, os, sys
import socket
import threading
import struct
from collections import deque, Counter

app = Flask(__name__)

# ── 경로 설정 ──────────────────────────────
if sys.platform == "win32":
    BASE       = r"C:\Users\AISW_203_101\Desktop\Team_SignBridge\model"
    OUTPUT_DIR = r"C:\Users\AISW_203_101\Desktop\Team_SignBridge\keypoints_output"
    WORD_MODEL = r"C:\Users\AISW_203_101\Desktop\Team_SignBridge\sign_model.pt"
    IMAGE_DIR  = r"C:\Users\AISW_203_101\Desktop\Team_SignBridge\image"
else:
    BASE       = "model"
    OUTPUT_DIR = "keypoints_output"
    WORD_MODEL = "sign_model.pt"
    IMAGE_DIR  = "image"

GOOGLE_MODEL = os.path.join(BASE, "gesture_recognizer.task")
CPP_PORT     = 9999   # C++ 카메라 서버 포트

# ── 전역 변수 (C++에서 받은 최신 프레임) ──
latest_frame = None
frame_lock   = threading.Lock()
cpp_connected = False

# ── C++ 프레임 수신 서버 ──────────────────
def recv_exact(conn, n):
    data = b""
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def cpp_receiver():
    """C++ 카메라 서버에서 프레임 수신하는 스레드"""
    global latest_frame, cpp_connected

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", CPP_PORT))
    server.listen(1)
    print(f"[C++ 수신 서버] 포트 {CPP_PORT}에서 대기 중...")

    while True:
        try:
            conn, addr = server.accept()
            cpp_connected = True
            print(f"[C++ 연결] {addr} 연결됨!")

            while True:
                # 4바이트 크기 수신
                size_data = recv_exact(conn, 4)
                if not size_data:
                    break
                size = struct.unpack("!I", size_data)[0]

                # 프레임 데이터 수신
                frame_data = recv_exact(conn, size)
                if not frame_data:
                    break

                # JPEG 디코딩
                np_arr = np.frombuffer(frame_data, np.uint8)
                frame  = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                if frame is not None:
                    with frame_lock:
                        latest_frame = frame.copy()

            conn.close()
            cpp_connected = False
            print("[C++ 연결] 연결 끊김")
        except Exception as e:
            print(f"[C++ 수신 오류] {e}")

# C++ 수신 스레드 시작
threading.Thread(target=cpp_receiver, daemon=True).start()

# ── MediaPipe 초기화 ──────────────────────
base_options = python.BaseOptions(model_asset_path=GOOGLE_MODEL)
recognizer = vision.GestureRecognizer.create_from_options(
    vision.GestureRecognizerOptions(base_options=base_options, num_hands=2))
print("✅ MediaPipe 로드 완료!")

# ── 숫자 모델 로드 (벡터+각도 55차원 지원) ───────────────
import torch
import torch.nn as nn

NUM_MODEL_PATH = os.path.join(BASE, "mynum_model.pth")
NUM_INPUT_DIM = 55
NUM_FEATURE_TYPE = "vector_angle_2d"

class NumLSTMVectorAngle(nn.Module):
    def __init__(self, input_dim, num_classes):
        super().__init__()
        self.lstm1 = nn.LSTM(input_dim, 128, batch_first=True)
        self.drop1 = nn.Dropout(0.3)
        self.lstm2 = nn.LSTM(128, 64, batch_first=True)
        self.drop2 = nn.Dropout(0.3)
        self.fc1 = nn.Linear(64, 64)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(64, num_classes)
    def forward(self, x):
        x, _ = self.lstm1(x)
        x = self.drop1(x)
        x, _ = self.lstm2(x)
        x = self.drop2(x[:, -1, :])
        x = self.relu(self.fc1(x))
        return self.fc2(x)

class NumLSTMOld(nn.Module):
    def __init__(self, num_classes, input_dim=126):
        super().__init__()
        self.input_norm = nn.LayerNorm(input_dim)
        self.lstm = nn.LSTM(
            input_size=input_dim, hidden_size=256,
            num_layers=3, batch_first=True,
            dropout=0.3, bidirectional=True,
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.5), nn.Linear(256*2, 256),
            nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )
    def forward(self, x):
        x, _ = self.lstm(self.input_norm(x))
        x = x[:, x.size(1)//2, :]
        return self.classifier(x)

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

def extract_vector_angle_features(hand_landmarks):
    """MediaPipe 한 손 랜드마크를 55차원 방향벡터+각도 특징으로 변환한다."""
    points = np.array([[lm.x, lm.y] for lm in hand_landmarks], dtype=np.float32)
    bone_vectors = np.array(
        [points[child] - points[parent] for parent, child in BONE_CONNECTIONS],
        dtype=np.float32,
    )
    lengths = np.linalg.norm(bone_vectors, axis=1, keepdims=True)
    unit_vectors = bone_vectors / np.maximum(lengths, 1e-6)

    angles = []
    for first_idx, second_idx in ANGLE_PAIRS:
        v1 = unit_vectors[first_idx]
        v2 = unit_vectors[second_idx]
        dot = np.clip(np.dot(v1, v2), -1.0, 1.0)
        angles.append(np.arccos(dot) / np.pi)

    return np.concatenate([unit_vectors.flatten(), np.array(angles, dtype=np.float32)]).astype(np.float32)

try:
    num_ckpt = torch.load(NUM_MODEL_PATH, map_location="cpu", weights_only=False)
    NUM_CLASSES = [str(c) for c in num_ckpt.get("le_classes", num_ckpt.get("classes", []))]
    NUM_FEATURE_TYPE = num_ckpt.get("feature_type", "old_126")
    NUM_INPUT_DIM = int(num_ckpt.get("feature_dim", 55 if NUM_FEATURE_TYPE == "vector_angle_2d" else 126))

    if NUM_FEATURE_TYPE == "vector_angle_2d" or NUM_INPUT_DIM == 55:
        num_model = NumLSTMVectorAngle(NUM_INPUT_DIM, len(NUM_CLASSES))
    else:
        num_model = NumLSTMOld(len(NUM_CLASSES), NUM_INPUT_DIM)

    num_model.load_state_dict(num_ckpt["model"])
    num_model.eval()
    NUM_OK = True
    print(f"✅ 숫자 모델 로드 완료! 클래스: {NUM_CLASSES}, 특징: {NUM_FEATURE_TYPE}, 입력 차원: {NUM_INPUT_DIM}")
except Exception as e:
    NUM_OK = False
    NUM_CLASSES = []
    NUM_INPUT_DIM = 55
    NUM_FEATURE_TYPE = "vector_angle_2d"
    print(f"⚠️ 숫자 모델 로드 실패: {e}")


# ── 한글 자모 모델 로드 (오른손 55차원) ─────────────────
HANGUL_MODEL_PATH = os.path.join(BASE, "mynum_model1.pth")
HANGUL_INPUT_DIM = 55
HANGUL_FEATURE_TYPE = "vector_angle_2d"

try:
    hangul_ckpt = torch.load(HANGUL_MODEL_PATH, map_location="cpu", weights_only=False)
    HANGUL_CLASSES = [str(c) for c in hangul_ckpt.get("le_classes", hangul_ckpt.get("classes", []))]
    HANGUL_FEATURE_TYPE = hangul_ckpt.get("feature_type", "vector_angle_2d")
    HANGUL_INPUT_DIM = int(hangul_ckpt.get("feature_dim", 55))
    hangul_model = NumLSTMVectorAngle(HANGUL_INPUT_DIM, len(HANGUL_CLASSES))
    hangul_model.load_state_dict(hangul_ckpt["model"])
    hangul_model.eval()
    HANGUL_OK = True
    print(f"✅ 한글 자모 모델 로드 완료! 클래스: {HANGUL_CLASSES}, 입력 차원: {HANGUL_INPUT_DIM}")
except Exception as e:
    HANGUL_OK = False
    HANGUL_CLASSES = []
    print(f"⚠️ 한글 자모 모델 로드 실패: {e}")
# ── 제스처 매핑 ──────────────────────────
GESTURE_KO = {
    "None":"손을 보여주세요","Closed_Fist":"주먹","Open_Palm":"손바닥",
    "Pointing_Up":"위로","Thumb_Up":"좋아요","Thumb_Down":"싫어요",
    "Victory":"브이","ILoveYou":"사랑해요",
}
GESTURE_EN = {
    "None":"Show your hand","Closed_Fist":"Fist","Open_Palm":"Open Palm",
    "Pointing_Up":"Point Up","Thumb_Up":"Good","Thumb_Down":"Bad",
    "Victory":"Victory","ILoveYou":"I Love You",
}
GESTURE_JA = {
    "None":"手を見せてください","Closed_Fist":"拳","Open_Palm":"手のひら",
    "Pointing_Up":"上","Thumb_Up":"いいね","Thumb_Down":"嫌い",
    "Victory":"V","ILoveYou":"愛してる",
}
GESTURE_ZH = {
    "None":"请展示您的手","Closed_Fist":"拳头","Open_Palm":"手掌",
    "Pointing_Up":"向上","Thumb_Up":"好","Thumb_Down":"不好",
    "Victory":"V","ILoveYou":"我爱你",
}
GESTURE_TRANS = {
    "Closed_Fist": {"en":"Fist",       "ja":"拳",       "zh":"拳头"},
    "Open_Palm":   {"en":"Open Palm",  "ja":"手のひら", "zh":"手掌"},
    "Pointing_Up": {"en":"Point Up",   "ja":"上",       "zh":"向上"},
    "Thumb_Up":    {"en":"Good",       "ja":"いいね",   "zh":"好"},
    "Thumb_Down":  {"en":"Bad",        "ja":"嫌い",     "zh":"不好"},
    "Victory":     {"en":"Victory",    "ja":"ピース",   "zh":"胜利"},
    "ILoveYou":    {"en":"I Love You", "ja":"愛してる", "zh":"我爱你"},
}

NUMBER_WORDS = {
    "0": {"ko": "영", "en": "zero", "ja": "ゼロ", "zh": "零"},
    "1": {"ko": "하나", "en": "one", "ja": "一", "zh": "一"},
    "2": {"ko": "둘", "en": "two", "ja": "二", "zh": "二"},
    "3": {"ko": "셋", "en": "three", "ja": "三", "zh": "三"},
    "4": {"ko": "넷", "en": "four", "ja": "四", "zh": "四"},
    "5": {"ko": "다섯", "en": "five", "ja": "五", "zh": "五"},
    "6": {"ko": "여섯", "en": "six", "ja": "六", "zh": "六"},
    "7": {"ko": "일곱", "en": "seven", "ja": "七", "zh": "七"},
    "8": {"ko": "여덟", "en": "eight", "ja": "八", "zh": "八"},
    "9": {"ko": "아홉", "en": "nine", "ja": "九", "zh": "九"},
}
# 손 연결선
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),(0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),(5,9),(9,13),(13,17)
]

state = {
    "gesture": "None", "gesture_conf": 0.0,
    "num": "", "num_conf": 0.0,
    "hangul": "", "hangul_conf": 0.0,
    "history": [],
    "last_record": None,
    "google_buffer": deque(maxlen=5),
    "num_seq": deque(maxlen=30),
    "num_buffer": deque(maxlen=6),
    "hangul_seq": deque(maxlen=30),
    "hangul_buffer": deque(maxlen=6),
    "jamo_buffer": [],
    "last_command_time": 0.0,
    "hangul_reference_image": "",
}

def stable(buf, val):
    buf.append(val)
    return Counter(buf).most_common(1)[0][0]

def add_history(kind, code, labels):
    """확정된 인식 결과를 시간과 함께 기록한다."""
    if not code or code == "None":
        return
    record_key = f"{kind}:{code}"
    if state.get("last_record") == record_key:
        return
    item = {"time": time.strftime("%H:%M"), "kind": kind, "code": code}
    item.update(labels)
    state["history"].insert(0, item)
    state["history"] = state["history"][:20]
    state["last_record"] = record_key

CHO_LIST = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]
JUNG_LIST = ["ㅏ","ㅐ","ㅑ","ㅒ","ㅓ","ㅔ","ㅕ","ㅖ","ㅗ","ㅘ","ㅙ","ㅚ","ㅛ","ㅜ","ㅝ","ㅞ","ㅟ","ㅠ","ㅡ","ㅢ","ㅣ"]
JONG_LIST = ["", "ㄱ","ㄲ","ㄳ","ㄴ","ㄵ","ㄶ","ㄷ","ㄹ","ㄺ","ㄻ","ㄼ","ㄽ","ㄾ","ㄿ","ㅀ","ㅁ","ㅂ","ㅄ","ㅅ","ㅆ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]
CHO_SET = set(CHO_LIST)
JUNG_SET = set(JUNG_LIST)
JONG_SET = set(JONG_LIST[1:])

def compose_hangul_jamos(jamos):
    """자모 리스트를 가능한 만큼 한글 음절로 조합한다. 예: ㅎㅏㅇㅣ -> 하이"""
    result = []
    i = 0
    while i < len(jamos):
        if i + 1 < len(jamos) and jamos[i] in CHO_SET and jamos[i + 1] in JUNG_SET:
            cho = CHO_LIST.index(jamos[i])
            jung = JUNG_LIST.index(jamos[i + 1])
            jong = 0
            step = 2
            if i + 2 < len(jamos) and jamos[i + 2] in JONG_SET:
                next_is_syllable = i + 3 < len(jamos) and jamos[i + 3] in JUNG_SET
                if not next_is_syllable:
                    jong = JONG_LIST.index(jamos[i + 2])
                    step = 3
            result.append(chr(0xAC00 + (cho * 21 + jung) * 28 + jong))
            i += step
        else:
            result.append(jamos[i])
            i += 1
    return "".join(result)

def split_hands_by_label(result):
    """MediaPipe handedness 기준으로 오른손/왼손 랜드마크를 나눈다."""
    right_hand = None
    left_hand = None
    handedness = getattr(result, "handedness", []) or []
    for idx, hand in enumerate(result.hand_landmarks or []):
        label = ""
        if idx < len(handedness) and handedness[idx]:
            label = handedness[idx][0].category_name
        if label == "Right":
            right_hand = hand
        elif label == "Left":
            left_hand = hand
    if right_hand is None and result.hand_landmarks:
        right_hand = result.hand_landmarks[0]
    return right_hand, left_hand

def count_open_fingers(hand):
    """검지~새끼손가락이 펴진 개수를 단순 규칙으로 계산한다."""
    finger_pairs = [(8, 6), (12, 10), (16, 14), (20, 18)]
    return sum(1 for tip, pip in finger_pairs if hand[tip].y < hand[pip].y)

def detect_two_hand_command(right_hand, left_hand):
    """양손 손모양으로 한글 입력 명령을 감지한다."""
    if right_hand is None or left_hand is None:
        return ""

    right_open = count_open_fingers(right_hand)
    left_open = count_open_fingers(left_hand)

    if right_open >= 4 and left_open >= 4:
        return "reset"
    if right_open <= 1 and left_open <= 1:
        return "combine"
    if left_open >= 4 and right_open <= 1:
        return "undo"
    return ""
def hangul_status_text(lang):
    texts = {
        "ko": "오른손 자모 / 왼손 명령",
        "en": "Right hand jamo / left hand command",
        "ja": "右手の字母 / 左手の命令",
        "zh": "右手字母 / 左手命令",
    }
    return texts.get(lang, texts["ko"])

def draw_hand(frame, lms, w, h):
    pts = [(int(lm.x*w), int(lm.y*h)) for lm in lms]
    finger_colors = {
        "thumb": (0, 0, 255),      # red
        "index": (0, 128, 255),    # orange
        "middle": (0, 255, 255),   # yellow
        "ring": (0, 255, 0),       # green
        "pinky": (255, 0, 0),      # blue
    }
    connection_colors = {
        (0,1): finger_colors["thumb"], (1,2): finger_colors["thumb"],
        (2,3): finger_colors["thumb"], (3,4): finger_colors["thumb"],
        (0,5): finger_colors["index"], (5,6): finger_colors["index"],
        (6,7): finger_colors["index"], (7,8): finger_colors["index"],
        (0,9): finger_colors["middle"], (9,10): finger_colors["middle"],
        (10,11): finger_colors["middle"], (11,12): finger_colors["middle"],
        (0,13): finger_colors["ring"], (13,14): finger_colors["ring"],
        (14,15): finger_colors["ring"], (15,16): finger_colors["ring"],
        (0,17): finger_colors["pinky"], (17,18): finger_colors["pinky"],
        (18,19): finger_colors["pinky"], (19,20): finger_colors["pinky"],
    }
    point_colors = {
        0: (255, 255, 255),
        1: finger_colors["thumb"], 2: finger_colors["thumb"], 3: finger_colors["thumb"], 4: finger_colors["thumb"],
        5: finger_colors["index"], 6: finger_colors["index"], 7: finger_colors["index"], 8: finger_colors["index"],
        9: finger_colors["middle"], 10: finger_colors["middle"], 11: finger_colors["middle"], 12: finger_colors["middle"],
        13: finger_colors["ring"], 14: finger_colors["ring"], 15: finger_colors["ring"], 16: finger_colors["ring"],
        17: finger_colors["pinky"], 18: finger_colors["pinky"], 19: finger_colors["pinky"], 20: finger_colors["pinky"],
    }
    for a,b in HAND_CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], connection_colors.get((a,b), (255,255,255)), 2, cv2.LINE_AA)
    for idx, pt in enumerate(pts):
        size = 5 if idx in [0,4,8,12,16,20] else 3
        cv2.circle(frame, pt, size, point_colors.get(idx, (255,255,255)), -1, cv2.LINE_AA)

@app.route('/process', methods=['POST'])
def process():
    global latest_frame

    data = request.get_json()  # 한 번만 호출
    lang = data.get('lang', 'ko')
    mode = data.get('mode', 'gesture')

    # C++ 연결 여부에 따라 프레임 소스 결정
    with frame_lock:
        frame = latest_frame.copy() if latest_frame is not None else None

    if frame is None:
        # C++ 미연결 시 브라우저 프레임 사용 (기존 방식)
        try:
            if not data.get('frame'):
                return jsonify({"error": "no frame", "cpp_connected": cpp_connected})
            img_data = base64.b64decode(data['frame'].split(',')[1])
            np_arr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            source = "browser"
        except Exception as e:
            return jsonify({"error": "no frame: " + str(e), "cpp_connected": cpp_connected})
    else:
        source = "cpp"

    if frame is None:
        return jsonify({"error": "no frame"})

    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = recognizer.recognize(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))

    # 손 그리기
    if result.hand_landmarks:
        for lm in result.hand_landmarks:
            draw_hand(frame, lm, w, h)

    # 소스 표시 (C++ or Browser)
    src_color = (0, 255, 100) if source == "cpp" else (0, 150, 255)
    cv2.putText(frame, f"Source: {source.upper()}", (10, h-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, src_color, 1)

    # 제스처 모드에서만 구글 제스처 결과를 화면 상태에 반영
    if mode in ("gesture", "hangul") and result.gestures:
        new_g = stable(state["google_buffer"], result.gestures[0][0].category_name)
        prev_g = state["gesture"]
        state["gesture"] = new_g
        state["gesture_conf"] = result.gestures[0][0].score
        if new_g != prev_g and new_g != "None":
            add_history("gesture", new_g, {
                "ko": GESTURE_KO.get(new_g, new_g),
                "en": GESTURE_EN.get(new_g, new_g),
                "ja": GESTURE_JA.get(new_g, new_g),
                "zh": GESTURE_ZH.get(new_g, new_g),
            })
    elif mode in ("gesture", "hangul"):
        state["gesture"] = stable(state["google_buffer"], "None")
        state["gesture_conf"] = 0.0
    else:
        state["gesture"] = "None"
        state["gesture_conf"] = 0.0

    # ── 숫자 모델 인식 ───────────────────
    if mode == "number" and NUM_OK and result.hand_landmarks:
        try:
            lms_all = result.hand_landmarks
            if NUM_FEATURE_TYPE == "vector_angle_2d" or NUM_INPUT_DIM == 55:
                flat_num = extract_vector_angle_features(lms_all[0])
            else:
                flat_parts = []
                for hand in lms_all[:2]:
                    bx, by = hand[0].x, hand[0].y
                    for lm in hand:
                        flat_parts += [lm.x - bx, lm.y - by, lm.z]
                while len(flat_parts) < NUM_INPUT_DIM:
                    flat_parts.append(0.0)
                flat_num = np.array(flat_parts[:NUM_INPUT_DIM], dtype=np.float32)
            state["num_seq"].append(flat_num)
            if len(state["num_seq"]) >= 30:
                seq_n = torch.tensor(np.array(state["num_seq"])[np.newaxis], dtype=torch.float32)
                with torch.no_grad():
                    probs_n = torch.softmax(num_model(seq_n), dim=1)[0]
                n_idx  = probs_n.argmax().item()
                n_conf = float(probs_n[n_idx])
                if n_conf >= 0.60:
                    state["num_buffer"].append(NUM_CLASSES[n_idx])
                else:
                    state["num_buffer"].append("None")
                counts_n = Counter(state["num_buffer"])
                top_n, cnt_n = counts_n.most_common(1)[0]
                if top_n != "None" and cnt_n >= 3:
                    prev_num = state["num"]
                    state["num"] = str(top_n)
                    state["num_conf"] = n_conf
                    if state["num"] != prev_num:
                        add_history("number", state["num"], NUMBER_WORDS.get(state["num"], {
                            "ko": state["num"], "en": state["num"], "ja": state["num"], "zh": state["num"]
                        }))
                else:
                    state["num"] = ""
        except Exception as e:
            state["num"] = ""
    else:
        state["num_seq"].clear()
        state["num_buffer"].append("None")
        state["num"] = ""

    # ── 한글 모드: 오른손 자모 인식 + 왼손 특수 명령 ─────
    if mode == "hangul" and result.hand_landmarks:
        right_hand, left_hand = split_hands_by_label(result)
        command = detect_two_hand_command(right_hand, left_hand)
        now_time = time.time()
        if command and now_time - state.get("last_command_time", 0.0) > 1.2:
            if command == "reset":
                state["hangul"] = ""
                state["hangul_conf"] = 0.0
                state["jamo_buffer"].clear()
                state["hangul_seq"].clear()
                state["hangul_buffer"].clear()
                state["hangul_reference_image"] = "/number-image/\uc591\uc190\ubcf4.png"
                add_history("hangul_command", "reset", {"ko": "\ucd08\uae30\ud654", "en": "Reset", "ja": "Reset", "zh": "Reset", "image": "/number-image/\uc591\uc190\ubcf4.png"})
            elif command == "combine" and state["jamo_buffer"]:
                combined = compose_hangul_jamos(state["jamo_buffer"])
                state["hangul"] = combined
                state["hangul_conf"] = 1.0
                add_history("hangul_word", combined, {"ko": combined, "en": combined, "ja": combined, "zh": combined})
                state["jamo_buffer"].clear()
                state["hangul_seq"].clear()
                state["hangul_buffer"].clear()
                state["hangul_reference_image"] = "/number-image/\uc591\uc190\uc8fc.png"
                add_history("hangul_command", "combine", {"ko": "\uc870\ud569", "en": "Combine", "ja": "Combine", "zh": "Combine", "image": "/number-image/\uc591\uc190\uc8fc.png"})
            elif command == "undo" and state["jamo_buffer"]:
                state["jamo_buffer"].pop()
                state["hangul"] = " ".join(state["jamo_buffer"])
                state["hangul_conf"] = 1.0 if state["jamo_buffer"] else 0.0
                state["hangul_seq"].clear()
                state["hangul_buffer"].clear()
                state["hangul_reference_image"] = "/number-image/\ud55c\uc190\uc8fc.png"
                add_history("hangul_command", "undo", {"ko": "\ub418\ub3cc\ub9ac\uae30", "en": "Undo", "ja": "Undo", "zh": "Undo", "image": "/number-image/\ud55c\uc190\uc8fc.png"})
            state["last_command_time"] = now_time

        # Google Pointing_Up is used as a temporary reliable shortcut for ㅏ.
        google_jamo = ""
        if (
            not command
            and state["gesture"] == "Pointing_Up"
            and state["google_buffer"].count("Pointing_Up") >= 3
            and state["gesture_conf"] >= 0.50
        ):
            google_jamo = "\u314F"

        if google_jamo:
            state["hangul_seq"].clear()
            state["hangul_buffer"].clear()
            state["hangul"] = google_jamo
            state["hangul_conf"] = state["gesture_conf"]
            state["hangul_reference_image"] = ""
            if not state["jamo_buffer"] or state["jamo_buffer"][-1] != google_jamo:
                state["jamo_buffer"].append(google_jamo)
                add_history("hangul_jamo", google_jamo, {"ko": google_jamo, "en": google_jamo, "ja": google_jamo, "zh": google_jamo})
        elif HANGUL_OK and right_hand is not None and not command:
            try:
                flat_hangul = extract_vector_angle_features(right_hand)
                state["hangul_seq"].append(flat_hangul)
                if len(state["hangul_seq"]) >= 30:
                    seq_h = torch.tensor(np.array(state["hangul_seq"])[np.newaxis], dtype=torch.float32)
                    with torch.no_grad():
                        probs_h = torch.softmax(hangul_model(seq_h), dim=1)[0]
                    h_idx = probs_h.argmax().item()
                    h_conf = float(probs_h[h_idx])
                    if h_conf >= 0.60:
                        state["hangul_buffer"].append(HANGUL_CLASSES[h_idx])
                    else:
                        state["hangul_buffer"].append("None")
                    top_h, cnt_h = Counter(state["hangul_buffer"]).most_common(1)[0]
                    if top_h != "None" and cnt_h >= 3:
                        state["hangul"] = top_h
                        state["hangul_conf"] = h_conf
                        state["hangul_reference_image"] = ""
                        if not state["jamo_buffer"] or state["jamo_buffer"][-1] != top_h:
                            state["jamo_buffer"].append(top_h)
                            add_history("hangul_jamo", top_h, {"ko": top_h, "en": top_h, "ja": top_h, "zh": top_h})
            except Exception:
                state["hangul"] = ""
                state["hangul_conf"] = 0.0
    else:
        state["hangul_seq"].clear()
        state["hangul_buffer"].append("None")
        if mode != "hangul":
            state["hangul"] = ""
            state["hangul_conf"] = 0.0

    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
    processed_frame = "data:image/jpeg;base64," + base64.b64encode(buf).decode()

    g = state["gesture"]
    trans = GESTURE_TRANS.get(g, {})
    trans_labels = {"ko": "KO", "en": "EN", "ja": "JA", "zh": "ZH"}

    # 숫자 인식 우선, 없으면 제스처
    if mode == "number":
        num_key = str(state["num"])
        display = NUMBER_WORDS.get(num_key, {}).get(lang, num_key) if num_key else ""
        conf    = state["num_conf"]
        if g in ["Pointing_Up", "Victory"]:
            g = "None"
        selected_trans = ""
        if not display:
            number_prompts = {
                "ko": "숫자를 보여주세요",
                "en": "Show a number",
                "ja": "数字を見せてください",
                "zh": "请展示数字",
            }
            display = number_prompts.get(lang, number_prompts["ko"])
            conf = 0.0
    elif mode == "hangul":
        display = state["hangul"] or " ".join(state["jamo_buffer"])
        conf = state["hangul_conf"]
        selected_trans = ""
        if not display:
            display = hangul_status_text(lang)
            conf = 0.0
    else:
        maps = {"ko": GESTURE_KO, "en": GESTURE_EN, "ja": GESTURE_JA, "zh": GESTURE_ZH}
        display = maps.get(lang, GESTURE_KO).get(g, g)
        conf    = state["gesture_conf"]
        selected_trans = "" if lang == "ko" else trans.get(lang, "")

    return jsonify({
        "frame": processed_frame,
        "display": display,
        "conf": round(conf * 100, 1),
        "gesture": g,
        "trans_label": trans_labels.get(lang, "KO"),
        "trans_text": selected_trans,
        "history": [{"time": h["time"], "text": h.get(lang, h.get("ko", "")), "kind": h.get("kind", ""), "image": h.get("image", "")} for h in state["history"]],
        "num": state["num"],
        "jamo_buffer": state["jamo_buffer"],
        "hangul": state["hangul"],
        "hangul_reference_image": state["hangul_reference_image"],
        "cpp_connected": cpp_connected,
        "source": source,
    })

@app.route('/status')
def status():
    return jsonify({
        "cpp_connected": cpp_connected,
        "has_frame": latest_frame is not None,
    })

@app.route('/number-image/<path:filename>')
def number_image(filename):
    return send_from_directory(IMAGE_DIR, filename)

@app.route('/')
def index():
    return HTML

HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>SignBridge</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#0a0a0a;color:#f0f0f0;font-family:'Noto Sans KR',sans-serif;min-height:100vh}
  .header{display:flex;align-items:center;justify-content:space-between;padding:16px 24px;border-bottom:1px solid #222}
  .header-title{font-size:18px;font-weight:700;color:#fbbf24}
  .live-badge{display:flex;align-items:center;gap:6px;font-size:13px;color:#fbbf24;font-weight:700}
  .live-dot{width:8px;height:8px;border-radius:50%;background:#ef4444;animation:pulse 1.5s infinite}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
  .cpp-status{padding:8px 24px;background:#111;border-bottom:1px solid #222;font-size:12px;}
  .cpp-on{color:#0f6e56}.cpp-off{color:#888}
  .lang-tabs{display:flex;gap:8px;padding:12px 24px;border-bottom:1px solid #222}
  .lang-tab{padding:6px 16px;border-radius:6px;font-size:13px;cursor:pointer;border:1px solid #333;background:transparent;color:#888;transition:all .2s}
  .lang-tab.active{background:#fbbf24;color:#0a0a0a;border-color:#fbbf24}
  .mode-tabs{display:flex;gap:8px;padding:0 24px 12px;border-bottom:1px solid #222}
  .mode-tab{padding:7px 16px;border-radius:6px;font-size:13px;font-weight:700;cursor:pointer;border:1px solid #333;background:#111;color:#888;transition:all .2s}
  .mode-tab.active{background:#0f6e56;color:#fff;border-color:#0f6e56}
  .main{display:grid;grid-template-columns:1fr 2fr 1fr;gap:16px;padding:16px 24px}
  .panel{background:#111;border:1px solid #222;border-radius:12px;padding:16px}
  .panel-title{font-size:12px;color:#666;margin-bottom:12px}
  .ref-img{width:100%;aspect-ratio:1;background:#1a1a1a;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:64px;overflow:hidden}
  .ref-img img{width:88%;height:88%;object-fit:contain;display:block}
  .cam-wrap{background:#000;border-radius:8px;overflow:hidden}
  .cam-wrap img{width:100%;display:block}
  .conf-bar{height:8px;background:#1e1e1e;border-radius:4px;overflow:hidden;margin-top:8px}
  .conf-fill{height:100%;background:linear-gradient(90deg,#fbbf24,#f59e0b);border-radius:4px;transition:width .3s}
  .result-box{background:#1a1a1a;border-radius:8px;padding:16px;text-align:center;min-height:120px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px}
  .result-word{font-size:28px;font-weight:700;color:#fbbf24}
  .speak-btn{margin-top:4px;padding:7px 14px;border-radius:6px;border:1px solid #333;background:#111;color:#fbbf24;font-size:13px;font-weight:700;cursor:pointer;transition:all .2s}
  .speak-btn:hover:not(:disabled){background:#fbbf24;color:#0a0a0a;border-color:#fbbf24}
  .speak-btn:disabled{color:#555;border-color:#262626;background:#151515;cursor:not-allowed;opacity:.65}
  .subtitle-bar{background:#111;border-top:1px solid #222;padding:14px 24px;display:flex;align-items:center;gap:12px}
  .history-bar{background:#0d0d0d;border-top:1px solid #1f1f1f;padding:10px 24px;display:flex;align-items:center;gap:10px;font-size:12px;color:#666;overflow:hidden;white-space:nowrap}
  .history-list{display:flex;gap:16px;overflow:hidden}
  .history-item{display:inline-flex;gap:5px;align-items:center;color:#777}
  .history-time{color:#fbbf24;font-weight:700}
  .history-command-image{width:28px;height:28px;object-fit:contain;border-radius:3px}
  .cam-status{font-size:12px;color:#666;text-align:center;padding:40px}
</style>
</head>
<body>
<div class="header">
  <div class="header-title" id="app-title">◆ 실시간 <b style="color:#fbbf24">수어</b> 번역 자막 시스템</div>
  <div class="live-badge"><div class="live-dot"></div> LIVE</div>
</div>
<div class="cpp-status" id="cpp-status">
  <span class="cpp-off">⏳ C++ 카메라 서버 대기 중... (camera_server 실행 시 자동 연결)</span>
</div>
<div class="lang-tabs">
  <div class="lang-tab active" id="tab-ko" onclick="setLang('ko')">🇰🇷 한국어</div>
  <div class="lang-tab" id="tab-en" onclick="setLang('en')">🇺🇸 ENG</div>
  <div class="lang-tab" id="tab-ja" onclick="setLang('ja')">🇯🇵 JPN</div>
  <div class="lang-tab" id="tab-zh" onclick="setLang('zh')">🇨🇳 CHN</div>
</div>
<div class="mode-tabs">
  <div class="mode-tab active" id="mode-gesture" onclick="setMode('gesture')">제스처 모드</div>
  <div class="mode-tab" id="mode-number" onclick="setMode('number')">숫자 모드</div>
  <div class="mode-tab" id="mode-hangul" onclick="setMode('hangul')">한글 모드</div>
</div>
<div class="main">
  <div class="panel">
    <div class="panel-title" id="ref-title">학습된 수어 이미지</div>
    <div class="ref-img" id="ref-emoji">🤟</div>
    <div style="margin-top:12px;font-size:13px;color:#666;text-align:center" id="ref-guide">수어를 보여주세요</div>
  </div>
  <div class="panel">
    <div class="panel-title" id="cam-title">📷 라이브 캠</div>
    <div class="cam-wrap">
      <img id="processed-frame" src="" style="display:none">
      <div class="cam-status" id="cam-status">카메라 시작 중...</div>
    </div>
    <div class="conf-bar"><div class="conf-fill" id="conf-fill" style="width:0%"></div></div>
    <div style="font-size:12px;color:#fbbf24;margin-top:6px" id="conf-text">정확도 0%</div>
  </div>
  <div class="panel">
    <div class="panel-title" id="result-title">분석결과</div>
    <div class="result-box">
      <div class="result-word" id="result-word">—</div>
      <button class="speak-btn" id="speak-btn" onclick="speakCurrentResult()" disabled>🔊 읽기</button>
    </div>
    <div style="margin-top:12px;font-size:11px;color:#555" id="history-title">최근 인식</div>
    <div id="mini-history" style="display:flex;flex-direction:column;gap:4px;margin-top:6px"></div>
  </div>
</div>
<div class="subtitle-bar">
  <div style="font-size:12px;color:#666" id="subtitle-label">실시간 번역 자막 →</div>
  <div style="font-size:16px;font-weight:700" id="sub-main">—</div>
  <div style="font-size:14px;color:#888" id="sub-trans"></div>
</div>
<div class="history-bar">
  <span id="history-bar-label">기록</span>
  <div class="history-list" id="history-list"></div>
</div>

<video id="video" style="display:none" autoplay playsinline></video>
<canvas id="canvas" style="display:none"></canvas>

<script>
let activeLang='ko', recognitionMode='gesture', processing=false, lastConf=0, lastCppConnected=false, currentSpeechText='';
const GESTURE_EMOJI={
  'None':'❌','Closed_Fist':'✊','Open_Palm':'🖐',
  'Pointing_Up':'☝️','Thumb_Up':'👍','Thumb_Down':'👎',
  'Victory':'✌️','ILoveYou':'🤟'
};
const NUMBER_IMAGE={
  '0':'/number-image/0.png',  
  '1':'/number-image/1.png',
  '2':'/number-image/2.png',
  '3':'/number-image/3.png',
  '4':'/number-image/4.png',
  '5':'/number-image/5.png',
  '6':'/number-image/6.png',
  '7':'/number-image/7.png',
  '8':'/number-image/8.png',
  '9':'/number-image/9.png',

};
const HANGUL_IMAGE={};
['\u3131','\u3134','\u3137','\u3139','\u3141','\u3142','\u3145','\u3147','\u3148','\u314A','\u314B','\u314C','\u314D','\u314E',
 '\u314F','\u3150','\u3151','\u3152','\u3153','\u3154','\u3155','\u3156','\u3157','\u315B','\u315C','\u3160','\u3161','\u3163']
  .forEach(jamo=>{HANGUL_IMAGE[jamo]='/number-image/'+encodeURIComponent(jamo)+'.png';});
const TTS_LANG={ko:'ko-KR',en:'en-US',ja:'ja-JP',zh:'zh-CN'};
const UNSPEAKABLE_TEXT=new Set([
  '', '—', '-',
  '손을 보여주세요','수어를 보여주세요','숫자를 보여주세요','카메라 시작 중...','카메라 오류',
  'Show your hand','Please show a sign','Show a number','Starting camera...','Camera error',
  '手を見せてください','数字を見せてください','カメラ起動中...','カメラエラー',
  '请展示您的手','请展示手语','请展示数字','摄像头启动中...','摄像头错误'
]);

function isSpeakableText(text){
  return text && !UNSPEAKABLE_TEXT.has(String(text).trim());
}

function updateSpeakButton(enabled){
  const btn=document.getElementById('speak-btn');
  if(btn) btn.disabled=!enabled;
}

function speakCurrentResult(){
  if(!currentSpeechText) return;
  if(!('speechSynthesis' in window)){
    alert('이 브라우저는 음성 읽기를 지원하지 않습니다.');
    return;
  }
  window.speechSynthesis.cancel();
  const utter=new SpeechSynthesisUtterance(currentSpeechText);
  utter.lang=TTS_LANG[activeLang] || 'ko-KR';
  utter.rate=0.95;
  utter.pitch=1;
  window.speechSynthesis.speak(utter);
}
const UI_TEXT={
  ko:{
    appTitle:'◆ 실시간 <b style="color:#fbbf24">수어</b> 번역 자막 시스템',
    tabs:['🇰🇷 한국어','🇺🇸 ENG','🇯🇵 JPN','🇨🇳 CHN'],
    cppOn:'✅ C++ 카메라 서버 연결됨! (고속 처리 중)',
    cppOff:'⏳ C++ 카메라 서버 대기 중...',
    refTitle:'학습된 수어 이미지',
    refGuide:'수어를 보여주세요',
    camTitle:'📷 라이브 캠',
    cameraStarting:'카메라 시작 중...',
    cameraError:'카메라 오류',
    confidence:'정확도',
    resultTitle:'분석결과',
    historyTitle:'최근 인식',
    recordLabel:'기록',
    subtitleLabel:'실시간 번역 자막 →',
    gestureMode:'제스처 모드',
    numberMode:'숫자 모드',
    hangulMode:'한글 모드',
    speakButton:'🔊 읽기',
  },
  en:{
    appTitle:'◆ Real-time <b style="color:#fbbf24">Sign Language</b> Translation Subtitle System',
    tabs:['🇰🇷 KOR','🇺🇸 English','🇯🇵 JPN','🇨🇳 CHN'],
    cppOn:'✅ C++ camera server connected! (high-speed processing)',
    cppOff:'⏳ Waiting for C++ camera server...',
    refTitle:'Learned sign image',
    refGuide:'Please show a sign',
    camTitle:'📷 Live Cam',
    cameraStarting:'Starting camera...',
    cameraError:'Camera error',
    confidence:'Confidence',
    resultTitle:'Analysis Result',
    historyTitle:'Recent Recognition',
    recordLabel:'History',
    subtitleLabel:'Real-time Translation Subtitle →',
    gestureMode:'Gesture Mode',
    numberMode:'Number Mode',
    hangulMode:'Hangul Mode',
    speakButton:'🔊 Speak',
  },
  ja:{
    appTitle:'◆ リアルタイム<b style="color:#fbbf24">手話</b>翻訳字幕システム',
    tabs:['🇰🇷 韓国語','🇺🇸 英語','🇯🇵 日本語','🇨🇳 中国語'],
    cppOn:'✅ C++カメラサーバー接続済み！（高速処理中）',
    cppOff:'⏳ C++カメラサーバー待機中...',
    refTitle:'学習済み手話画像',
    refGuide:'手話を見せてください',
    camTitle:'📷 ライブカメラ',
    cameraStarting:'カメラ起動中...',
    cameraError:'カメラエラー',
    confidence:'信頼度',
    resultTitle:'分析結果',
    historyTitle:'最近の認識',
    recordLabel:'履歴',
    subtitleLabel:'リアルタイム翻訳字幕 →',
    gestureMode:'ジェスチャーモード',
    numberMode:'数字モード',
    hangulMode:'ハングルモード',
    speakButton:'🔊 読み上げ',
  },
  zh:{
    appTitle:'◆ 实时<b style="color:#fbbf24">手语</b>翻译字幕系统',
    tabs:['🇰🇷 韩语','🇺🇸 英语','🇯🇵 日语','🇨🇳 中文'],
    cppOn:'✅ C++ 摄像头服务器已连接！（高速处理中）',
    cppOff:'⏳ 正在等待 C++ 摄像头服务器...',
    refTitle:'已学习的手语图像',
    refGuide:'请展示手语',
    camTitle:'📷 实时摄像头',
    cameraStarting:'摄像头启动中...',
    cameraError:'摄像头错误',
    confidence:'准确度',
    resultTitle:'分析结果',
    historyTitle:'最近识别',
    recordLabel:'历史',
    subtitleLabel:'实时翻译字幕 →',
    gestureMode:'手势模式',
    numberMode:'数字模式',
    hangulMode:'韩文模式',
    speakButton:'🔊 朗读',
  }
};

function uiText(){
  return UI_TEXT[activeLang] || UI_TEXT.ko;
}

function updateUiText(){
  const t=uiText();
  document.getElementById('app-title').innerHTML=t.appTitle;
  ['ko','en','ja','zh'].forEach((lang,i)=>{
    document.getElementById(`tab-${lang}`).textContent=t.tabs[i];
  });
  document.getElementById('ref-title').textContent=t.refTitle;
  document.getElementById('ref-guide').textContent=t.refGuide;
  document.getElementById('cam-title').textContent=t.camTitle;
  document.getElementById('result-title').textContent=t.resultTitle;
  document.getElementById('history-title').textContent=t.historyTitle;
  document.getElementById('history-bar-label').textContent=t.recordLabel;
  document.getElementById('subtitle-label').textContent=t.subtitleLabel;
  document.getElementById('mode-gesture').textContent=t.gestureMode;
  document.getElementById('mode-number').textContent=t.numberMode;
  document.getElementById('mode-hangul').textContent=t.hangulMode;
  document.getElementById('speak-btn').textContent=t.speakButton;
  document.getElementById('conf-text').textContent=`${t.confidence} ${lastConf}%`;
  document.getElementById('cpp-status').innerHTML=
    `<span class="${lastCppConnected?'cpp-on':'cpp-off'}">${lastCppConnected?t.cppOn:t.cppOff}</span>`;
  const camStatus=document.getElementById('cam-status');
  if(camStatus && camStatus.style.display !== 'none'){
    camStatus.textContent=t.cameraStarting;
  }
}

function setLang(lang){
  activeLang=lang;
  currentSpeechText='';
  updateSpeakButton(false);
  document.querySelectorAll('.lang-tab').forEach((t,i)=>t.classList.toggle('active',['ko','en','ja','zh'][i]===lang));
  updateUiText();
}

function setMode(mode){
  recognitionMode=mode;
  currentSpeechText='';
  updateSpeakButton(false);
  document.getElementById('mode-gesture').classList.toggle('active', mode==='gesture');
  document.getElementById('mode-number').classList.toggle('active', mode==='number');
  document.getElementById('mode-hangul').classList.toggle('active', mode==='hangul');
  document.getElementById('sub-trans').textContent='';
}

async function startCamera(){
  try{
    const s=await navigator.mediaDevices.getUserMedia({video:true});
    document.getElementById('video').srcObject=s;
    document.getElementById('cam-status').style.display='none';
    document.getElementById('processed-frame').style.display='block';
  }catch(e){
    document.getElementById('cam-status').textContent=uiText().cameraStarting;
    document.getElementById('processed-frame').style.display='block';
  }
  processFrame(); // 카메라 실패해도 항상 실행
}

async function processFrame(){
  if(processing){requestAnimationFrame(processFrame);return;}
  const video=document.getElementById('video');
  const canvas=document.getElementById('canvas');
  
  let frameData = '';
  // C++ 서버가 없을 때만 브라우저 카메라 프레임을 보조 입력으로 전송
  if(!lastCppConnected && video.srcObject && video.readyState >= 2){
    canvas.width=320;canvas.height=240;
    canvas.getContext('2d').drawImage(video,0,0,320,240);
    frameData=canvas.toDataURL('image/jpeg',0.5);
  }
  
  processing=true;
  try{
    const r=await fetch('/process',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({frame:frameData,lang:activeLang,mode:recognitionMode})
    });
    const d=await r.json();
    lastConf=d.conf || 0;
    lastCppConnected=!!d.cpp_connected;
    const frameEl=document.getElementById('processed-frame');
    const camStatus=document.getElementById('cam-status');
    if(d.frame){
      frameEl.src=d.frame;
      frameEl.style.display='block';
      camStatus.style.display='none';
    } else if(d.error){
      camStatus.textContent=lastCppConnected ? uiText().cameraStarting : `${uiText().cameraError}: ${d.error}`;
      camStatus.style.display='block';
    }
    document.getElementById('conf-fill').style.width=lastConf+'%';
    document.getElementById('conf-text').textContent=uiText().confidence+' '+lastConf+'%';
    document.getElementById('result-word').textContent=d.display||'—';
    const displayText=d.display||'';
    const canSpeak=lastConf>0 && isSpeakableText(displayText);
    currentSpeechText=canSpeak ? displayText : '';
    updateSpeakButton(canSpeak);
    document.getElementById('sub-main').textContent=d.display||'—';
    document.getElementById('sub-trans').textContent=
      d.trans_text ? `${d.trans_label}:${d.trans_text}` : '';

    // C++ 연결 상태
    const cppEl=document.getElementById('cpp-status');
    if(d.cpp_connected){
      cppEl.innerHTML=`<span class="cpp-on">${uiText().cppOn}</span>`;
    } else {
      cppEl.innerHTML=`<span class="cpp-off">${uiText().cppOff}</span>`;
    }

    if(!d.frame && d.error){
      processing=false;
      requestAnimationFrame(processFrame);
      return;
    }

    // 이모지 업데이트
    const numKey=String(d.num || d.display || '');
    const refEmoji=document.getElementById('ref-emoji');
    if(recognitionMode==='hangul'){
      const hangulKey=String((d.jamo_buffer || []).slice(-1)[0] || '');
      const hangulImage=d.hangul_reference_image || HANGUL_IMAGE[hangulKey];
      if(hangulImage){
        const image=new Image();
        image.src=hangulImage;
        image.alt='hangul '+hangulKey;
        image.onerror=()=>{refEmoji.textContent=hangulKey;};
        refEmoji.replaceChildren(image);
      } else {
        refEmoji.textContent=hangulKey || '❌';
      }
    } else if(NUMBER_IMAGE[numKey]){
      refEmoji.innerHTML=`<img src="${NUMBER_IMAGE[numKey]}" alt="number ${numKey}">`;
    } else {
      refEmoji.textContent=GESTURE_EMOJI[d.gesture] || '🤟';
    }

    const historyItems=d.history || [];
    const visibleHistoryItems=historyItems.filter(h=>{
      if(recognitionMode==='hangul') return h.kind.startsWith('hangul');
      if(recognitionMode==='number') return h.kind==='number';
      return h.kind==='gesture';
    });
    document.getElementById('history-list').innerHTML=
      visibleHistoryItems.slice(0,12).map(h=>{
        const image=h.image ? `<img class="history-command-image" src="${h.image}" alt="${h.text}" onerror="this.remove()">` : '';
        return `<span class="history-item"><span class="history-time">${h.time}</span>${image}${h.text}</span>`;
      }).join('');

    document.getElementById('mini-history').innerHTML=
      visibleHistoryItems.slice(0,5).map(h=>
        `<div style="font-size:12px;color:#666;display:flex;justify-content:space-between">
          <span>${h.text}</span><span style="color:#444">${h.time}</span>
        </div>`
      ).join('');
  }catch(e){console.error(e);}
  processing=false;
  requestAnimationFrame(processFrame);
}

updateUiText();
startCamera();
</script>
</body>
</html>"""

if __name__ == '__main__':
    print("SignBridge 서버 시작! (C++ 소켓 연동 버전)")
    print(f"C++ 카메라 서버 대기 포트: {CPP_PORT}")
    print("브라우저: http://localhost:7860")
    app.run(host='0.0.0.0', port=7860, debug=False, threaded=True)
























