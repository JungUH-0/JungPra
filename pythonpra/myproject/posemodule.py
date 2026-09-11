# ============================================================
#  개인 AI 비서 - 전신 포즈 입력 모듈
#  MediaPipe Pose(BlazePose, 33개 랜드마크)로 상체 자세를 인식한다.
#
#  [카메라 소유권] 카메라는 하나뿐이라 두 모듈이 동시에 VideoCapture를 열 수 없다.
#  그래서 이 모듈은 카메라를 직접 열지 않고, cameramodule이 읽어온 프레임을
#  process()로 넘겨받아 처리한다. (cameramodule이 포즈 모드일 때만 호출함)
#
#  [현재 범위] 랜드마크 검출 + 특징 벡터 추출까지만 구현. 자세 분류(학습된 모델)는
#  아직 없음 - 손 제스처 때와 마찬가지로 "먼저 인식되는지 확인 → 그다음 학습" 순서.
#
#  [모드 전환] 포즈 모드에서도 손 모드로 돌아가야 하는데, 이때는 mediapipe 손 추적이
#  꺼져 있으므로 포즈의 손목 좌표(15, 16)로 양손 모임을 판정한다. 어깨 너비로 나눠서
#  카메라와의 거리에 무관하게 동작하게 함.
#
#  [좌우 주의] cameramodule이 프레임을 거울 모드로 뒤집어서(cv.flip) 넘겨주기 때문에,
#  여기서 말하는 mediapipe의 "왼쪽"(LEFT_*)은 화면 기준이며 실제로는 사용자의
#  오른쪽이다. 분류 자체에는 문제가 없지만(항상 일관되게 뒤집혀 있으므로), 나중에
#  자세에 "오른팔 들기" 같은 이름을 붙일 때 좌우가 반대라는 점을 기억해야 한다.
# ============================================================

import time
import threading
import numpy as np
import cv2 as cv
import mediapipe as mp
# 한글 텍스트 표시 헬퍼는 cameramodule에 있는 것을 그대로 재사용 (cv.putText는 한글 불가).
# cameramodule은 posemodule을 import하지 않으므로 순환 import가 생기지 않는다.
from cameramodule import put_korean_text

mp_pose    = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# ── 사용할 랜드마크 (BlazePose 33개 중 팔 + 머리) ───────────
# [수정] 명령을 "팔 동작 + 머리 동작"으로 주기로 해서 구성을 바꿈.
#  - 엉덩이(23, 24) 제거: 책상 앞에 앉으면 가려지거나 화면 밖이라 계속 pose skip이 났음
#  - 귀(7, 8) 추가: 머리 방향(돌리기/기울이기)을 판정하려면 필요하고,
#                   웹캠 앞에서는 거의 항상 보이는 부위라 안정적임
# [확장] 나중에 전신까지 쓰려면 다리를 추가하면 됨:
#   23, 24 엉덩이 / 25, 26 무릎 / 27, 28 발목 / 29, 30 뒤꿈치 / 31, 32 발끝
# 특징 벡터 차원과 이후 수집/학습 스크립트는 이 목록을 따라가므로 여기만 고치면 된다.
UPPER_BODY_KEYPOINTS = [
    0,       # 코
    7, 8,    # 귀 (머리 방향)
    11, 12,  # 어깨 (정규화 기준)
    13, 14,  # 팔꿈치
    15, 16,  # 손목
]

# [추가] 이 관절들이 안 보이면 팔 자세 자체를 판단할 수 없으므로 프레임을 버린다.
# 반대로 머리 쪽(코·귀)은 안 보여도 팔 동작은 판정할 수 있으므로 필수에서 뺐다.
REQUIRED_KEYPOINTS = [11, 12, 13, 14, 15, 16]  # 어깨·팔꿈치·손목

