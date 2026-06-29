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

CLOSE_CONFIRM_TIMEOUT_SEC = 5.0  # 닫기 확인 요청 후 응답 없으면 자동 취소(안전 기본값)
VISUAL_CLAP_COOLDOWN_SEC  = 0.5  # 손이 겹친 채로 있는 동안 같은 박수가 중복 인식되는 것 방지


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

            yes_event = cam_res["blink"] or audio_res["clap"] or visual_clap
            no_event  = cam_res["double_blink"] or audio_res["double_clap"]

            if pending_close:
                if yes_event:
                    windowcontrol.close_active_window()
                    pending_close = False
                    print("[확정] 창 닫기 실행")
                elif no_event:
                    pending_close = False
                    print("[취소] 창 닫기 취소")
                elif time.time() - pending_close_since > CLOSE_CONFIRM_TIMEOUT_SEC:
                    pending_close = False
                    print("[취소] 응답 없음 - 자동 취소")
            else:
                if cam_res["close_request"]:
                    pending_close       = True
                    pending_close_since = time.time()
                    print("[확인 필요] 창을 닫을까요? 눈 1번/박수 1번=예, 더블=아니오")
                elif yes_event:
                    print("[신호] 예 / 동의")
                elif no_event:
                    print("[신호] 아니오 / 거절")

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
