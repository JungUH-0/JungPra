# ============================================================
#  개인 AI 비서 - 카메라 입력 모듈
#  SignBridge 기반으로 추출 및 정리
#  감지 대상: 손동작 / 눈 깜빡임 / 표정(기본)
# ============================================================

import cv2 as cv
import mediapipe as mp
import numpy as np
import time
import os  # [추가] 디버그 로그 파일 경로용
import threading
from collections import deque  # [추가] 손 위치 이동(스와이프) 추적용
from PIL import Image, ImageDraw, ImageFont  # [추가] cv.putText는 한글을 못 그려서 한글 표시용으로 사용
import windowcontrol  # [추가] 스와이프/손날 제스처로 창 제어

# [추가] 디버그용 - 특정 이벤트가 발동한 순간, 그 직전 몇 프레임의 판정값을 파일에 남겨서
# 나중에 확인할 수 있게 함 (개발/튜닝 끝나면 지워도 되는 임시 진단 도구)
DEBUG_LOG_PATH = os.path.join(os.path.dirname(__file__), "debug_log.txt")

# [추가] 한글 텍스트 표시용 폰트 (OpenCV putText는 Hershey 폰트라 한글 렌더링이 안 됨)
KOREAN_FONT_PATH = r"C:\Windows\Fonts\malgun.ttf"  # 맑은 고딕(윈도우 기본 한글 폰트)
_korean_font_cache = {}


def _get_korean_font(size):
    if size not in _korean_font_cache:
        _korean_font_cache[size] = ImageFont.truetype(KOREAN_FONT_PATH, size)
    return _korean_font_cache[size]


