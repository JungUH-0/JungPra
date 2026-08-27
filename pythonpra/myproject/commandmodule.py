# ============================================================
#  개인 AI 비서 - 명령 등록/실행 모듈 (로컬 LLM 기반)
#  사용자가 자연어로 입력한 명령을 Ollama(qwen2.5:3b-instruct)로 해석해서
#  {gesture, action, target} 형태의 구조화된 매핑으로 commands.json에 저장한다.
#  실시간 제스처 인식 루프(main.py)와는 분리되어, 명령을 등록/수정할 때만
#  이 스크립트를 직접 실행한다. LLM 호출은 여기서 끝나고, 실제 실행은
#  windowcontrol.py의 기존 함수로 위임한다(LLM이 시스템을 직접 건드리지 않음).
# ============================================================

import json
import os
import requests

import windowcontrol

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b-instruct"
COMMANDS_FILE = os.path.join(os.path.dirname(__file__), "commands.json")

# action별로 필요한 파라미터 정의 - LLM 출력 검증 및 프롬프트 스키마로 함께 사용
ALLOWED_ACTIONS = {
    "minimize_window": [],
    "close_window": [],
    "restore_window": [],
    "turn_off_monitor": [],
    "turn_on_monitor": [],
    "open_app": ["target"],
    "press_shortcut": ["target"],   # [추가] 키보드 단축키 입력
    "press_media_key": ["target"],  # [추가] 볼륨/재생 등 미디어 키 입력
    "open_url": ["target"],         # [추가] 화이트리스트에 등록된 사이트 열기
}

# [추가] target이 필요한 action마다 어떤 화이트리스트로 검증할지 매핑
# (windowcontrol.py에 있는 화이트리스트를 그대로 재사용 - LLM이 만든 임의 문자열이
#  그대로 실행되지 않도록 여기서도 한 번 더 걸러냄)
TARGET_WHITELISTS = {
    "open_app": windowcontrol.ALLOWED_APPS,
    "press_shortcut": windowcontrol.ALLOWED_SHORTCUTS,
    "press_media_key": windowcontrol.ALLOWED_MEDIA_KEYS,
    "open_url": windowcontrol.ALLOWED_URLS,
}

SYSTEM_PROMPT = f"""너는 사용자의 자연어 명령을 아래 JSON 스키마로만 변환하는 파서다.
다른 설명 없이 JSON 객체 하나만 출력해라.

허용된 action과 필요한 파라미터:
{json.dumps(ALLOWED_ACTIONS, ensure_ascii=False)}

각 action의 target으로 쓸 수 있는 값 (반드시 이 중 하나):
- open_app: {", ".join(windowcontrol.ALLOWED_APPS.keys())}
- press_shortcut: {", ".join(windowcontrol.ALLOWED_SHORTCUTS.keys())}
- press_media_key: {", ".join(windowcontrol.ALLOWED_MEDIA_KEYS.keys())}
- open_url: {", ".join(windowcontrol.ALLOWED_URLS.keys())}

주의:
- target 목록에 있는 값(예: close_tab, mute)을 action 자리에 쓰면 안 된다. action은 반드시 위 action 목록 중 하나여야 한다.
- "음소거"/"뮤트"/"소리 꺼줘"는 press_media_key(target=mute)이지, turn_off_monitor(모니터 끄기)가 아니다.
- "탭 닫기"는 press_shortcut(target=close_tab)이다.

예시:
사용자 명령: 탭 닫아줘
{{"action": "press_shortcut", "target": "close_tab"}}

사용자 명령: 소리 꺼줘
{{"action": "press_media_key", "target": "mute"}}

사용자 명령: 화면 꺼줘
{{"action": "turn_off_monitor", "target": null}}

사용자 명령: 유튜브 켜줘
{{"action": "open_url", "target": "youtube"}}

출력 형식(JSON만):
{{"action": "<action 이름>", "target": "<필요시 대상, 없으면 null>"}}

목록에 없는 동작이거나 해석할 수 없으면 action을 "unknown"으로 출력해라.
"""


def _ask_llm(user_text):
    """자연어 명령을 Ollama에 보내 구조화된 JSON으로 변환 요청"""
    prompt = f"{SYSTEM_PROMPT}\n\n사용자 명령: {user_text}"
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "format": "json",  # Ollama가 valid JSON만 생성하도록 강제
        },
        timeout=30,
    )
    resp.raise_for_status()
    return json.loads(resp.json()["response"])


