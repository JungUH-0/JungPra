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

from cameramodule import CameraModule
from audiomodule import AudioModule
import windowcontrol
import commandmodule  # [추가] LLM으로 등록한 사용자 정의 명령 실행용

CLOSE_CONFIRM_TIMEOUT_SEC = 5.0  # 닫기 확인 요청 후 응답 없으면 자동 취소(안전 기본값)
VISUAL_CLAP_COOLDOWN_SEC  = 0.5  # 손이 겹친 채로 있는 동안 같은 박수가 중복 인식되는 것 방지


# [추가] 콘솔에 시각 태그를 붙여 어느 시점에 무슨 신호가 찍혔는지 구분하기 쉽게 함
def _log(tag, msg):
    print(f"[{time.strftime('%H:%M:%S')}] [{tag}] {msg}")


def run_assistant():
    cam   = CameraModule(camera_id=0, show_window=True)
    audio = AudioModule()

    cam_thread   = threading.Thread(target=cam.run, daemon=True)
    audio_thread = threading.Thread(target=audio.run, daemon=True)
    cam_thread.start()
    audio_thread.start()

    print("[Assistant] 시작 - 카메라 창에서 'q'를 누르면 전체 종료")

    pending_close        = False
    pending_close_since  = None
    last_visual_clap_time = 0.0  # [추가] 손겹침+소리스파이크 박수 보조 판정용 쿨다운

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

    # [추가] 커스텀 명령 슬롯 1(엄지+중지) rising edge용 이전 상태 기억
    prev_pinch_middle = False

    try:
        while cam_thread.is_alive():
            cam_res   = cam.get_result()
            audio_res = audio.get_result()

            # [추가] 양손이 겹친 상태에서 소리 스파이크가 같이 잡히면 박수로 인정
            # (오디오 단독 판정보다 느슨한 기준이라, 시각적 확인이 있을 때만 적용)
            now = time.time()
            visual_clap = False
            if (cam_res["hands_together"] and audio_res["spike"] and
                    now - last_visual_clap_time > VISUAL_CLAP_COOLDOWN_SEC):
                visual_clap = True
                last_visual_clap_time = now

            # [수정] 엄지척/엄지다운(손 제스처)을 예/아니오 채널에 추가
            yes_event = cam_res["blink"] or audio_res["clap"] or visual_clap or cam_res["thumbs_up"]
            no_event  = cam_res["double_blink"] or audio_res["double_clap"] or cam_res["thumbs_down"]

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
            pinch_middle_edge  = cam_res["pinch_middle"] and not prev_pinch_middle
            prev_pinch_middle  = cam_res["pinch_middle"]

            # [추가] 어느 채널에서 온 신호인지 출력용으로 구분
            if cam_res["blink"]:
                yes_source = "카메라-눈깜빡임"
            elif cam_res["thumbs_up"]:
                yes_source = "카메라-엄지척"
            elif visual_clap:
                yes_source = "융합-손겹침+소리"
            else:
                yes_source = "오디오-박수"
            if cam_res["double_blink"]:
                no_source = "카메라-눈더블블링크"
            elif cam_res["thumbs_down"]:
                no_source = "카메라-엄지다운"
            else:
                no_source = "오디오-더블박수"

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

            # [추가] 커스텀 명령 슬롯 1(엄지+중지 붙이기) - swipe와 달리 기본 동작이 없는
            # 순수 커스텀 슬롯이라, 등록된 명령이 없으면 아무 것도 실행하지 않고 안내만 함
            if pinch_middle_edge:
                ok, _ = commandmodule.execute_command("pinch_middle")
                if ok:
                    _log("제스처", "pinch_middle (사용자 정의)")
                else:
                    _log("제스처", "pinch_middle - 등록된 명령 없음 (commandmodule.py로 등록하세요)")

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
        time.sleep(0.2)
        print("[Assistant] 종료")


if __name__ == "__main__":
    run_assistant()
