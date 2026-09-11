# ============================================================
#  개인 AI 비서 - 통합 실행 스크립트
#  카메라 모듈(눈 깜빡임/손) + 오디오 모듈(박수)을 동시에 실행하고
#  깜빡임 1번 또는 박수 1번 → 예/동의
#  더블 블링크 또는 더블 클랩 → 아니오/거절
#  로 통합해서 신호를 출력한다.
#
#  손날+스와이프다운(close_request)으로 닫기 확인이 들어오면,
#  카메라 모듈이 즉시 닫지 않고 여기서 예/아니오 응답을 기다렸다가
#  최종적으로 닫기/취소를 결정한다.
# ============================================================

import time
import threading

from cameramodule import CameraModule, PINCH_SLOTS
from posemodule import PoseModule  # [추가] 전신 포즈 인식 (포즈 모드)
from audiomodule import AudioModule
from voicemodule import VoiceModule  # [추가] 웨이크워드 감지 (음성 명령의 첫 단계)
import windowcontrol
import commandmodule  # [추가] LLM으로 등록한 사용자 정의 명령 실행용

# [추가] 커스텀 명령 슬롯 이름 목록 (엄지+중지/약지/새끼) - cameramodule의 정의를 그대로 사용
PINCH_SLOT_NAMES = [name for name, _ in PINCH_SLOTS]

# [추가] 인식 모드 - 손동작 인식(cameramodule)과 전신 포즈 인식(posemodule)을 번갈아 사용.
# 둘을 동시에 돌리면 FPS가 크게 떨어지고 제스처끼리 충돌해서, 한 번에 하나만 켠다.
MODE_HAND = "hand"
MODE_POSE = "pose"
MODE_SWITCH_COOLDOWN_SEC = 1.5  # 전환 직후 같은 박수로 곧바로 되돌아가는 것 방지

# [추가] 박수 소리와 "양손 모임"이 정확히 같은 순간에 잡히길 요구하면 거의 안 맞는다:
#  - clap 신호는 약 30ms만 유지되는데 카메라는 33ms에 한 프레임이라 겹칠 확률이 낮고,
#  - 손바닥이 맞닿는 순간엔 두 손이 하나로 보여서 mediapipe가 양손 검출에 실패한다.
# 그래서 "박수 직전/직후 이 시간 안에 양손이 모여 있었으면" 인정하는 방식으로 바꿈.
# (손날+스와이프다운에서 EDGE_RECENT_SEC를 쓴 것과 같은 방식)
HANDS_TOGETHER_RECENT_SEC = 1.0

# [수정] 주변에 사람이 많아 박수를 계속 칠 수 없는 상황이라, 당분간 소리 없이
# "양손 모으기"만으로 전환한다. 조용한 환경에서 박수 조건을 다시 켜려면 True로 바꾸면 됨.
MODE_SWITCH_REQUIRE_CLAP = False
# 손이 스치듯 잠깐 겹치는 것으로 전환되지 않도록, 이 시간 이상 모으고 있어야 인정
MODE_SWITCH_HOLD_SEC = 1.0

CLOSE_CONFIRM_TIMEOUT_SEC = 5.0  # 닫기 확인 요청 후 응답 없으면 자동 취소(안전 기본값)


# [추가] 콘솔에 시각 태그를 붙여 어느 시점에 무슨 신호가 찍혔는지 구분하기 쉽게 함
def _log(tag, msg):
    print(f"[{time.strftime('%H:%M:%S')}] [{tag}] {msg}")


# [추가] 음성 명령 실행 - 별도 스레드에서 돌린다.
# LLM 응답이 늦어도 메인 루프(제스처 처리)가 멈추지 않게 하기 위함이고,
# 혹시 모를 예외가 비서 전체를 죽이지 않도록 여기서 한 번 더 감싼다.
def _run_voice_command(text):
    try:
        ok, err = commandmodule.execute_text(text)
        _log("음성", "명령 실행 완료" if ok else f"명령 실행 실패: {err}")
    except Exception as e:
        _log("음성", f"명령 실행 중 오류: {e}")