# 정규화 기준으로 쓰는 랜드마크 (양 어깨)
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
# 양손 모임(모드 전환) 판정에 쓰는 랜드마크 (양 손목)
LEFT_WRIST, RIGHT_WRIST = 15, 16
# 팔꿈치 각도 계산용 (어깨 - 팔꿈치 - 손목)
LEFT_ELBOW, RIGHT_ELBOW = 13, 14
# 머리 방향 계산용
NOSE, LEFT_EAR, RIGHT_EAR = 0, 7, 8

# ── 판정 설정 ─────────────────────────────────────────────
# 선택한 랜드마크가 이 값보다 잘 안 보이면(가려짐/화면 밖) 그 프레임은 버림.
# mediapipe가 안 보이는 관절도 좌표를 "추측해서" 내놓기 때문에, 이걸 안 걸러내면
# 쓰레기 값이 특징 벡터에 그대로 섞여 들어간다.
MIN_VISIBILITY = 0.5

# 양 손목 사이 거리가 어깨 너비의 이 비율보다 가까우면 "양손 모임"으로 판정.
# 고정 좌표값 대신 어깨 너비로 나눈 비율을 쓰는 이유는, 사람이 카메라에서 멀어지면
# 화면상 거리가 전부 작아져서 고정값 기준은 무조건 "가깝다"고 나오기 때문.
HANDS_TOGETHER_SHOULDER_RATIO = 0.5

MIN_SHOULDER_WIDTH = 1e-6  # 0으로 나누기 방지

# [추가] 진단용 - 팔꿈치 각도/머리 방향/손목 위치가 실제 동작에서 어떻게 움직이는지
# 파일로 남겨서 나중에 확인한다. (어떤 자세가 값으로 잘 구분되는지 판단하는 근거)
# 매 프레임 남기면 파일이 너무 커지므로 일정 간격으로만 기록한다.
DEBUG_LOG_ENABLED  = True
DEBUG_LOG_PATH     = "debug_pose.txt"
DEBUG_LOG_INTERVAL = 0.3  # 초

# 특징 벡터에서 특정 랜드마크의 (x, y) 위치를 찾기 위한 표.
# UPPER_BODY_KEYPOINTS 순서대로 좌표가 2개씩 들어가므로, 목록을 바꿔도 자동으로 맞춰진다.
_KP_FEATURE_INDEX = {kp: i * 2 for i, kp in enumerate(UPPER_BODY_KEYPOINTS)}


def _keypoint_feature(features, kp):
    """특징 벡터에서 해당 랜드마크의 정규화된 (x, y)를 꺼냄"""
    i = _KP_FEATURE_INDEX[kp]
    return features[i], features[i + 1]


def get_bounding_box(landmarks, frame_w, frame_h, padding=0.06):
    """
    [추가] 랜드마크들을 감싸는 사각형(박스)을 계산.
    MediaPipe Pose는 YOLO와 달리 박스를 직접 주지 않기 때문에(랜드마크만 출력),
    우리가 쓰는 관절들의 좌표 min/max로 직접 만든다.
    padding은 박스가 몸에 너무 딱 붙지 않게 하는 여백 (프레임 크기 대비 비율).
    반환값: (x1, y1, x2, y2) 픽셀 좌표 또는 None
    """
    xs, ys = [], []
    for idx in UPPER_BODY_KEYPOINTS:
        lm = landmarks[idx]
        if lm.visibility < MIN_VISIBILITY:
            continue
        xs.append(lm.x)
        ys.append(lm.y)

    if not xs:
        return None

    pad_x, pad_y = padding, padding
    x1 = int(max(0.0, min(xs) - pad_x) * frame_w)
    x2 = int(min(1.0, max(xs) + pad_x) * frame_w)
    y1 = int(max(0.0, min(ys) - pad_y) * frame_h)
    y2 = int(min(1.0, max(ys) + pad_y) * frame_h)
    return x1, y1, x2, y2