def put_korean_text(frame, text, org, font_size=24, color=(255, 200, 0)):
    """
    OpenCV 프레임(BGR numpy 배열)에 한글 텍스트를 그림 (cv.putText처럼 frame을 제자리에서 수정).
    PIL로 그린 뒤 다시 numpy로 변환하는 방식이라 매 프레임 호출하면 약간의 비용이 있지만,
    텍스트 몇 줄 정도는 실시간 표시에 문제 없는 수준.
    """
    img_pil = Image.fromarray(cv.cvtColor(frame, cv.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    # color는 OpenCV(BGR) 관례를 그대로 받되, PIL은 RGB라서 순서를 뒤집어줌
    rgb_color = (color[2], color[1], color[0])
    draw.text(org, text, font=_get_korean_font(font_size), fill=rgb_color)
    frame[:] = cv.cvtColor(np.array(img_pil), cv.COLOR_RGB2BGR)

# ── MediaPipe 초기화 ──────────────────────────────────────
mp_hands    = mp.solutions.hands
mp_face     = mp.solutions.face_mesh
mp_drawing  = mp.solutions.drawing_utils
mp_styles   = mp.solutions.drawing_styles

# ── 특징 추출용 상수 (SignBridge 동일) ────────────────────
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

# 눈 랜드마크 인덱스 (Face Mesh 기준)
LEFT_EYE  = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33,  160, 158, 133, 153, 144]

# EAR 임계값 설정
EAR_THRESHOLD  = 0.20   # 이 값 이하면 눈 감은 것으로 판단
LONG_BLINK_SEC = 3    # 이 시간 이상 감기면 '길게 감기'로 판단

# [수정] FPS가 20~40 사이로 들쭉날쭉해도 항상 같게 동작하도록 프레임수 대신 시간(초) 기준으로 변경
MIN_BLINK_SEC           = 0.05  # 눈 감은 시간이 이보다 짧으면 노이즈로 보고 무시
DOUBLE_BLINK_WINDOW_SEC = 1.0   # 이 시간 안에 짧은 깜빡임이 2번 나오면 더블 블링크

# [추가] 눈 인식 스트릭(화면 켜기) 설정
EYE_STREAK_SEC      = 5.0  # 이 시간 이상 계속 눈이 인식되면 화면 켜기
EYE_BLINK_IGNORE_SEC = 0.4  # 이보다 짧게 감은 건 자연스러운 깜빡임으로 보고 스트릭 유지

# [추가] 손 스와이프(쓸어올리기/쓸어내리기) 감지 설정
SWIPE_WINDOW_SEC   = 0.27  # [수정] 위치 변화를 추적할 시간(초) - 프레임수 대신 시간 기준 (기존 8프레임@30fps 환산)
SWIPE_Y_THRESHOLD  = 0.18  # 이 정도 이상 이동해야 스와이프로 인식 (정규화 좌표 기준) [수정] 과민 인식 완화를 위해 0.12→0.18로 상향
SWIPE_COOLDOWN_SEC = 0.6   # 한 번 인식 후 재인식까지 대기 시간

# [추가] 손 중심점 계산용 랜드마크 (손목 + 4개 손가락 MCP 관절)
HAND_CENTER_INDICES = [0, 5, 9, 13, 17]

# [추가] 손바닥/손등/손날 판별 설정
# [수정] 정규화(단위벡터화)된 외적 = 두 벡터 사잇각의 sin값이라 -1~1 범위로 고정됨.
# 예전엔 정규화 없이 원본 좌표차로 외적을 구해서, 손이 카메라에서 멀어져 랜드마크 간
# 거리가 작아지면 손날이 아닌데도 cross 값이 작아져 손날로 오인식되는 문제가 있었음.
# [수정] 0.15(약 8.6도)는 너무 엄격해서 손날 인식률이 낮았음 → 0.28(약 16.3도)로 완화
EDGE_SIN_THRESHOLD = 0.28  # sin(각도) 기준 - 이 각도 이내로 손을 세우면 손날로 판정 (edge 진입 기준)

# [추가] 손날 자세를 유지하는 동안 손이 미세하게 떨리기만 해도 sin값이 EDGE_SIN_THRESHOLD를
# 넘나들면서 edge↔손등/손바닥 사이에서 판정이 깜빡이는(flicker) 문제가 있었음. 그래서
# "이미 edge였던 상태"에서는 더 확실히 벗어나야만(이 값을 넘어야만) 손등/손바닥으로
# 전환되도록 진입 기준(0.28)보다 넉넉한 이탈 기준을 따로 둠 (히스테리시스)
EDGE_EXIT_SIN_THRESHOLD = 0.42

# [추가] 클릭류(좌/우클릭/커스텀슬롯1) 제스처를 미리 막기 위한 더 넉넉한 기준.
# EDGE_SIN_THRESHOLD보다 큰 값이라, 손날로 "확정"되기 전 - 손을 세우는 과도기(전환 중)
# 부터 미리 클릭류를 막아준다. (과도기 중에 엄지가 우연히 검지/중지에 가까워지면서
# 아직 "손날"로 확정 안 된 그 프레임에 클릭이 튀는 문제가 있었음)
EDGE_GATE_SIN_THRESHOLD = 0.45

# [추가] 손날+스와이프다운(닫기 확인) 인식률 개선용 - "정확히 그 프레임"에 손날이어야만
# 인정하면, 빠르게 손을 내리치는 동작 중엔 프레임 사이에서 각도가 흔들려 놓치기 쉬움.
# 최근 이 시간 안에 손날이 한 번이라도 잡혔으면 "손날 상태"로 인정해서 여유를 줌
EDGE_RECENT_SEC = 0.3
ORIENTATION_KO = {"front": "손바닥", "back": "손등", "edge": "손날"}  # [추가] 화면 표시용 한글 라벨

# [추가] 양손이 겹쳐졌는지(박수 동작 보조 판정용) 설정
HANDS_TOGETHER_THRESHOLD = 0.15  # 두 손 중심점 사이 거리(정규화 좌표)가 이보다 작으면 겹친 것으로 판정 - 실측 후 조정 필요

# [추가] 핀치(엄지+검지 집기)로 창 드래그 설정
PINCH_ON_DIST  = 0.05  # 엄지-검지 거리(정규화 좌표)가 이보다 가까우면 "집기" 시작 - 실측 후 조정 필요
PINCH_OFF_DIST = 0.08  # 집은 상태에서 이 이상 벌어지면 "놓기" (ON보다 느슨하게 잡아 떨림으로 인한 오해제 방지)

# [추가] 검지 손가락으로 실제 마우스 커서 조작 설정
CURSOR_SMOOTHING = 0.5  # 랜드마크 떨림으로 인한 커서 흔들림 완화용 EMA 계수 (0=필터 없음, 1에 가까울수록 둔감/부드러움)
# [추가] 카메라 프레임 전체가 아니라 중앙의 이 비율만큼만 화면 전체에 매핑 - 손을 조금만
# 움직여도 커서가 화면 끝까지 크게 움직이게 함(감도 증폭). 값이 클수록 더 민감해짐.
# [수정] 커서 기준점을 검지 끝 → 손바닥 중심으로 바꾸면서, 같은 화면 이동에 필요한
# 손 움직임의 범위가 커져서 0.08(약 1.19배)로는 화면 좌우 끝까지 가기엔 너무 느려짐 →
# 0.15(중앙 70% 매핑, 약 1.43배 증폭)로 다시 올림
CURSOR_ACTIVE_MARGIN = 0.15

# [수정] 우클릭 판정 설정 - 검지+중지 겹침은 손날 자세와 충돌해서, 엄지를 손바닥
# 중심 쪽으로 넣는 동작(주먹 쥐듯 엄지를 안으로 접는 느낌)으로 변경
# [수정] 0.10 → 0.06으로 낮췄는데도 여전히 엄지가 살짝만 움직여도 발동할 만큼
# 민감해서 0.035로 더 낮춤 (더욱 깊이 접어야만 인식되게 함)
THUMB_TUCK_DIST = 0.035  # 엄지 끝과 손바닥 중심 사이 거리(정규화 좌표)가 이보다 가까우면 "엄지 넣음" - 실측 후 조정 필요

# [추가] 엄지척(예)/엄지다운(아니오) 판정 설정
# 검지~새끼 4개 손가락의 (MCP, PIP, TIP) 인덱스 - 다 말려있어야 "주먹"으로 인정
FIST_FINGERS = [(5, 6, 8), (9, 10, 12), (13, 14, 16), (17, 18, 20)]
THUMB_UPDOWN_Y_MARGIN = 0.08  # 엄지 끝이 손바닥 중심보다 이 정도 이상 위/아래여야 업/다운으로 판정
# [추가] 엄지다운을 하려고 손을 움직이는 도중 잠깐 엄지업처럼 보이는 전환 자세를 거치면서
# "예"가 먼저 오인식되는 문제가 있어서, 이 시간 이상 같은 상태를 유지해야 확정하도록 함
THUMB_UPDOWN_HOLD_SEC = 1.0

# [추가] 커스텀 명령 슬롯 1 - 엄지+중지 붙이기 (LLM/commandmodule에 등록한 사용자 정의
# 명령 실행용). 엄지+검지 핀치(좌클릭)와 같은 방식이지만 손가락 조합만 다름 - 검증된
# 판정 방식을 그대로 재사용해서 새 슬롯을 늘림
# [수정] 임계값이 하나(0.05)뿐이면 그 값 근처에서 거리가 미세하게 떨릴 때마다 붙음/떨어짐이
# 반복되면서 여러 번 연속 발동하는 문제가 있었음. 좌클릭(PINCH_ON_DIST/OFF_DIST)처럼
# ON/OFF 두 단계로 나눠서 여유를 줌
PINCH_MIDDLE_ON_DIST  = 0.05  # 이 거리보다 가까우면 "붙음" 시작 - 실측 후 조정 필요
PINCH_MIDDLE_OFF_DIST = 0.08  # 붙은 상태에서 이 이상 벌어져야 "떨어짐" (ON보다 느슨하게 잡아 떨림 방지)
# [추가] 손을 빠르게 돌리는 도중에도 순간적으로 엄지-중지가 스치듯 가까워질 수 있어서,
# 진짜로 붙여서 "유지"한 경우만 인정하도록 최소 유지시간을 둠 (엄지척/다운과 같은 방식)
PINCH_MIDDLE_HOLD_SEC = 0.1

# [수정] 마우스 휠 스크롤 자세 설정 - 검지/약지/새끼를 다 말아야 했던 건 손이 너무
# 불편해서, 약지/새끼만 말면 되도록 완화 (검지는 펴져있든 말든 상관 안 함)
WHEEL_CURL_FINGERS = [(13, 14, 16), (17, 18, 20)]  # 약지/새끼의 (MCP, PIP, TIP)
# [수정] 중지 손끝 하나만 독립적으로 움직이는 건 실제로 어려운 동작이었음(약지가 인대
# 구조상 중지/새끼랑 같이 움직이는 경우가 많아서, 중지를 펴는 순간 약지도 같이 펴져서
# wheel_pose 자체가 깨져버림). 그래서 손가락 하나의 미세 움직임 대신, 이미 스와이프에서
# 검증된 "손바닥 중심점 전체를 위/아래로 움직이기" 방식을 재사용 - 약지+새끼를 만 자세를
# 유지한 채로 손 전체를 위/아래로 움직이면 휠이 동작함
WHEEL_HAND_MARGIN = 0.06  # 손바닥 중심이 기준점보다 이 정도 이상 위/아래로 움직이면 휠 업/다운
WHEEL_TICK_INTERVAL_SEC = 0.12  # 활성화된 동안 이 간격으로 휠 이벤트를 반복 발생시킴


# ── 특징 추출 함수 (SignBridge 동일, 55차원) ──────────────
def extract_vector_angle_features(hand_landmarks):
    """
    MediaPipe 손 랜드마크 → 55차원 특징벡터
    20개 뼈대 방향벡터(x,y) × 2 = 40 + 관절각도 15 = 55차원
    """
    points = np.array([[lm.x, lm.y] for lm in hand_landmarks], dtype=np.float32)
    bone_vectors = np.array(
        [points[child] - points[parent] for parent, child in BONE_CONNECTIONS],
        dtype=np.float32,
    )
    lengths = np.linalg.norm(bone_vectors, axis=1, keepdims=True)
    unit_vectors = bone_vectors / np.maximum(lengths, 1e-6)

    angles = []
    for first_idx, second_idx in ANGLE_PAIRS:
        v1  = unit_vectors[first_idx]
        v2  = unit_vectors[second_idx]
        dot = np.clip(np.dot(v1, v2), -1.0, 1.0)
        angles.append(np.arccos(dot) / np.pi)

    return np.concatenate(
        [unit_vectors.flatten(), np.array(angles, dtype=np.float32)]
    ).astype(np.float32)


# ── EAR 계산 함수 ─────────────────────────────────────────
def get_ear(landmarks, eye_indices, w, h):
    """Eye Aspect Ratio: 눈 감김 정도 수치화"""
    pts = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in eye_indices]
    v1  = np.linalg.norm(np.array(pts[1]) - np.array(pts[5]))
    v2  = np.linalg.norm(np.array(pts[2]) - np.array(pts[4]))
    h1  = np.linalg.norm(np.array(pts[0]) - np.array(pts[3]))
    return (v1 + v2) / (2.0 * h1)


