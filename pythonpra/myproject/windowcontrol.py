# ============================================================
#  개인 AI 비서 - 윈도우 제어 모듈
#  카메라 모듈에서 인식한 제스처로 현재 활성 창을 제어
#  (최소화 / 복원 / 닫기)
# ============================================================

import os
import win32gui
import win32con
import win32api  # [추가] 모니터 켜기용 마우스 이벤트

CAMERA_WINDOW_TITLE = "AI Assistant - Camera"  # cameramodule.py의 imshow 창 제목

# [추가] LLM이 해석한 "앱 열기" 명령용 화이트리스트 (임의 문자열 실행 방지 - 등록된 이름만 허용)
ALLOWED_APPS = {
    "chrome": "chrome",
    "edge": "msedge",
    "notepad": "notepad",
    "calculator": "calc",
    "explorer": "explorer",
    "cmd": "cmd",
    "powershell": "powershell",
}

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
    [수정] SetCursorPos는 좌표만 옮길 뿐 '진짜 입력'으로 인식되지 않는 경우가 많아
    모니터가 안 깨는 경우가 있었음. keybd_event로 실제 키 입력 이벤트를 발생시키는
    방식이 더 확실하게 깨움 (SC_MONITORPOWER 켜기 신호도 함께 보내 이중으로 시도).
    """
    win32gui.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SYSCOMMAND, win32con.SC_MONITORPOWER, -1)
    win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)                          # Shift 키 누름
    win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)   # Shift 키 뗌


# [추가] 핀치(엄지+검지 집기) 제스처로 창을 잡아서 옮기는 기능
def get_screen_size():
    """모니터 해상도 (width, height) 반환 - 손 좌표를 화면 좌표로 매핑할 때 사용"""
    return win32api.GetSystemMetrics(win32con.SM_CXSCREEN), win32api.GetSystemMetrics(win32con.SM_CYSCREEN)


# [추가] 검지 손가락으로 실제 OS 마우스 커서를 조작하는 기능용
def move_cursor_to(x, y):
    """실제 마우스 커서를 화면 좌표 (x, y)로 이동"""
    win32api.SetCursorPos((int(x), int(y)))


# [추가] 핀치(엄지+검지) = 실제 좌클릭, 검지+중지 겹쳐 내리기 = 실제 우클릭
def mouse_left_down():
    """마우스 왼쪽 버튼을 누른 상태로 (커서 이동 중에도 유지되면 드래그처럼 동작)"""
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)


def mouse_left_up():
    """마우스 왼쪽 버튼을 뗌"""
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def mouse_right_click():
    """마우스 오른쪽 버튼 클릭(누르고 즉시 뗌, 1회성)"""
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)


# [추가] 중지 단독 제스처로 마우스 휠 스크롤
def mouse_scroll(ticks):
    """휠을 ticks만큼 굴림 (양수=위로 스크롤, 음수=아래로 스크롤). 1틱 = 표준 휠 한 칸(120)"""
    win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, int(ticks * 120), 0)


def get_window_at_point(x, y):
    """화면 좌표 (x, y) 아래에 있는 최상위 창의 핸들을 반환. 카메라 미리보기 창은 제외."""
    hwnd = win32gui.WindowFromPoint((x, y))
    if not hwnd:
        return None
    hwnd = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)  # 자식 컨트롤이 아닌 최상위 창으로
    if not hwnd or win32gui.GetWindowText(hwnd) == CAMERA_WINDOW_TITLE:
        return None
    return hwnd


def get_window_rect(hwnd):
    """창의 (left, top, right, bottom) 화면 좌표 반환"""
    return win32gui.GetWindowRect(hwnd)


def is_window_valid(hwnd):
    """드래그 중 창이 닫히는 등으로 핸들이 무효해졌는지 확인"""
    return bool(hwnd) and win32gui.IsWindow(hwnd)


def move_window_to(hwnd, x, y):
    """창을 좌상단이 화면 좌표 (x, y)가 되도록 이동 (크기/Z순서/포커스는 그대로 유지)"""
    if hwnd and win32gui.IsWindow(hwnd):
        win32gui.SetWindowPos(
            hwnd, 0, int(x), int(y), 0, 0,
            win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
        )


# [추가] LLM이 해석한 명령("앱 열기")을 실제로 실행하는 함수
def open_app(name):
    """
    ALLOWED_APPS 화이트리스트에 있는 앱만 실행 (LLM이 만든 임의 문자열을 그대로
    실행하면 명령 주입 위험이 있어서, 등록된 이름으로만 매핑해 실행함)
    반환값: (성공 여부, 에러 메시지 또는 None)
    """
    if not name:
        return False, "앱 이름이 없습니다"
    key = name.strip().lower()
    exe = ALLOWED_APPS.get(key)
    if exe is None:
        return False, f"허용되지 않은 앱: {name}"
    try:
        os.startfile(exe)
        return True, None
    except OSError as e:
        return False, str(e)