def _joint_angle(a, b, c):
    """
    b를 꼭짓점으로 하는 a-b-c 사잇각을 0~1로 정규화해서 반환 (0=접힘, 1=펴짐).
    손 모듈(extract_vector_angle_features)에서 관절 각도를 쓰던 방식과 같다.
    각도는 좌표와 달리 위치·크기에 전혀 영향을 받지 않아서, "팔을 굽혔나 폈나"
    같은 구분에 특히 강하다.
    """
    v1x, v1y = a.x - b.x, a.y - b.y
    v2x, v2y = c.x - b.x, c.y - b.y
    n1 = (v1x ** 2 + v1y ** 2) ** 0.5
    n2 = (v2x ** 2 + v2y ** 2) ** 0.5
    if n1 < MIN_SHOULDER_WIDTH or n2 < MIN_SHOULDER_WIDTH:
        return 0.0
    cos = (v1x * v2x + v1y * v2y) / (n1 * n2)
    return float(np.arccos(np.clip(cos, -1.0, 1.0)) / np.pi)


def _head_features(landmarks, shoulder_width):
    """
    머리 방향 특징 2개. 귀가 안 보이면 (0, 0)을 반환해서 "중립"으로 둔다.
      - 돌리기(yaw): 코가 어느 쪽 귀에 더 가까운지. 정면이면 0, 좌우로 돌리면 ±
      - 기울이기(roll): 양 귀를 잇는 선이 수평에서 얼마나 기울었는지
    둘 다 비율/각도라서 카메라와의 거리에 영향을 받지 않는다.
    """
    nose = landmarks[NOSE]
    le, re = landmarks[LEFT_EAR], landmarks[RIGHT_EAR]

    if (le.visibility < MIN_VISIBILITY or re.visibility < MIN_VISIBILITY
            or nose.visibility < MIN_VISIBILITY):
        return 0.0, 0.0

    ear_dist = ((le.x - re.x) ** 2 + (le.y - re.y) ** 2) ** 0.5
    if ear_dist < MIN_SHOULDER_WIDTH:
        return 0.0, 0.0

    d_left  = ((nose.x - le.x) ** 2 + (nose.y - le.y) ** 2) ** 0.5
    d_right = ((nose.x - re.x) ** 2 + (nose.y - re.y) ** 2) ** 0.5
    head_turn = (d_right - d_left) / ear_dist

    head_tilt = float(np.arctan2(le.y - re.y, le.x - re.x) / np.pi)
    return float(head_turn), head_tilt


def extract_pose_features(landmarks):
    """
    선택한 랜드마크들을 '몸 기준'으로 정규화한 특징 벡터로 변환.
    - 양 어깨의 중점을 원점으로 옮기고 (사람이 화면 어디에 서 있든 같은 값)
    - 어깨 너비로 나눠 스케일을 맞춤 (카메라에서 멀든 가깝든 같은 값)
    - [추가] 좌표만으로는 부족해서 팔꿈치 각도 2개 + 머리 방향 2개를 덧붙임

    구성: 좌표 9개×2 = 18 + 팔꿈치 각도 2 + 머리 방향 2 = 22차원
    반환값: (특징 numpy 배열, None) 또는 (None, 실패 사유)
    """
    ls = landmarks[LEFT_SHOULDER]
    rs = landmarks[RIGHT_SHOULDER]

    # [수정] 필수 관절(팔)만 확인. 머리 쪽은 안 보여도 팔 동작은 판정할 수 있으므로
    # 프레임을 버리지 않고, 대신 머리 특징만 중립값(0)으로 처리한다.
    for idx in REQUIRED_KEYPOINTS:
        if landmarks[idx].visibility < MIN_VISIBILITY:
            return None, f"랜드마크 {idx}가 잘 안 보임"

    origin_x = (ls.x + rs.x) / 2.0
    origin_y = (ls.y + rs.y) / 2.0
    shoulder_width = ((ls.x - rs.x) ** 2 + (ls.y - rs.y) ** 2) ** 0.5
    if shoulder_width < MIN_SHOULDER_WIDTH:
        return None, "어깨 너비를 잴 수 없음"

    features = []
    for idx in UPPER_BODY_KEYPOINTS:
        lm = landmarks[idx]
        features.append((lm.x - origin_x) / shoulder_width)
        features.append((lm.y - origin_y) / shoulder_width)

    # 팔꿈치 각도 (어깨 - 팔꿈치 - 손목)
    features.append(_joint_angle(landmarks[LEFT_SHOULDER],
                                 landmarks[LEFT_ELBOW],
                                 landmarks[LEFT_WRIST]))
    features.append(_joint_angle(landmarks[RIGHT_SHOULDER],
                                 landmarks[RIGHT_ELBOW],
                                 landmarks[RIGHT_WRIST]))

    # 머리 방향 (돌리기 / 기울이기)
    head_turn, head_tilt = _head_features(landmarks, shoulder_width)
    features.append(head_turn)
    features.append(head_tilt)

    return np.array(features, dtype=np.float32), None