# ── 손바닥/손등/손날 판별 함수 ─────────────────────────────
def _hand_edge_sin(landmarks):
    """
    손목(0) → 인덱스 MCP(5) → 새끼 MCP(17) 벡터 사잇각의 sin값(정규화된 외적, -1~1) 계산.
    get_hand_orientation과 클릭류 제스처 게이팅(EDGE_GATE_SIN_THRESHOLD)이 이 값을 공유해서 씀.
    """
    wrist     = landmarks[0]
    index_mcp = landmarks[5]
    pinky_mcp = landmarks[17]

    v1x, v1y = index_mcp.x - wrist.x, index_mcp.y - wrist.y
    v2x, v2y = pinky_mcp.x - wrist.x, pinky_mcp.y - wrist.y

    v1_len = (v1x ** 2 + v1y ** 2) ** 0.5
    v2_len = (v2x ** 2 + v2y ** 2) ** 0.5
    if v1_len < 1e-6 or v2_len < 1e-6:
        return None  # 랜드마크가 거의 겹쳐서 방향을 판단할 수 없는 프레임

    return (v1x * v2y - v1y * v2x) / (v1_len * v2_len)  # 정규화된 외적 = sin(사잇각)


def get_hand_orientation(landmarks, handedness, previous=None):
    """
    - [수정] 두 벡터를 단위벡터로 정규화한 뒤 외적을 구함 (= 사잇각의 sin값, -1~1로 스케일 고정)
      → 손이 카메라에 가깝든 멀든(=벡터 크기가 커지든 작아지든) 판정이 흔들리지 않음
    - sin값 절댓값이 작으면 손을 세운 상태(손날), 그 외에는 부호로 손바닥/손등 구분
    - [추가] previous(직전 프레임 판정 결과)로 히스테리시스 적용 - 직전이 "edge"였으면
      더 넉넉한 EDGE_EXIT_SIN_THRESHOLD를 기준으로 판정해서, 손날 자세 유지 중 미세한
      떨림으로 edge↔손등/손바닥 사이에서 깜빡이는 걸 막음
    """
    cross = _hand_edge_sin(landmarks)
    if cross is None:
        return previous  # 판단 불가한 프레임은 직전 상태를 그대로 유지

    edge_threshold = EDGE_EXIT_SIN_THRESHOLD if previous == "edge" else EDGE_SIN_THRESHOLD
    if abs(cross) < edge_threshold:
        return "edge"  # 손날

    # [수정] front/back 부호가 실제와 반대로 나와서(손등을 손바닥으로 오판정) 뒤집음
    if handedness == "Right":
        return "back" if cross < 0 else "front"
    else:
        return "back" if cross > 0 else "front"


# ── 엄지척(예)/엄지다운(아니오) 판별 함수 ──────────────────
def get_thumb_updown(landmarks, center_y):
    """
    검지~새끼 4개 손가락이 전부 말려있는(주먹) 상태에서, 엄지 끝이 손바닥 중심보다
    충분히 위/아래에 있으면 "up"(엄지척=예) / "down"(엄지다운=아니오)으로 판정.
    - 손가락이 말렸는지는 [손끝-손목 거리] < [PIP 관절-손목 거리]로 판단
      (펴져 있으면 손끝이 손목에서 제일 멀고, 말리면 PIP보다 손목에 가까워짐)
    """
    wrist = landmarks[0]
    for mcp_i, pip_i, tip_i in FIST_FINGERS:
        tip_to_wrist = ((landmarks[tip_i].x - wrist.x) ** 2 + (landmarks[tip_i].y - wrist.y) ** 2) ** 0.5
        pip_to_wrist = ((landmarks[pip_i].x - wrist.x) ** 2 + (landmarks[pip_i].y - wrist.y) ** 2) ** 0.5
        if tip_to_wrist >= pip_to_wrist:
            return None  # 손가락 하나라도 펴져 있으면 주먹이 아님

    thumb_tip = landmarks[4]
    if thumb_tip.y < center_y - THUMB_UPDOWN_Y_MARGIN:
        return "up"
    if thumb_tip.y > center_y + THUMB_UPDOWN_Y_MARGIN:
        return "down"
    return None  # 주먹은 맞는데 엄지가 옆으로 뻗어있는 등 애매한 경우


# ── 휠 스크롤 자세 판별 함수 ────────────────────────────────
def is_wheel_pose(landmarks):
    """약지/새끼는 말리고 중지는 펴져 있는지 판정 (검지/엄지 위치는 상관 안 함)"""
    wrist = landmarks[0]
    for mcp_i, pip_i, tip_i in WHEEL_CURL_FINGERS:
        tip_to_wrist = ((landmarks[tip_i].x - wrist.x) ** 2 + (landmarks[tip_i].y - wrist.y) ** 2) ** 0.5
        pip_to_wrist = ((landmarks[pip_i].x - wrist.x) ** 2 + (landmarks[pip_i].y - wrist.y) ** 2) ** 0.5
        if tip_to_wrist >= pip_to_wrist:
            return False  # 약지/새끼 중 하나라도 펴져 있으면 아님

    middle_tip_to_wrist = ((landmarks[12].x - wrist.x) ** 2 + (landmarks[12].y - wrist.y) ** 2) ** 0.5
    middle_pip_to_wrist = ((landmarks[10].x - wrist.x) ** 2 + (landmarks[10].y - wrist.y) ** 2) ** 0.5
    return middle_tip_to_wrist > middle_pip_to_wrist  # 중지는 펴져 있어야 함


