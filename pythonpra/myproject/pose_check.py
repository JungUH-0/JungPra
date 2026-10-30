# ============================================================
#  포즈 모드 단독 확인용 스크립트
#  카메라 + PoseModule만 연결해서 끄덕임 / 가로젓기 / 자리 비움 판정을 확인한다.
#  음성·오디오·PC 제어(main.py)는 띄우지 않으므로 마우스·키보드가 움직이지 않는다.
#
#  사용: python pose_check.py   (카메라 창에서 'q'로 종료)
#  임계값 조정: posemodule.py의 HEAD_* / AWAY_AFTER_SEC 상수를 고치고 다시 실행.
#  값 변화는 debug_pose.txt에도 0.3초 간격으로 남는다 (headPitch / headTurn).
# ============================================================

import time
import threading

from cameramodule import CameraModule
from posemodule import PoseModule

MODE_POSE = "pose"
POLL_SEC = 0.02


def _log(tag, msg):
    print(f"[{time.strftime('%H:%M:%S')}] [{tag}] {msg}")


def _watch(pose, cam):
    """pose 결과를 폴링해서 이벤트가 켜지는 순간(rising edge)만 콘솔에 출력"""
    prev = {"nod": False, "shake": False, "away": False}
    while cam.running:
        res = pose.get_result()
        if res["nod"] and not prev["nod"]:
            _log("이벤트", "끄덕임 (예)")
        if res["shake"] and not prev["shake"]:
            _log("이벤트", "가로젓기 (아니오)")
        if res["away"] and not prev["away"]:
            _log("이벤트", "자리 비움")
        if prev["away"] and not res["away"]:
            _log("이벤트", "자리 복귀")
        prev = {k: res[k] for k in prev}
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    pose = PoseModule()
    cam = CameraModule(camera_id=0, show_window=True, pose_module=pose)
    cam.set_mode(MODE_POSE)

    print("[pose_check] 포즈 모드 시작 - 두 번 끄덕이면 예, 두 번 가로저으면 아니오")
    print("[pose_check] 카메라에서 벗어나 있으면 자리 비움, 'q'로 종료")

    # 카메라 창(cv)은 메인 스레드에서 돌리고, 이벤트 출력만 별도 스레드로 둔다.
    # cam.running은 run() 안에서 켜지므로, 먼저 True로 둬서 감시 스레드가 바로 돌게 한다.
    cam.running = True
    threading.Thread(target=_watch, args=(pose, cam), daemon=True).start()
    cam.run()