def get_hands_together(landmarks):
    """
    양 손목이 모였는지 판정 (포즈 모드에서 모드 전환 신호로 사용).
    어깨 너비 대비 비율로 보기 때문에 카메라와의 거리와 무관하다.
    """
    lw, rw = landmarks[LEFT_WRIST], landmarks[RIGHT_WRIST]
    ls, rs = landmarks[LEFT_SHOULDER], landmarks[RIGHT_SHOULDER]

    if lw.visibility < MIN_VISIBILITY or rw.visibility < MIN_VISIBILITY:
        return False

    shoulder_width = ((ls.x - rs.x) ** 2 + (ls.y - rs.y) ** 2) ** 0.5
    if shoulder_width < MIN_SHOULDER_WIDTH:
        return False

    wrist_dist = ((lw.x - rw.x) ** 2 + (lw.y - rw.y) ** 2) ** 0.5
    return (wrist_dist / shoulder_width) < HANDS_TOGETHER_SHOULDER_RATIO


class PoseModule:
    """
    전신(상체) 포즈를 인식하는 모듈.
    카메라를 직접 열지 않고, cameramodule이 넘겨주는 프레임을 process()로 처리한다.
    결과는 self.result에 저장되고 외부에서 get_result()로 읽는다.
    """

    def __init__(self):
        self.pose = mp_pose.Pose(
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.result = {
            "pose_detected"  : False,  # 이번 프레임에 사람 포즈가 잡혔는지
            "pose_features"  : None,   # 정규화된 상체 특징 벡터 (수집/학습/분류용)
            "hands_together" : False,  # 양손 모임 - 포즈 모드에서 모드 전환 판정에 사용
            "pose_name"      : None,   # [예정] 학습된 분류기가 붙으면 자세 이름이 들어갈 자리
        }
        self._lock = threading.Lock()

        # [추가] 진단 로그 상태
        self._last_log_time = 0.0
        if DEBUG_LOG_ENABLED:
            try:
                with open(DEBUG_LOG_PATH, "w", encoding="utf-8") as f:
                    f.write(f"[포즈 진단 로그 시작 @ {time.strftime('%H:%M:%S')}]\n")
                    f.write(f"키포인트: {UPPER_BODY_KEYPOINTS} / 특징 {len(UPPER_BODY_KEYPOINTS)*2 + 4}차원\n")
                    f.write("elbow: 0=완전히 굽힘 1=완전히 폄 / head turn·tilt: 정면 0, 좌우 ±\n")
                    f.write("wrist: 어깨중점 기준 정규화 좌표 (y는 아래가 +, 팔 들면 -)\n")
            except OSError:
                pass

    # ── 내부: 진단 로그 기록 ──────────────────────────────
    def _debug_log(self, features, reason):
        if not DEBUG_LOG_ENABLED:
            return
        now = time.time()
        if now - self._last_log_time < DEBUG_LOG_INTERVAL:
            return
        self._last_log_time = now

        if features is None:
            line = f"{time.strftime('%H:%M:%S')} pose skip: {reason}"
        else:
            lwx, lwy = _keypoint_feature(features, LEFT_WRIST)
            rwx, rwy = _keypoint_feature(features, RIGHT_WRIST)
            line = (f"{time.strftime('%H:%M:%S')} "
                    f"elbowL={features[-4]:.2f} elbowR={features[-3]:.2f} "
                    f"headTurn={features[-2]:+.2f} headTilt={features[-1]:+.2f} "
                    f"wristL=({lwx:+.2f},{lwy:+.2f}) wristR=({rwx:+.2f},{rwy:+.2f})")

        try:
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            pass

    # ── 외부(cameramodule)에서 매 프레임 호출 ────────────────
    def process(self, frame_rgb, frame_vis):
        res = self.pose.process(frame_rgb)

        detected       = False
        features       = None
        hands_together = False

        if res.pose_landmarks:
            landmarks = res.pose_landmarks.landmark

            # 시각화 - 손 모드의 손 랜드마크 표시와 같은 방식
            mp_drawing.draw_landmarks(
                frame_vis, res.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 200, 255), thickness=2, circle_radius=3),
                mp_drawing.DrawingSpec(color=(255, 140, 0), thickness=2),
            )

            hands_together = get_hands_together(landmarks)
            features, reason = extract_pose_features(landmarks)
            detected = features is not None

            # [추가] 사람 주위에 박스 + 그 위에 자세 이름 표시.
            # MediaPipe는 YOLO처럼 박스를 직접 주지 않아서 랜드마크 min/max로 직접 계산함.
            h_frame, w_frame = frame_vis.shape[:2]
            box = get_bounding_box(landmarks, w_frame, h_frame)
            if box is not None:
                x1, y1, x2, y2 = box
                box_color = (0, 255, 100) if detected else (0, 165, 255)
                cv.rectangle(frame_vis, (x1, y1), (x2, y2), box_color, 2)

                # 분류기가 붙기 전까지는 자세 이름 자리에 상태를 대신 표시
                with self._lock:
                    pose_name = self.result["pose_name"]
                label = pose_name if pose_name else ("자세 학습 전" if detected else "인식 불가")
                # 박스가 화면 위쪽에 붙어도 글자가 잘리지 않게 위치 보정
                label_y = y1 - 10 if y1 > 30 else y2 + 28
                put_korean_text(frame_vis, label, (x1, label_y - 20),
                                font_size=24, color=box_color)

            # 특징을 못 뽑은 이유를 화면에 표시 (어느 관절이 안 보이는지 바로 알 수 있게)
            status = f"pose ok ({len(features)}d)" if detected else f"pose skip: {reason}"
            cv.putText(frame_vis, status, (10, 60),
                       cv.FONT_HERSHEY_SIMPLEX, 0.6,
                       (0, 255, 100) if detected else (0, 165, 255), 2)

            # [추가] 각도 특징이 실제로 어떻게 반응하는지 화면에서 바로 확인할 수 있게 표시.
            # (팔을 굽히면 elbow 값이 내려가고, 고개를 돌리면 turn 값이 ±로 움직임)
            if detected:
                cv.putText(frame_vis,
                           f"elbow L{features[-4]:.2f} R{features[-3]:.2f}  "
                           f"head turn{features[-2]:+.2f} tilt{features[-1]:+.2f}",
                           (10, 120), cv.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

            if hands_together:
                cv.putText(frame_vis, "HANDS TOGETHER", (10, 90),
                           cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

            # [추가] 값 변화를 파일로 남겨서 나중에 어떤 자세가 잘 구분되는지 분석
            self._debug_log(features, reason)

        with self._lock:
            self.result["pose_detected"]  = detected
            self.result["pose_features"]  = features
            self.result["hands_together"] = hands_together

    def get_result(self):
        """현재 감지 결과 반환 (스레드 안전)"""
        with self._lock:
            return dict(self.result)

    def reset(self):
        """[추가] 모드가 바뀔 때 호출 - 이전 모드의 결과가 남아있지 않게 비움"""
        with self._lock:
            self.result["pose_detected"]  = False
            self.result["pose_features"]  = None
            self.result["hands_together"] = False
            self.result["pose_name"]      = None