# ── 카메라 입력 모듈 메인 클래스 ─────────────────────────
class CameraModule:
    """
    카메라로부터 손동작 / 눈 깜빡임 / 표정을 감지하는 모듈
    
    감지 결과는 self.result 딕셔너리에 저장됨
    외부에서 self.result를 읽어서 명령 매핑에 사용
    """

    def __init__(self, camera_id=0, show_window=True):
        self.camera_id   = camera_id
        self.show_window = show_window
        self.running     = False

        # 손 인식기
        self.hands = mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        # 얼굴 메시 (눈 + 표정)
        self.face_mesh = mp_face.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,  # [수정] 홍채(iris) 랜드마크 안 쓰는데 켜져있어 불필요한 연산이었음 - FPS 변동 완화
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # 눈 깜빡임 상태
        self._eye_close_start = None  # 눈 감기 시작 시간

        # [수정] 더블 블링크 판정용 (시간 기준으로 변경 - FPS 변동에 영향 안 받게)
        self._last_blink_time = None

        # [추가] 눈 인식 스트릭(화면 켜기) / 롱블링크 화면끄기 상태
        self._eye_streak_start     = None   # 눈이 계속 인식된(열린) 시작 시각
        self._eye_streak_triggered = False  # 이번 스트릭에서 이미 화면 켜기를 실행했는지
        self._long_blink_triggered = False  # 이번 롱블링크에서 이미 화면 끄기를 실행했는지

        # [수정] 손 스와이프 상태 - (시각, y좌표) 기록, 시간 기준 윈도우로 판정 (FPS 변동에 영향 안 받게)
        self._hand_y_history = deque(maxlen=200)  # 시간 기준으로 trim하므로 maxlen은 안전장치용 상한일 뿐
        self._last_swipe_time = 0.0

        # [추가] 손날+스와이프다운(닫기 확인) 인식률 개선용 - 최근에 손날이 잡힌 시각 기억
        self._last_edge_time = 0.0

        # [추가] 화면에 계속 표시할 마지막 상태 텍스트 (다음 동작 인식 전까지 유지)
        self._eye_display_text  = None   # ("BLINK!" / "LONG BLINK!", color)
        self._hand_display_text = None   # ("SWIPE UP" / "SWIPE DOWN", color)

        # [비활성화] 핀치로 창을 SetWindowPos로 직접 옮기던 예전 방식 - 이제 검지가 실제
        # 마우스 커서이므로, 핀치는 실제 좌클릭(마우스 다운/업)으로 대체함
        # self._drag_hwnd   = None
        # self._drag_offset = (0.0, 0.0)
        self._screen_w, self._screen_h = windowcontrol.get_screen_size()  # 손 좌표 → 화면 좌표 매핑용

        # [추가] 검지 손가락으로 마우스 커서를 조작하는 기능용 - EMA 스무딩 상태
        self._cursor_smooth_x = None
        self._cursor_smooth_y = None

        # [추가] 핀치(엄지+검지) = 실제 좌클릭 - 지금 마우스 버튼을 누르고 있는 상태인지
        self._left_button_down = False

        # [수정] 우클릭 제스처를 검지+중지 겹침(손날 자세와 충돌) 대신 엄지를 손바닥
        # 중심 쪽으로 넣는 동작으로 변경. rising edge(넣는 순간 1회)만 발동하도록 상태 기억
        self._thumb_tucked = False

        # [추가] 커스텀 명령 슬롯 1(엄지+중지 붙이기) - rising edge(붙는 순간 1회) 상태 기억
        self._pinch_middle_active = False
        self._pinch_middle_candidate_since = None  # [추가] 최소 유지시간(hold) 판정용

        # [추가] 손 방향(front/back/edge) 히스테리시스용 - 직전 판정 결과 기억
        self._last_orientation = None

        # [추가] 디버그용 - 최근 프레임들의 판정값 기록 (이벤트 발동 시 파일로 덤프)
        self._debug_history = deque(maxlen=40)
        try:
            with open(DEBUG_LOG_PATH, "w", encoding="utf-8") as f:
                f.write(f"[디버그 로그 시작 @ {time.strftime('%H:%M:%S')}]\n")
        except OSError:
            pass

        # [추가] 엄지척/엄지다운 - 짧은 전환 자세로 오인식되지 않도록 유지 시간 추적
        self._thumb_updown_candidate       = None  # 지금 후보로 잡힌 상태 ("up"/"down"/None)
        self._thumb_updown_candidate_since = None  # 후보 상태가 시작된 시각

        # [수정] 휠 스크롤 상태 - 약지+새끼를 만 자세가 시작된 순간의 손바닥 중심 y좌표(기준점)
        self._wheel_baseline_y     = None
        self._last_wheel_tick_time = 0.0

        # 결과 딕셔너리 (외부에서 읽는 곳)
        self.result = {
            # 손동작
            "hand_features"  : None,   # 55차원 numpy 배열 (오른손 우선)
            "hand_side"      : None,   # "Right" / "Left" / None
            "hand_detected"  : False,
            "swipe_up"       : False,  # [추가] 손을 위로 쓸어올리는 동작 감지
            "swipe_down"     : False,  # [추가] 손을 아래로 쓸어내리는 동작 감지
            "hand_orientation": None,  # [추가] "front" / "back" / "edge"
            "close_request"  : False,  # [수정] 손날+스와이프다운 → 닫기 확인 요청 (예/아니오로 최종 결정)
            "hands_together" : False,  # [추가] 양손이 겹쳐졌는지 (박수 보조 판정용)
            "left_click"     : False,  # [추가] 핀치(엄지+검지) - 지금 마우스 왼쪽 버튼을 누르고 있는지
            "right_click"    : False,  # [추가] 엄지를 손 중앙으로 넣기 - 이번 프레임에 우클릭 발생했는지
            "thumbs_up"      : False,  # [추가] 주먹+엄지 위 = 예
            "thumbs_down"    : False,  # [추가] 주먹+엄지 아래 = 아니오
            "pinch_middle"   : False,  # [추가] 커스텀 명령 슬롯 1(엄지+중지 붙이기) - 이번 프레임에 발생했는지

            # 눈 깜빡임
            "blink"          : False,  # 이번 프레임에 깜빡임 발생 여부
            "long_blink"     : False,  # 길게 감기 여부
            "double_blink"   : False,  # [추가] 10프레임 안에 짧은 깜빡임 2번
            "eye_closed"     : False,  # 지금 눈을 감고 있는지 (실시간)
            "ear"            : 0.0,    # 현재 EAR 수치

            # 표정 (추후 확장용 자리)
            "expression"     : None,

            # FPS
            "fps"            : 0.0,
        }

        self._lock = threading.Lock()

    # ── 디버그용: 최근 프레임 판정값 기록/덤프 ─────────────
    def _debug_record(self, **kwargs):
        self._debug_history.append((time.time(), kwargs))

    def _debug_dump(self, label):
        try:
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"\n=== {label} @ {time.strftime('%H:%M:%S')} ===\n")
                for t, kwargs in self._debug_history:
                    values = " ".join(f"{k}={v}" for k, v in kwargs.items())
                    f.write(f"  t={t:.3f} {values}\n")
        except OSError:
            pass

    # ── 내부: 손동작 처리 ────────────────────────────────
    def _process_hands(self, frame_rgb, frame_vis):
        h, w = frame_vis.shape[:2]
        res  = self.hands.process(frame_rgb)

        features  = None
        hand_side = None
        detected  = False
        chosen_landmarks = None  # [추가] 스와이프 판정에 쓸 손의 랜드마크
        hand_centers = []  # [추가] 양손 겹침(박수 보조 판정) 계산용 중심점 목록

        if res.multi_hand_landmarks:
            detected = True
            # 오른손 우선으로 특징 추출
            for i, hand_lm in enumerate(res.multi_hand_landmarks):
                handedness = res.multi_handedness[i].classification[0].label
                if handedness == "Right" or features is None:
                    features  = extract_vector_angle_features(hand_lm.landmark)
                    hand_side = handedness
                    chosen_landmarks = hand_lm.landmark  # [추가]

                # [추가] 이 손의 중심점도 기록 (양손 겹침 판정용)
                hand_centers.append((
                    float(np.mean([hand_lm.landmark[j].x for j in HAND_CENTER_INDICES])),
                    float(np.mean([hand_lm.landmark[j].y for j in HAND_CENTER_INDICES])),
                ))

                # 시각화
                mp_drawing.draw_landmarks(
                    frame_vis, hand_lm, mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0,200,255), thickness=2, circle_radius=3),
                    mp_drawing.DrawingSpec(color=(0,255,100), thickness=2),
                )

        # [추가] 양손이 모두 보이고 두 중심점이 가까우면 "겹침"으로 판정 (박수 보조 판정용)
        hands_together = False
        if len(hand_centers) == 2:
            (x1, y1), (x2, y2) = hand_centers
            dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
            hands_together = dist < HANDS_TOGETHER_THRESHOLD
            cv.putText(frame_vis, f"hands_dist:{dist:.2f}", (10, 240),
                       cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # [수정] 손목+4개 MCP 관절(0,5,9,13,17) 평균을 손 중심점으로 잡아 스와이프 감지
        swipe_up   = False
        swipe_down = False
        orientation = None
        close_request = False  # [추가] 손날+스와이프다운 → 닫기 확인 요청 (실제 닫기는 main.py에서)
        right_click_event = False  # [추가] 이번 프레임에 우클릭 제스처가 확정됐는지
        thumbs_up   = False  # [추가] 주먹+엄지 위 = 예
        thumbs_down = False  # [추가] 주먹+엄지 아래 = 아니오
        pinch_middle_event = False  # [추가] 이번 프레임에 커스텀 슬롯 1(엄지+중지)이 발생했는지
        if chosen_landmarks is not None:
            thumb_tip  = chosen_landmarks[4]
            index_tip  = chosen_landmarks[8]
            middle_tip = chosen_landmarks[12]  # [추가] 커스텀 명령 슬롯 1(엄지+중지 붙이기)용

            # [수정] 손목+4개 MCP 관절(0,5,9,13,17) 평균 = 손바닥 중심점.
            # 커서 기준점을 검지 끝에서 이 손바닥 중심점으로 바꿈 - 검지 끝을 기준으로 하면
            # 클릭하려고 엄지-검지를 붙이는 마지막 순간에 검지 끝 자체가 움직여서 커서가
            # 목표 지점에서 벗어나는 문제가 있었음. 손바닥 중심은 핀치 동작에 거의 영향을
            # 안 받아서 클릭 순간에도 커서가 안정적으로 유지됨.
            center_x = float(np.mean([chosen_landmarks[i].x for i in HAND_CENTER_INDICES]))
            center_y = float(np.mean([chosen_landmarks[i].y for i in HAND_CENTER_INDICES]))

            # [수정] 손 방향(orientation)을 여기서 먼저 계산해둠. 손날 자세는 손날을 만들면서
            # 엄지를 검지/손바닥중심/중지 쪽에 가깝게 붙이게 되는 경우가 많아서, 그대로 두면
            # 손날을 하는 동시에 좌클릭/우클릭/커스텀슬롯이 같이 발동하는 문제가 있었음.
            # 그래서 orientation=="edge"인 동안은 엄지 기반 클릭류 제스처를 아예 판정하지 않음
            orientation = get_hand_orientation(chosen_landmarks, hand_side, previous=self._last_orientation)
            self._last_orientation = orientation  # [추가] 히스테리시스용 - 다음 프레임에서 참조
            if orientation == "edge":
                self._last_edge_time = time.time()  # [추가] 손날+스와이프 인식률 개선용 기록

            # [추가] "손날로 확정"되기 전 과도기(손을 세우는 중)에도 클릭류를 미리 막기 위한
            # 더 넉넉한 판정. orientation=="edge"보다 먼저 켜져서, 손날로 전환하는 동안
            # 엄지가 우연히 검지/중지에 가까워지면서 클릭이 튀는 문제를 막아줌
            edge_sin = _hand_edge_sin(chosen_landmarks)
            near_edge = edge_sin is not None and abs(edge_sin) < EDGE_GATE_SIN_THRESHOLD

            # [추가] 디버그용 - 매 프레임 판정값을 기록해둠 (pinch_middle 오발동 시 덤프해서 확인)
            _debug_thumb_middle_dist = ((thumb_tip.x - middle_tip.x) ** 2 + (thumb_tip.y - middle_tip.y) ** 2) ** 0.5
            self._debug_record(
                orientation=orientation,
                edge_sin=round(edge_sin, 3) if edge_sin is not None else None,
                near_edge=near_edge,
                thumb_middle_dist=round(_debug_thumb_middle_dist, 4),
                pinch_middle_active=self._pinch_middle_active,
            )

            # [추가] 휠 스크롤 자세(약지+새끼 말기, 중지는 폄)인지 미리 판정
            wheel_pose = is_wheel_pose(chosen_landmarks)

            # [추가] 엄지척(예)/엄지다운(아니오) - 주먹 쥔 상태에서 엄지 방향으로 판정
            # (손날 자세에서는 판정하지 않음)
            # [수정] 엄지다운을 하려고 손을 움직이다가 잠깐 엄지업처럼 보이는 전환 자세를
            # 거치면서 "예"가 먼저 오인식되는 문제가 있어서, THUMB_UPDOWN_HOLD_SEC 이상
            # 같은 상태가 유지돼야만 확정하도록 함
            if orientation != "edge":
                thumb_updown = get_thumb_updown(chosen_landmarks, center_y)
                if thumb_updown != self._thumb_updown_candidate:
                    self._thumb_updown_candidate       = thumb_updown
                    # [수정] thumb_updown이 None인 채로 계속 유지되면(주먹 안 쥔 상태)
                    # 위 조건이 매번 "None != None"(False)이라 걸리지 않아 _since가 영영
                    # None으로 남고, 그 상태에서 아래 time.time() - None 연산이 터졌었음.
                    # thumb_updown이 None이면 유지 시간을 잴 필요가 없으니 아예 None으로 둠
                    self._thumb_updown_candidate_since = time.time() if thumb_updown is not None else None

                if thumb_updown is not None and self._thumb_updown_candidate_since is not None:
                    held_sec = time.time() - self._thumb_updown_candidate_since
                    if held_sec >= THUMB_UPDOWN_HOLD_SEC:
                        if thumb_updown == "up":
                            thumbs_up = True
                            self._hand_display_text = ("THUMBS UP (YES)", (0, 255, 0))
                        elif thumb_updown == "down":
                            thumbs_down = True
                            self._hand_display_text = ("THUMBS DOWN (NO)", (0, 0, 255))
                    else:
                        # [추가] 확정 전까지 얼마나 유지됐는지 화면에 표시해서 타이밍을 가늠하기 쉽게 함
                        cv.putText(frame_vis, f"HOLD {held_sec:.1f}/{THUMB_UPDOWN_HOLD_SEC:.0f}s ({thumb_updown})",
                                   (10, 180), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 200), 2)
            else:
                self._thumb_updown_candidate       = None
                self._thumb_updown_candidate_since = None

            # [수정] 프레임 전체(0~1) 대신 중앙의 좁은 영역(CURSOR_ACTIVE_MARGIN~1-MARGIN)만
            # 화면 전체로 매핑해서, 손을 조금만 움직여도 커서가 크게 움직이도록 감도를 높임
            active_x = (center_x - CURSOR_ACTIVE_MARGIN) / (1 - 2 * CURSOR_ACTIVE_MARGIN)
            active_y = (center_y - CURSOR_ACTIVE_MARGIN) / (1 - 2 * CURSOR_ACTIVE_MARGIN)
            active_x = min(max(active_x, 0.0), 1.0)  # 화면 밖으로 안 나가게 클램프
            active_y = min(max(active_y, 0.0), 1.0)

            # 랜드마크 좌표가 프레임 단위로 미세하게 떨리는 걸 그대로 커서에 반영하면
            # 마우스가 계속 떨려서 못 쓰는 수준이 되므로, EMA(지수이동평균)로 부드럽게 함
            raw_cursor_x = active_x * self._screen_w
            raw_cursor_y = active_y * self._screen_h
            if self._cursor_smooth_x is None:
                self._cursor_smooth_x, self._cursor_smooth_y = raw_cursor_x, raw_cursor_y
            else:
                self._cursor_smooth_x = (self._cursor_smooth_x * CURSOR_SMOOTHING +
                                          raw_cursor_x * (1 - CURSOR_SMOOTHING))
                self._cursor_smooth_y = (self._cursor_smooth_y * CURSOR_SMOOTHING +
                                          raw_cursor_y * (1 - CURSOR_SMOOTHING))
            windowcontrol.move_cursor_to(self._cursor_smooth_x, self._cursor_smooth_y)

            # 시각화: 커서 기준점(손바닥 중심)을 매 프레임 표시
            cx, cy = int(center_x * w), int(center_y * h)
            cv.circle(frame_vis, (cx, cy), 5, (255, 200, 0), -1)

            # [수정] 디버그 로그로 확인해보니 "손날 전환 중"만 문제가 아니라, 손이 "손등"
            # 방향을 보고 있을 때도 카메라 2D 투영상 손가락들이 겹쳐 보이면서 엄지-중지
            # 거리가 우연히 가까워지는 문제가 있었음(손등→손날→손바닥 회전 전체 구간에서
            # 발생). 그래서 "edge만 제외"가 아니라 "정면(front)일 때만 허용"으로 강화함.
            # 휠 자세(약지/새끼만 말기)는 엄지 위치와 무관해서 배타 처리를 안 함
            if orientation == "front":
                # [수정] 핀치(엄지+검지) = 실제 마우스 왼쪽 버튼. SetWindowPos로 직접 창을 옮기던
                # 예전 방식 대신 진짜 마우스 다운/업 이벤트를 보내서 OS가 알아서 처리하게 함
                # (제목표시줄을 잡으면 창 드래그, 아이콘/버튼 위면 클릭 등 자연스럽게 다 됨)
                pinch_dist = ((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2) ** 0.5
                px, py = int((thumb_tip.x + index_tip.x) / 2.0 * w), int((thumb_tip.y + index_tip.y) / 2.0 * h)
                pinch_color = (0, 165, 255) if self._left_button_down else (0, 255, 255)
                cv.circle(frame_vis, (px, py), 10, pinch_color, 2)

                if not self._left_button_down and pinch_dist < PINCH_ON_DIST:
                    windowcontrol.mouse_left_down()
                    self._left_button_down = True
                    self._hand_display_text = ("LEFT CLICK: DOWN", (0, 255, 255))
                elif self._left_button_down and pinch_dist > PINCH_OFF_DIST:
                    windowcontrol.mouse_left_up()
                    self._left_button_down = False
                    self._hand_display_text = ("LEFT CLICK: UP", (0, 200, 0))

                # [수정] 엄지를 손바닥 중심 쪽으로 넣으면 우클릭(넣는 순간 1회만 발동 - rising edge)
                thumb_center_dist = ((thumb_tip.x - center_x) ** 2 + (thumb_tip.y - center_y) ** 2) ** 0.5
                thumb_tucked_now = thumb_center_dist < THUMB_TUCK_DIST
                if thumb_tucked_now and not self._thumb_tucked:
                    windowcontrol.mouse_right_click()
                    right_click_event = True
                    self._hand_display_text = ("RIGHT CLICK", (255, 0, 255))
                self._thumb_tucked = thumb_tucked_now

                # [추가] 커스텀 명령 슬롯 1 - 엄지+중지 붙이기 (붙는 순간 1회만 발동 - rising edge)
                # 실제 동작은 여기서 정하지 않고 main.py가 commandmodule을 통해 결정함
                # (commands.json에 "pinch_middle"로 등록된 명령이 있으면 실행, 없으면 아무 것도 안 함)
                # [수정] ON/OFF 이중 임계값 + 최소 유지시간(PINCH_MIDDLE_HOLD_SEC) 추가.
                # 손을 빠르게 돌리는 도중 순간적으로 거리가 가까워지는 경우와, 진짜로 붙여서
                # 유지하는 경우를 구분하기 위함 - 이미 붙어서 활성화된 상태는 즉시 반응하되
                # (OFF_DIST 초과해야 해제), 새로 붙는 판정만 HOLD_SEC 동안 유지돼야 확정
                thumb_middle_dist = ((thumb_tip.x - middle_tip.x) ** 2 + (thumb_tip.y - middle_tip.y) ** 2) ** 0.5
                if self._pinch_middle_active:
                    if thumb_middle_dist > PINCH_MIDDLE_OFF_DIST:
                        self._pinch_middle_active = False
                else:
                    if thumb_middle_dist < PINCH_MIDDLE_ON_DIST:
                        if self._pinch_middle_candidate_since is None:
                            self._pinch_middle_candidate_since = time.time()
                        elif time.time() - self._pinch_middle_candidate_since >= PINCH_MIDDLE_HOLD_SEC:
                            self._pinch_middle_active = True
                            pinch_middle_event = True
                            self._hand_display_text = ("PINCH: MIDDLE", (255, 165, 0))
                            self._debug_dump("pinch_middle 발동")  # [추가] 발동 직전 프레임들 기록을 파일로 남김
                            self._pinch_middle_candidate_since = None
                    else:
                        self._pinch_middle_candidate_since = None  # 멀어졌으니 후보 취소
            else:
                # [추가] 손날 자세 도중엔 클릭류 판정을 건너뛰지만, 혹시 좌클릭
                # 버튼이 눌린 채로 손날 자세에 들어갔다면 눌린 채로 고정되지 않게 놓아줌 (안전장치)
                # [수정] _thumb_tucked/_pinch_middle_active는 여기서 강제로 False로 리셋하지
                # 않음 - 손날 전환 중 near_edge가 프레임 사이에서 깜빡이면, 리셋된 직후
                # (2D 투영상 엄지-중지가 우연히 가까워 보이는) 손날 회전 특성 때문에 바로
                # 다시 "새로 붙었다"고 오판정되는 문제가 있었음. 그냥 마지막 상태를 그대로
                # 유지해서 진짜로 떨어졌을 때만 다시 판정되게 함
                if self._left_button_down:
                    windowcontrol.mouse_left_up()
                    self._left_button_down = False
                # [추가] 후보 타이머는 리셋 - front가 아닌 동안 흐른 시간이 그대로 남아있으면
                # front로 복귀하자마자 HOLD_SEC을 이미 채운 걸로 오판정될 수 있음
                self._pinch_middle_candidate_since = None

            # [수정] 휠 스크롤 자세 (약지+새끼 말기 = 레디). 중지 손끝 하나만 독립적으로
            # 움직이는 대신, 스와이프에서 이미 검증된 "손바닥 중심점(center_x/center_y)을
            # 손 전체로 위/아래로 움직이기" 방식을 재사용. 자세가 시작된 순간의 손바닥
            # 중심 y좌표를 기준점으로 기억해뒀다가, 기준점보다 위로 움직이면 휠 업,
            # 아래로 움직이면 휠 다운을 일정 간격으로 반복 발생
            # [수정] swipe_up/down처럼 commandmodule을 거치게 했다가 되돌림 - 휠은 손을
            # 유지하는 동안 계속 반복 발생하는 이벤트라, 여기에 커스텀 명령을 걸면 스크롤
            # 하는 몇 초 동안 그 명령이 초당 여러 번 반복 실행되어버려 실용성이 없음.
            # 그래서 다시 여기서 직접 스크롤을 실행함(휠 자체는 커스터마이징 대상에서 제외)
            if wheel_pose:
                if self._wheel_baseline_y is None:
                    self._wheel_baseline_y = center_y
                    self._hand_display_text = ("WHEEL: READY", (200, 200, 0))
                else:
                    now_wheel = time.time()
                    if now_wheel - self._last_wheel_tick_time > WHEEL_TICK_INTERVAL_SEC:
                        if center_y < self._wheel_baseline_y - WHEEL_HAND_MARGIN:
                            windowcontrol.mouse_scroll(1)
                            self._last_wheel_tick_time = now_wheel
                            self._hand_display_text = ("WHEEL UP", (0, 255, 255))
                        elif center_y > self._wheel_baseline_y + WHEEL_HAND_MARGIN:
                            windowcontrol.mouse_scroll(-1)
                            self._last_wheel_tick_time = now_wheel
                            self._hand_display_text = ("WHEEL DOWN", (255, 100, 0))
                        else:
                            self._hand_display_text = ("WHEEL: READY", (200, 200, 0))
            else:
                self._wheel_baseline_y = None

            # [수정] 왼쪽 버튼을 누르고 있는(드래그) 동안이나 휠 스크롤 자세일 때는
            # 스와이프/손날 제스처를 판정하지 않음 - 휠 자세로 손을 빠르게 움직이면
            # 스와이프까지 같이 발동해서 창이 최소화/복원되는 문제가 있었음
            # center_x/center_y는 위에서 커서 매핑용으로 이미 계산해둔 걸 그대로 재사용
            if not self._left_button_down and not wheel_pose:
                now = time.time()
                self._hand_y_history.append((now, center_y))

                # [수정] SWIPE_WINDOW_SEC보다 오래된 기록은 버림 (프레임수 대신 시간 기준 윈도우)
                while (self._hand_y_history and
                       now - self._hand_y_history[0][0] > SWIPE_WINDOW_SEC):
                    self._hand_y_history.popleft()

                oldest_t, oldest_y = self._hand_y_history[0]
                if now - oldest_t >= SWIPE_WINDOW_SEC * 0.8:  # 윈도우가 충분히 채워졌을 때만 판정
                    delta = center_y - oldest_y
                    if now - self._last_swipe_time > SWIPE_COOLDOWN_SEC:
                        if delta > SWIPE_Y_THRESHOLD:
                            swipe_down = True          # 기준점이 아래로 이동 = 쓸어내리기
                            self._last_swipe_time = now
                            self._hand_y_history.clear()
                        elif delta < -SWIPE_Y_THRESHOLD:
                            swipe_up = True             # 기준점이 위로 이동 = 쓸어올리기
                            self._last_swipe_time = now
                            self._hand_y_history.clear()

                # orientation은 위에서 이미 계산해둔 걸 재사용 (클릭류 제스처 게이팅에도 씀)

                # 시각화: 방향 텍스트(한글) - 중심점은 위에서 이미 매 프레임 그려둠
                orientation_label = ORIENTATION_KO.get(orientation, "판정 불가")
                put_korean_text(frame_vis, f"손 방향: {orientation_label}", (10, 145),
                                 font_size=24, color=(255, 200, 0))

                if swipe_up:
                    self._hand_display_text = ("SWIPE UP", (255, 0, 0))  # [추가]
                if swipe_down:
                    self._hand_display_text = ("SWIPE DOWN", (0, 0, 255))  # [추가]

                # [수정] 스와이프 → 창 제어. 손날+다운은 여기서 바로 닫지 않고
                # close_request 이벤트만 알려서, 예/아니오(깜빡임/박수) 응답으로
                # 최종 행동(닫기/취소)은 main.py(통합 스크립트)에서 결정하게 함
                # [수정] swipe_up/swipe_down(손날 제외) 자체의 실행(minimize/restore)도
                # main.py에서 commandmodule을 거쳐 처리하도록 옮김 - 사용자가 나중에
                # 이 제스처에 다른 명령을 등록해도 여기서 하드코딩된 동작이 그대로
                # 실행되어버리는 걸 막기 위함 (인식/실행 계층 분리 유지)
                # [수정] "정확히 이 프레임"에 손날이어야만 인정하면, 손을 빠르게 내리치는
                # 동작 중 프레임 사이에서 각도가 흔들려 손날 판정을 놓치기 쉬움. 최근
                # EDGE_RECENT_SEC 안에 손날이 한 번이라도 잡혔으면 인정해서 여유를 줌
                if swipe_down:
                    if orientation == "edge" or time.time() - self._last_edge_time < EDGE_RECENT_SEC:
                        close_request = True
                        self._hand_display_text = ("CLOSE? say YES/NO", (0, 0, 255))
            else:
                self._hand_y_history.clear()  # 왼쪽 버튼 누름(드래그)/휠 자세 중엔 스와이프 히스토리 오염 방지
        else:
            self._hand_y_history.clear()  # 손이 사라지면 히스토리 초기화
            self._thumb_tucked = False    # [수정] 우클릭 rising edge 상태도 리셋
            self._pinch_middle_active = False  # [추가] 커스텀 슬롯 1 rising edge 상태도 리셋
            self._pinch_middle_candidate_since = None
            self._last_orientation = None  # [추가] 손 방향 히스테리시스 상태도 리셋
            self._thumb_updown_candidate       = None  # [추가] 엄지척/다운 유지 시간 추적도 리셋
            self._thumb_updown_candidate_since = None
            self._wheel_baseline_y = None  # [수정] 휠 스크롤 기준점도 리셋
            if self._left_button_down:    # [추가] 손이 사라졌는데 버튼이 눌린 채로 고정되지 않게 놓아줌
                windowcontrol.mouse_left_up()
                self._left_button_down = False
            # [추가] 손이 사라졌다 다시 나타나면 예전 위치에서 스무딩되며 슬라이드해오는
            # 대신 새 위치로 바로 스냅하도록 커서 스무딩 상태 초기화
            self._cursor_smooth_x = None
            self._cursor_smooth_y = None

        # [추가] 마지막으로 인식된 스와이프/닫기/클릭 텍스트를 계속 표시
        if self._hand_display_text is not None:
            text, color = self._hand_display_text
            cv.putText(frame_vis, text, (10, 120),
                       cv.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        with self._lock:
            self.result["hand_features"]    = features
            self.result["hand_side"]        = hand_side
            self.result["hand_detected"]    = detected
            self.result["swipe_up"]         = swipe_up    # [추가]
            self.result["swipe_down"]       = swipe_down  # [추가]
            self.result["hand_orientation"] = orientation  # [추가]
            self.result["close_request"]    = close_request  # [수정] 손날+다운 → 닫기 확인 요청
            self.result["hands_together"]   = hands_together  # [추가] 양손 겹침 (박수 보조 판정용)
            self.result["left_click"]       = self._left_button_down  # [추가] 핀치로 왼쪽 버튼을 누르고 있는지
            self.result["right_click"]      = right_click_event  # [추가] 이번 프레임에 우클릭 발생했는지
            self.result["thumbs_up"]        = thumbs_up    # [추가] 주먹+엄지 위 = 예
            self.result["thumbs_down"]      = thumbs_down  # [추가] 주먹+엄지 아래 = 아니오
            self.result["pinch_middle"]     = pinch_middle_event  # [추가] 커스텀 슬롯 1(엄지+중지)

    # ── 내부: 눈 깜빡임 처리 ─────────────────────────────
    # [비활성화] 눈 관련 기능은 손 쪽 기능이 어느 정도 정리될 때까지 뒤로 미룸.
    # 예/아니오도 손 제스처로 옮길 예정이라 블링크 판정은 통째로 꺼두고 EAR만 확인.
    def _process_blink(self, frame_rgb, frame_vis):
        h, w  = frame_vis.shape[:2]
        res   = self.face_mesh.process(frame_rgb)
        blink = False
        long_blink = False
        double_blink = False
        eye_closed = False  # 지금 눈을 감고 있는지 (실시간)
        ear   = 0.0

        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            left_ear  = get_ear(lm, LEFT_EYE,  w, h)
            right_ear = get_ear(lm, RIGHT_EYE, w, h)
            ear       = (left_ear + right_ear) / 2.0
            eye_closed = ear < EAR_THRESHOLD  # 블링크 판정 없이 EAR로만 실시간 갱신

            # 눈 인식 확인용 - 눈 랜드마크 위치에 점 표시
            for idx in LEFT_EYE + RIGHT_EYE:
                px, py = int(lm[idx].x * w), int(lm[idx].y * h)
                cv.circle(frame_vis, (px, py), 2, (0, 255, 255), -1)

            # if (self._last_blink_time is not None and
            #         time.time() - self._last_blink_time > DOUBLE_BLINK_WINDOW_SEC):
            #     blink = True
            #     self._last_blink_time = None
            #
            # if ear < EAR_THRESHOLD:
            #     if self._eye_close_start is None:
            #         self._eye_close_start = time.time()
            #
            #     close_duration = time.time() - self._eye_close_start
            #     if close_duration >= LONG_BLINK_SEC:
            #         long_blink = True
            #         if not self._long_blink_triggered:
            #             windowcontrol.turn_off_monitor()
            #             self._long_blink_triggered = True
            #
            #     if close_duration >= EYE_BLINK_IGNORE_SEC:
            #         self._eye_streak_start     = None
            #         self._eye_streak_triggered = False
            # else:
            #     if self._eye_close_start is not None:
            #         close_duration = time.time() - self._eye_close_start
            #         if MIN_BLINK_SEC <= close_duration < LONG_BLINK_SEC:
            #             now = time.time()
            #             if (self._last_blink_time is not None and
            #                     now - self._last_blink_time <= DOUBLE_BLINK_WINDOW_SEC):
            #                 double_blink = True
            #                 self._last_blink_time = None
            #             else:
            #                 self._last_blink_time = now
            #     self._eye_close_start      = None
            #     self._long_blink_triggered = False
            #
            #     if self._eye_streak_start is None:
            #         self._eye_streak_start = time.time()
            #     streak_elapsed = time.time() - self._eye_streak_start
            #     if streak_elapsed >= EYE_STREAK_SEC and not self._eye_streak_triggered:
            #         windowcontrol.turn_on_monitor()
            #         self._eye_streak_triggered = True
            #     elif not self._eye_streak_triggered:
            #         cv.putText(frame_vis, f"EYE STREAK {streak_elapsed:.1f}/{EYE_STREAK_SEC:.0f}s",
            #                    (10, 210), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)

            # EAR 시각화 (이건 계속 켜둠 - 눈 움직임 확인용)
            color = (0, 0, 255) if ear < EAR_THRESHOLD else (0, 255, 0)
            cv.putText(frame_vis, f"EAR:{ear:.2f}", (10, 60),
                       cv.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            # if blink:
            #     self._eye_display_text = ("BLINK!", (0, 0, 255))
            # if long_blink:
            #     self._eye_display_text = ("LONG BLINK!", (0, 165, 255))
            # if double_blink:
            #     self._eye_display_text = ("DOUBLE BLINK!", (255, 0, 255))
        # else:
        #     self._eye_streak_start     = None
        #     self._eye_streak_triggered = False

        # [비활성화] 블링크 텍스트 표시 - 위 판정 자체를 꺼뒀으므로 함께 꺼둠
        # if self._eye_display_text is not None:
        #     text, color = self._eye_display_text
        #     cv.putText(frame_vis, text, (10, 90),
        #                cv.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        with self._lock:
            self.result["blink"]        = blink
            self.result["long_blink"]   = long_blink
            self.result["double_blink"] = double_blink
            self.result["eye_closed"]   = eye_closed
            self.result["ear"]          = ear

    # ── 메인 루프 ─────────────────────────────────────────
    def run(self):
        """카메라 루프 실행 (메인 스레드 or 별도 스레드에서 호출)"""
        cap = cv.VideoCapture(self.camera_id, cv.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv.VideoCapture(self.camera_id)
        if not cap.isOpened():
            print("[CameraModule] 카메라를 열 수 없습니다.")
            return

        self.running  = True
        prev_time     = time.time()

        print("[CameraModule] 시작 - 'q' 키로 종료")

        while self.running:
            ret, frame = cap.read()
            if not ret:
                print("[CameraModule] 프레임 획득 실패")
                break

            # 좌우반전 (거울 모드)
            frame = cv.flip(frame, 1)
            frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

            # 손동작 처리
            self._process_hands(frame_rgb, frame)

            # 눈 깜빡임 처리
            self._process_blink(frame_rgb, frame)

            # FPS 계산 및 표시
            curr_time = time.time()
            fps = 1 / max(curr_time - prev_time, 1e-6)
            prev_time = curr_time
            with self._lock:
                self.result["fps"] = fps
            cv.putText(frame, f"FPS:{fps:.1f}", (10, 30),
                       cv.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,100), 2)

            if self.show_window:
                cv.imshow("AI Assistant - Camera", frame)
                if cv.waitKey(1) & 0xFF == ord('q'):
                    break

        cap.release()
        cv.destroyAllWindows()
        self.running = False
        print("[CameraModule] 종료")

    def get_result(self):
        """현재 감지 결과 반환 (스레드 안전)"""
        with self._lock:
            return dict(self.result)

    def stop(self):
        self.running = False


# ── 테스트용 실행 ─────────────────────────────────────────
if __name__ == "__main__":
    cam = CameraModule(camera_id=0, show_window=True)

    # 별도 스레드로 실행하는 예시
    # t = threading.Thread(target=cam.run, daemon=True)
    # t.start()

    # 또는 직접 실행 (블로킹)
    cam.run()