def run_assistant():
    # [추가] 포즈 모듈은 카메라를 직접 열지 않고 cameramodule이 읽은 프레임을 넘겨받음
    pose  = PoseModule()
    cam   = CameraModule(camera_id=0, show_window=True, pose_module=pose)
    audio = AudioModule()
    voice = VoiceModule()  # [추가] Whisper 모델을 여기서 로딩함 (몇 초~몇 십 초 걸릴 수 있음)

    cam_thread   = threading.Thread(target=cam.run, daemon=True)
    audio_thread = threading.Thread(target=audio.run, daemon=True)
    voice_thread = threading.Thread(target=voice.run, daemon=True)
    cam_thread.start()
    audio_thread.start()
    voice_thread.start()

    print("[Assistant] 시작 - 카메라 창에서 'q'를 누르면 전체 종료")

    pending_close        = False
    pending_close_since  = None

    # [추가] 인식 모드 상태 - 시작은 손동작 모드
    mode = MODE_HAND
    last_mode_switch_time = 0.0
    last_hands_together_time = 0.0   # [추가] 양손이 마지막으로 모여 있던 시각 (박수 방식용)
    hands_together_start     = None  # [추가] 양손을 모으기 시작한 시각 (유지시간 판정용)
    mode_switch_armed        = True  # [추가] 한 번 전환 후엔 손을 떼야 다시 전환 가능
    cam.set_mode(mode)

    # [추가] 신호가 "새로 켜진 순간(rising edge)"에만 반응하기 위한 이전 상태 기억
    # (폴링 주기(0.02s)가 카메라/오디오 처리 주기보다 빨라서, 같은 신호를 여러 번 읽어
    #  콘솔에 중복으로 마구 찍히는 것을 방지)
    prev_yes = False
    prev_no  = False

    # [추가] swipe_up/swipe_down도 rising edge로만 반응 (commandmodule 연결용)
    prev_swipe_up   = False
    prev_swipe_down = False

    # [추가] 좌클릭(누름 상태)/우클릭(1회성 이벤트) 콘솔 로그용 이전 상태 기억
    prev_left_click  = False
    prev_right_click = False

    # [수정] 커스텀 명령 슬롯 3개(엄지+중지/약지/새끼) rising edge용 이전 상태 기억
    prev_pinch_slots = {name: False for name in PINCH_SLOT_NAMES}

    # [추가] 음성 명령 트리거(웨이크워드 / 손등 3초) rising edge용 이전 상태 기억
    prev_wake_word     = False
    prev_voice_trigger = False

    # [추가] 손등 무전기 방식 녹음 중인지 - main.py가 직접 시작/종료를 제어함
    recording_manual = False

    try:
        while cam_thread.is_alive():
            cam_res   = cam.get_result()
            pose_res  = pose.get_result()
            audio_res = audio.get_result()
            voice_res = voice.get_result()

            now = time.time()

            # [수정] 모드 전환 - "박수 소리 + 양손 모임(시각 확인)"이 동시에 있어야 인정.
            # 소리만으로 판정하면 주변 소음(문 닫는 소리, 남의 박수 등)에 오작동하는데,
            # 눈으로 본 확인까지 요구하면 사실상 오작동이 없어짐.
            # 양손 모임은 지금 켜져 있는 인식기에서 가져온다 - 손 모드는 mediapipe 손
            # 중심점 거리, 포즈 모드는 포즈의 손목 거리(÷어깨 너비)로 판정함.
            hands_together = (cam_res["hands_together"] if mode == MODE_HAND
                              else pose_res["hands_together"])
            if hands_together:
                last_hands_together_time = now
                if hands_together_start is None:
                    hands_together_start = now
            else:
                hands_together_start = None
                mode_switch_armed = True  # 손을 떼면 다시 전환 가능해짐

            if MODE_SWITCH_REQUIRE_CLAP:
                # [박수 방식] 박수와 양손 모임이 "동시"가 아니라 "최근"이면 인정
                switch_trigger = (audio_res["clap"] and
                                  (now - last_hands_together_time) < HANDS_TOGETHER_RECENT_SEC)
            else:
                # [현재 방식] 소리 없이 양손을 MODE_SWITCH_HOLD_SEC 이상 모으고 있으면 전환
                switch_trigger = (hands_together_start is not None and
                                  now - hands_together_start >= MODE_SWITCH_HOLD_SEC)

            # mode_switch_armed: 손을 계속 모으고 있어도 반복 전환되지 않게, 한 번 전환한
            # 뒤에는 손을 떼야만 다시 전환되도록 잠금
            if (switch_trigger and mode_switch_armed and
                    now - last_mode_switch_time > MODE_SWITCH_COOLDOWN_SEC):
                mode = MODE_POSE if mode == MODE_HAND else MODE_HAND
                last_mode_switch_time = now
                hands_together_start  = None
                mode_switch_armed     = False
                cam.set_mode(mode)
                _log("모드", f"{'전신 포즈' if mode == MODE_POSE else '손동작'} 모드로 전환")

            # [수정] 예/아니오는 엄지척/엄지다운 담당 (박수는 모드 전환 전용이 됐고,
            # 눈 깜빡임은 현재 비활성화 상태라 blink/double_blink는 항상 False임)
            yes_event = cam_res["blink"] or cam_res["thumbs_up"]
            no_event  = cam_res["double_blink"] or cam_res["thumbs_down"]

            # [추가] rising edge만 추출 - 신호가 계속 True로 읽혀도 딱 한 번만 반응
            yes_edge = yes_event and not prev_yes
            no_edge  = no_event and not prev_no
            prev_yes = yes_event
            prev_no  = no_event

            # [추가] swipe_up/swipe_down rising edge (commandmodule 연결용)
            swipe_up_edge   = cam_res["swipe_up"]   and not prev_swipe_up
            swipe_down_edge = cam_res["swipe_down"] and not prev_swipe_down
            prev_swipe_up   = cam_res["swipe_up"]
            prev_swipe_down = cam_res["swipe_down"]

            # [추가] 좌클릭 다운/업 전환, 우클릭 rising edge (콘솔 로그용)
            # - 카메라 프레임 처리 주기보다 이 폴링 주기(0.02s)가 더 빨라서, right_click도
            #   swipe와 마찬가지로 여기서 다시 한번 rising edge를 걸러줘야 중복 로그를 피함
            left_click_down_edge = cam_res["left_click"] and not prev_left_click
            left_click_up_edge   = prev_left_click and not cam_res["left_click"]
            prev_left_click      = cam_res["left_click"]
            right_click_edge     = cam_res["right_click"] and not prev_right_click
            prev_right_click     = cam_res["right_click"]

            # [추가] 커스텀 명령 슬롯 1(엄지+중지) rising edge
            pinch_slot_edges = {}
            for slot_name in PINCH_SLOT_NAMES:
                pinch_slot_edges[slot_name] = cam_res[slot_name] and not prev_pinch_slots[slot_name]
                prev_pinch_slots[slot_name] = cam_res[slot_name]

            # [추가] 음성 명령 트리거(웨이크워드 / 손등 5초) rising edge
            # - voice_res["wake_word"]는 VoiceModule이 CHECK_INTERVAL_SEC(1.5초)마다
            #   갱신하는 값이라 이 폴링 주기(0.02s)에서는 여러 번 True로 읽힐 수 있음
            wake_word_edge     = voice_res["wake_word"]    and not prev_wake_word
            voice_trigger_edge = cam_res["voice_trigger"]  and not prev_voice_trigger
            prev_wake_word     = voice_res["wake_word"]
            prev_voice_trigger = cam_res["voice_trigger"]

            # [수정] 어느 채널에서 온 신호인지 출력용으로 구분
            # (박수 채널이 모드 전환 전용으로 빠지면서 예/아니오는 손/눈만 남음)
            yes_source = "카메라-눈깜빡임" if cam_res["blink"] else "카메라-엄지척"
            no_source  = "카메라-눈더블블링크" if cam_res["double_blink"] else "카메라-엄지다운"

            if pending_close:
                if yes_edge:
                    # [수정] "닫기"도 commandmodule에 등록된 사용자 정의 명령이 있으면
                    # 그걸 실행, 없으면 기본 동작(실제 창 닫기)으로 폴백
                    ok, _ = commandmodule.execute_command("close_confirm")
                    if not ok:
                        windowcontrol.close_active_window()
                    pending_close = False
                    _log("확정", f"{'사용자 정의 명령 실행' if ok else '창 닫기 실행'} ({yes_source})")
                elif no_edge:
                    pending_close = False
                    _log("취소", f"창 닫기 취소 ({no_source})")
                elif time.time() - pending_close_since > CLOSE_CONFIRM_TIMEOUT_SEC:
                    pending_close = False
                    _log("취소", "응답 없음 - 자동 취소")
            else:
                if cam_res["close_request"]:
                    pending_close       = True
                    pending_close_since = time.time()
                    _log("확인 필요", "창을 닫을까요? 눈 1번/박수 1번=예, 더블=아니오 (5초 내 응답)")
                elif yes_edge:
                    _log("신호", f"예 / 동의 ({yes_source})")
                elif no_edge:
                    _log("신호", f"아니오 / 거절 ({no_source})")

            # [추가] swipe_up/swipe_down → commandmodule에 등록된 사용자 정의 명령이
            # 있으면 그걸 실행, 없으면 기본 동작(복원/최소화)으로 폴백.
            # close_request(손날+스와이프다운)는 위 pending_close 흐름에서 처리하므로 제외.
            if swipe_up_edge:
                ok, _ = commandmodule.execute_command("swipe_up")
                if not ok:
                    windowcontrol.restore_last_window()
                _log("제스처", f"swipe_up ({'사용자 정의' if ok else '기본 동작'})")
            if swipe_down_edge and not cam_res["close_request"]:
                ok, _ = commandmodule.execute_command("swipe_down")
                if not ok:
                    windowcontrol.minimize_active_window()
                _log("제스처", f"swipe_down ({'사용자 정의' if ok else '기본 동작'})")

            # [수정] 커스텀 명령 슬롯 3개(엄지를 중지/약지/새끼에 붙이기) - swipe와 달리
            # 기본 동작이 없는 순수 커스텀 슬롯이라, 등록된 명령이 없으면 아무 것도
            # 실행하지 않고 안내만 함
            for slot_name in PINCH_SLOT_NAMES:
                if pinch_slot_edges[slot_name]:
                    ok, _ = commandmodule.execute_command(slot_name)
                    if ok:
                        _log("제스처", f"{slot_name} (사용자 정의)")
                    else:
                        _log("제스처", f"{slot_name} - 등록된 명령 없음 (commandmodule.py로 등록하세요)")

            # [수정] 음성 명령 트리거 처리
            # - 웨이크워드: VoiceModule이 스스로 녹음을 시작하고 무음 감지로 알아서
            #   끝냄(mode="vad") - 여기선 로그만 남기면 됨
            # - 손등 3초 유지(무전기 방식): main.py가 직접 녹음 시작을 걸고, 이후 매
            #   프레임 손 방향을 지켜보다가 손등 자세가 풀리는 순간 직접 종료시킴
            if wake_word_edge:
                _log("음성", f"웨이크워드 감지 (\"{voice_res['last_text']}\") - 명령 녹음 시작")
            if voice_trigger_edge and not recording_manual and not voice_res["recording"]:
                # voice_res["recording"] 체크: 웨이크워드로 이미 녹음 중이면 겹쳐서
                # 시작하지 않음 (진행 중이던 vad 녹음 버퍼가 지워지는 것 방지)
                voice.start_command_recording(mode="manual")
                recording_manual = True
                _log("음성", "손등 유지 감지 - 명령 녹음 시작 (손을 떼면 종료)")
            if recording_manual and cam_res["hand_orientation"] != "back":
                voice.stop_command_recording()
                recording_manual = False
                _log("음성", "손등 자세 풀림 - 명령 녹음 종료")

            # [추가] 녹음이 끝나고 텍스트로 변환됐으면 LLM으로 해석해서 바로 실행
            # (제스처 슬롯에 등록하는 게 아니라, 그 자리에서 한 번만 실행하는 자유 명령)
            # [수정] LLM 호출을 별도 스레드로 돌림 - 여기서 바로 호출하면 응답이 올 때까지
            # (최대 60초) 이 루프가 통째로 멈춰서 그동안 제스처가 전혀 처리되지 않는다.
            if voice_res["command_text"]:
                heard_text = voice_res["command_text"]
                voice.clear_command_text()
                _log("음성", f"명령 인식: \"{heard_text}\"")
                threading.Thread(target=_run_voice_command,
                                 args=(heard_text,), daemon=True).start()

            # [추가] 마우스 좌/우클릭도 콘솔에 로그 (실제 클릭 자체는 cameramodule에서 이미 실행됨)
            if left_click_down_edge:
                _log("마우스", "좌클릭 DOWN (핀치)")
            elif left_click_up_edge:
                _log("마우스", "좌클릭 UP")
            if right_click_edge:
                _log("마우스", "우클릭 (엄지 넣기)")

            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        cam.stop()
        audio.stop()
        voice.stop()
        time.sleep(0.2)
        print("[Assistant] 종료")


if __name__ == "__main__":
    run_assistant()
