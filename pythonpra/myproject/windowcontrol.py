# ============================================================
#  개인 AI 비서 - 윈도우 제어 모듈
#  카메라 모듈에서 인식한 제스처로 현재 활성 창을 제어
#  (최소화 / 복원 / 닫기)
# ============================================================

import win32gui
import win32con
import win32api  # [추가] 모니터 켜기용 마우스 이벤트

CAMERA_WINDOW_TITLE = "AI Assistant - Camera"  # cameramodule.py의 imshow 창 제목

_last_minimized_hwnd = None  # swipe_up 복원을 위해 마지막으로 최소화한 창 기억


def _get_target_window():
    """현재 활성 창 핸들을 반환. 카메라 미리보기 창 자신은 제외."""
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None
    if win32gui.GetWindowText(hwnd) == CAMERA_WINDOW_TITLE:
        return None
    return hwnd


def minimize_active_window():
    """현재 활성 창을 최소화"""
    global _last_minimized_hwnd
    hwnd = _get_target_window()
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        _last_minimized_hwnd = hwnd


def restore_last_window():
    """직전에 최소화했던 창을 복원"""
    global _last_minimized_hwnd
    hwnd = _last_minimized_hwnd
    if hwnd and win32gui.IsWindow(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        try:
            win32gui.SetForegroundWindow(hwnd)  # 포커스 이동은 OS 정책상 실패할 수 있음
        except Exception:
            pass
    _last_minimized_hwnd = None


def close_active_window():
    """현재 활성 창에 닫기 메시지 전달 (앱이 저장 확인 등을 처리할 수 있도록 WM_CLOSE 사용)"""
    hwnd = _get_target_window()
    if hwnd:
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)


# [추가] 모니터 끄기/켜기 (롱블링크 화면끄기 / 5초 눈인식 화면켜기용)
def turn_off_monitor():
    """모니터에 절전(끄기) 신호 전달"""
    win32gui.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SYSCOMMAND, win32con.SC_MONITORPOWER, 2)


def turn_on_monitor():
    """
    절전 중인 모니터를 깨움.
    SC_MONITORPOWER에 '켜기' 값을 보내는 건 드라이버에 따라 무시되는 경우가 많아,
    마우스를 1px 움직였다가 되돌려 입력 이벤트로 깨우는 방식을 사용.
    """
    x, y = win32api.GetCursorPos()
    win32api.SetCursorPos((x + 1, y))
    win32api.SetCursorPos((x, y))
