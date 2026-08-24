# ============================================================
#  개인 AI 비서 - 카메라 입력 모듈
#  SignBridge 기반으로 추출 및 정리
#  감지 대상: 손동작 / 눈 깜빡임 / 표정(기본)
# ============================================================

import cv2 as cv
import mediapipe as mp
import numpy as np
import time
import threading
from collections import deque  # [추가] 손 위치 이동(스와이프) 추적용
import windowcontrol  # [추가] 스와이프/손날 제스처로 창 제어

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
LONG_BLINK_SEC = 2    # 이 시간 이상 감기면 '길게 감기'로 판단

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
EDGE_CROSS_THRESHOLD = 0.01  # 이 값보다 작으면 손날(옆면)로 판정 - 실측 후 조정 필요

# [추가] 양손이 겹쳐졌는지(박수 동작 보조 판정용) 설정
HANDS_TOGETHER_THRESHOLD = 0.15  # 두 손 중심점 사이 거리(정규화 좌표)가 이보다 작으면 겹친 것으로 판정 - 실측 후 조정 필요

# [추가] 핀치(엄지+검지 집기)로 창 드래그 설정
PINCH_ON_DIST  = 0.05  # 엄지-검지 거리(정규화 좌표)가 이보다 가까우면 "집기" 시작 - 실측 후 조정 필요
PINCH_OFF_DIST = 0.08  # 집은 상태에서 이 이상 벌어지면 "놓기" (ON보다 느슨하게 잡아 떨림으로 인한 오해제 방지)


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
def get_hand_orientation(landmarks, handedness):
    """
    손목(0) → 인덱스 MCP(5) → 새끼 MCP(17) 삼각형의 외적으로 방향 판별
    - 외적 절댓값이 작으면 손을 세운 상태(손날)
    - 그 외에는 부호로 손바닥/손등 구분
    """
    wrist     = landmarks[0]
    index_mcp = landmarks[5]
    pinky_mcp = landmarks[17]

    v1x, v1y = index_mcp.x - wrist.x, index_mcp.y - wrist.y
    v2x, v2y = pinky_mcp.x - wrist.x, pinky_mcp.y - wrist.y
    cross = v1x * v2y - v1y * v2x

    if abs(cross) < EDGE_CROSS_THRESHOLD:
        return "edge"  # 손날

    if handedness == "Right":
        return "front" if cross < 0 else "back"
    else:
        return "front" if cross > 0 else "back"


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

        # [추가] 화면에 계속 표시할 마지막 상태 텍스트 (다음 동작 인식 전까지 유지)
        self._eye_display_text  = None   # ("BLINK!" / "LONG BLINK!", color)
        self._hand_display_text = None   # ("SWIPE UP" / "SWIPE DOWN", color)

        # [추가] 핀치(엄지+검지 집기)로 창 드래그하는 기능용 상태
        self._drag_hwnd   = None          # 지금 잡고 있는 창 핸들 (없으면 None)
        self._drag_offset = (0.0, 0.0)    # 잡은 지점 - 창 좌상단 사이 오프셋 (화면 좌표계)
        self._screen_w, self._screen_h = windowcontrol.get_screen_size()  # 손 좌표 → 화면 좌표 매핑용

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
            "window_drag"    : False,  # [추가] 핀치로 창을 잡아 옮기는 중인지

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
        if chosen_landmarks is not None:
            # [추가] 핀치(엄지 4번 + 검지 8번 집기) 판정 - 화면 속 창을 잡아서 옮기는 기능
            thumb_tip = chosen_landmarks[4]
            index_tip = chosen_landmarks[8]
            pinch_dist = ((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2) ** 0.5
            pinch_x = (thumb_tip.x + index_tip.x) / 2.0
            pinch_y = (thumb_tip.y + index_tip.y) / 2.0
            # 프레임이 거울 모드로 좌우반전되어 있어(cv.flip), 정규화 좌표를 그대로 화면 좌표에
            # 곱하면 미리보기 화면에서 보이는 손 위치와 동일한 감각으로 화면을 가리키게 됨
            screen_x = pinch_x * self._screen_w
            screen_y = pinch_y * self._screen_h

            px, py = int(pinch_x * w), int(pinch_y * h)
            pinch_color = (0, 255, 255) if self._drag_hwnd is None else (0, 165, 255)
            cv.circle(frame_vis, (px, py), 10, pinch_color, 2)

            if self._drag_hwnd is None:
                if pinch_dist < PINCH_ON_DIST:
                    hwnd = windowcontrol.get_window_at_point(int(screen_x), int(screen_y))
                    if hwnd:
                        left, top, _, _ = windowcontrol.get_window_rect(hwnd)
                        self._drag_hwnd    = hwnd
                        self._drag_offset  = (screen_x - left, screen_y - top)
                        self._hand_display_text = ("WINDOW GRABBED", (0, 255, 255))
            else:
                if pinch_dist < PINCH_OFF_DIST and windowcontrol.is_window_valid(self._drag_hwnd):
                    off_x, off_y = self._drag_offset
                    windowcontrol.move_window_to(self._drag_hwnd, screen_x - off_x, screen_y - off_y)
                else:
                    self._drag_hwnd = None
                    self._hand_display_text = ("WINDOW RELEASED", (0, 200, 0))

            # [수정] 창을 드래그하는 중에는 스와이프/손날 제스처를 판정하지 않음
            # (손을 크게 움직이는 드래그 동작이 스와이프로 오인식되는 것 방지)
            if self._drag_hwnd is None:
                center_x = float(np.mean([chosen_landmarks[i].x for i in HAND_CENTER_INDICES]))
                center_y = float(np.mean([chosen_landmarks[i].y for i in HAND_CENTER_INDICES]))
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

                # [추가] 손바닥/손등/손날 판별
                orientation = get_hand_orientation(chosen_landmarks, hand_side)

                # 시각화: 손 중심점 + 방향 텍스트는 매 프레임
                cx, cy = int(center_x * w), int(center_y * h)
                cv.circle(frame_vis, (cx, cy), 5, (255, 200, 0), -1)
                cv.putText(frame_vis, f"hand:{orientation}", (10, 150),
                           cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)

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
                if swipe_down:
                    if orientation == "edge":
                        close_request = True
                        self._hand_display_text = ("CLOSE? say YES/NO", (0, 0, 255))
            else:
                self._hand_y_history.clear()  # 드래그 중엔 스와이프 히스토리 오염 방지
        else:
            self._hand_y_history.clear()  # 손이 사라지면 히스토리 초기화
            self._drag_hwnd = None        # [추가] 손이 사라지면 드래그도 해제

        # [추가] 마지막으로 인식된 스와이프/닫기 텍스트를 계속 표시
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
            self.result["window_drag"]      = self._drag_hwnd is not None  # [추가] 핀치로 창을 잡아 옮기는 중인지

    # ── 내부: 눈 깜빡임 처리 ─────────────────────────────
    def _process_blink(self, frame_rgb, frame_vis):
        h, w  = frame_vis.shape[:2]
        res   = self.face_mesh.process(frame_rgb)
        blink = False
        long_blink = False
        double_blink = False  # [추가]
        eye_closed = False  # [수정] 지금 눈을 감고 있는지 실시간 상태 추가
        ear   = 0.0

        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            left_ear  = get_ear(lm, LEFT_EYE,  w, h)
            right_ear = get_ear(lm, RIGHT_EYE, w, h)
            ear       = (left_ear + right_ear) / 2.0

            # [임시] 눈 인식 확인용 - 눈 랜드마크 위치에 점 표시
            for idx in LEFT_EYE + RIGHT_EYE:
                px, py = int(lm[idx].x * w), int(lm[idx].y * h)
                cv.circle(frame_vis, (px, py), 2, (0, 255, 255), -1)

            # [수정] 더블 블링크로 이어지지 않고 대기 시간(DOUBLE_BLINK_WINDOW_SEC)이 지나면
            # 그제서야 단일 블링크로 확정. (매 프레임 확인 - 눈을 뜨고 있는 동안에도 시간초과를 감지해야 함)
            # 이전엔 첫 깜빡임이 눈을 뜨는 즉시 blink=True로 확정돼서, 더블 블링크를 하려고 해도
            # 첫 번째 깜빡임에서 바로 '예'로 인식되어 창닫기 확인 중 의도치 않게 창이 닫히는 문제가 있었음.
            if (self._last_blink_time is not None and
                    time.time() - self._last_blink_time > DOUBLE_BLINK_WINDOW_SEC):
                blink = True
                self._last_blink_time = None

            if ear < EAR_THRESHOLD:
                # 눈 감기 시작 시간 기록
                if self._eye_close_start is None:
                    self._eye_close_start = time.time()
                eye_closed = True  # [수정] 감고 있는 동안 매 프레임 True로 표시

                # [수정] 눈을 다시 뜨기 전에도 즉시 long_blink 판정
                # (기존엔 눈을 떠야만 길게 감았는지 알 수 있어서 반응이 느렸음)
                close_duration = time.time() - self._eye_close_start
                if close_duration >= LONG_BLINK_SEC:
                    long_blink = True  # [수정] 감고 있는 도중 바로 켜짐
                    # [추가] 롱블링크 1회당 한 번만 화면 끄기 실행
                    if not self._long_blink_triggered:
                        windowcontrol.turn_off_monitor()
                        self._long_blink_triggered = True

                # [추가] 짧은 자연스러운 깜빡임(0.4초 미만)은 무시하고,
                # 그보다 길게 감으면 의도적인 동작으로 보고 눈 인식 스트릭을 끊음
                if close_duration >= EYE_BLINK_IGNORE_SEC:
                    self._eye_streak_start     = None
                    self._eye_streak_triggered = False
            else:
                # [수정] 프레임수(BLINK_FRAMES) 대신 시간(MIN_BLINK_SEC) 기준으로 노이즈 필터링
                # → FPS가 20~40으로 변해도 동일하게 동작함
                if self._eye_close_start is not None:
                    close_duration = time.time() - self._eye_close_start
                    # long_blink는 위에서 이미 실시간으로 처리했으므로 여기서는 짧은 깜빡임만 판정
                    if MIN_BLINK_SEC <= close_duration < LONG_BLINK_SEC:
                        # [수정] 짧은 깜빡임이 오면 바로 blink=True로 확정하지 않고 일단 "대기"만 함
                        # (단일인지 더블의 첫 번째인지는 아직 알 수 없음 - 위쪽의 시간초과 체크에서 확정됨)
                        now = time.time()
                        if (self._last_blink_time is not None and
                                now - self._last_blink_time <= DOUBLE_BLINK_WINDOW_SEC):
                            double_blink = True   # 대기 중이던 첫 깜빡임 + 지금 이 깜빡임 = 더블 확정
                            self._last_blink_time = None
                        else:
                            self._last_blink_time = now   # 대기 시작 (다음 프레임들에서 시간초과 시 단일로 확정)
                self._eye_close_start      = None
                self._long_blink_triggered = False  # [추가] 눈을 떴으니 다음 롱블링크는 다시 트리거 가능

                # [추가] 눈 인식 스트릭 진행 - 5초 이상 계속 인식되면 화면 켜기
                if self._eye_streak_start is None:
                    self._eye_streak_start = time.time()
                streak_elapsed = time.time() - self._eye_streak_start
                if streak_elapsed >= EYE_STREAK_SEC and not self._eye_streak_triggered:
                    windowcontrol.turn_on_monitor()
                    self._eye_streak_triggered = True
                elif not self._eye_streak_triggered:
                    cv.putText(frame_vis, f"EYE STREAK {streak_elapsed:.1f}/{EYE_STREAK_SEC:.0f}s",
                               (10, 210), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)

            # EAR 시각화
            color = (0, 0, 255) if ear < EAR_THRESHOLD else (0, 255, 0)
            cv.putText(frame_vis, f"EAR:{ear:.2f}", (10, 60),
                       cv.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            if blink:
                self._eye_display_text = ("BLINK!", (0, 0, 255))  # [추가]
            if long_blink:
                self._eye_display_text = ("LONG BLINK!", (0, 165, 255))  # [추가]
            if double_blink:
                self._eye_display_text = ("DOUBLE BLINK!", (255, 0, 255))  # [추가]
        else:
            # [추가] 얼굴이 안 보이면 눈 인식 스트릭도 신뢰할 수 없으니 리셋
            self._eye_streak_start     = None
            self._eye_streak_triggered = False

        # [추가] 마지막으로 인식된 깜빡임 텍스트를 다음 동작 전까지 계속 표시
        if self._eye_display_text is not None:
            text, color = self._eye_display_text
            cv.putText(frame_vis, text, (10, 90),
                       cv.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        with self._lock:
            self.result["blink"]        = blink
            self.result["long_blink"]   = long_blink
            self.result["double_blink"] = double_blink  # [추가]
            self.result["eye_closed"]   = eye_closed  # [수정] 실시간 눈감김 상태 저장
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