def _load_commands():
    if not os.path.exists(COMMANDS_FILE):
        return {}
    with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_commands(commands):
    with open(COMMANDS_FILE, "w", encoding="utf-8") as f:
        json.dump(commands, f, ensure_ascii=False, indent=2)


def register_command(gesture_name, user_text):
    """자연어 명령을 해석해서 gesture_name에 대한 동작으로 저장"""
    parsed = _ask_llm(user_text)
    action = parsed.get("action")
    target = parsed.get("target")

    if action not in ALLOWED_ACTIONS:
        return False, f"인식 실패 또는 지원하지 않는 동작입니다: {parsed}"

    needed_params = ALLOWED_ACTIONS[action]
    if "target" in needed_params:
        whitelist = TARGET_WHITELISTS.get(action, {})
        if not target or target.strip().lower() not in whitelist:
            return False, f"target을 알아듣지 못했습니다: {parsed}"

    commands = _load_commands()
    commands[gesture_name] = {"action": action, "target": target}
    _save_commands(commands)
    return True, commands[gesture_name]


def _run_action(action, target):
    """
    이미 해석된 {action, target}을 실제로 실행 - execute_command(제스처 슬롯)와
    execute_text(자유 텍스트 즉시 실행)가 이 함수를 공유해서 씀
    """
    if action == "minimize_window":
        windowcontrol.minimize_active_window()
    elif action == "close_window":
        windowcontrol.close_active_window()
    elif action == "restore_window":
        windowcontrol.restore_last_window()
    elif action == "turn_off_monitor":
        windowcontrol.turn_off_monitor()
    elif action == "turn_on_monitor":
        windowcontrol.turn_on_monitor()
    elif action == "open_app":
        return windowcontrol.open_app(target)
    elif action == "press_shortcut":
        return windowcontrol.press_shortcut(target)
    elif action == "press_media_key":
        return windowcontrol.press_media_key(target)
    elif action == "open_url":
        return windowcontrol.open_url(target)
    else:
        return False, f"알 수 없는 action: {action}"

    return True, None


def execute_command(gesture_name):
    """
    저장된 매핑에서 gesture_name에 해당하는 동작을 실제로 실행.
    main.py 같은 실시간 루프에서, 제스처가 인식됐을 때 호출하는 용도.
    """
    commands = _load_commands()
    cmd = commands.get(gesture_name)
    if cmd is None:
        return False, "등록된 명령이 없습니다"
    return _run_action(cmd.get("action"), cmd.get("target"))


def execute_text(user_text):
    """
    자연어 명령을 그 자리에서 해석해서 바로 실행 (제스처 슬롯에 등록하지 않는
    1회성 실행). 음성 명령처럼, 미리 등록해두지 않고 그때그때 자유롭게
    명령할 때 사용.
    """
    parsed = _ask_llm(user_text)
    action = parsed.get("action")
    target = parsed.get("target")

    if action not in ALLOWED_ACTIONS:
        return False, f"인식 실패 또는 지원하지 않는 동작입니다: {parsed}"

    needed_params = ALLOWED_ACTIONS[action]
    if "target" in needed_params:
        whitelist = TARGET_WHITELISTS.get(action, {})
        if not target or target.strip().lower() not in whitelist:
            return False, f"target을 알아듣지 못했습니다: {parsed}"

    return _run_action(action, target)


# ── 테스트/등록용 실행 ─────────────────────────────────────
if __name__ == "__main__":
    print("[CommandModule] 명령 등록 - Ctrl+C로 종료")
    while True:
        try:
            gesture = input("\n제스처 이름 (예: double_clap, swipe_left): ").strip()
            if not gesture:
                continue
            text = input("무엇을 하고 싶으세요? (자연어로 입력): ").strip()
            if not text:
                continue

            ok, result = register_command(gesture, text)
            if ok:
                print(f"등록 완료: {gesture} -> {result}")
                run = input("지금 바로 실행해볼까요? (y/n): ").strip().lower()
                if run == "y":
                    ok2, err = execute_command(gesture)
                    print("실행 성공" if ok2 else f"실행 실패: {err}")
            else:
                print(f"등록 실패: {result}")
        except KeyboardInterrupt:
            print("\n[CommandModule] 종료")
            break
