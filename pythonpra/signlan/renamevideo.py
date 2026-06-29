import os
import shutil
import cv2
from PIL import ImageFont, ImageDraw, Image
import numpy as np

# ──────────────────────────────────────────────
# 설정값
# ──────────────────────────────────────────────
SRC_DIR   = r"C:\Users\AISW_203_104\Pictures\Camera Roll"
NUM_DIR   = os.path.join(SRC_DIR, "mynum")
VOWEL_DIR = os.path.join(SRC_DIR, "myvowel")
CONS_DIR  = os.path.join(SRC_DIR, "myconsonant")

os.makedirs(NUM_DIR,   exist_ok=True)
os.makedirs(VOWEL_DIR, exist_ok=True)
os.makedirs(CONS_DIR,  exist_ok=True)

FONT_PATHS = [
    r"C:\Windows\Fonts\malgun.ttf",
    r"C:\Windows\Fonts\gulim.ttc",
]

NUMBERS    = list('0123456789')
CONSONANTS = ['ㄱ','ㄴ','ㄷ','ㄹ','ㅁ','ㅂ','ㅅ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
VOWELS     = ['ㅏ','ㅐ','ㅑ','ㅒ','ㅓ','ㅕ','ㅖ','ㅗ','ㅛ','ㅜ','ㅠ','ㅡ','ㅣ']
ALL_LABELS = NUMBERS + CONSONANTS + VOWELS

KEY_TO_LABEL = {
    '0':'0','1':'1','2':'2','3':'3','4':'4',
    '5':'5','6':'6','7':'7','8':'8','9':'9',
    'a':'ㄱ','b':'ㄴ','c':'ㄷ','d':'ㄹ','e':'ㅁ',
    'f':'ㅂ','g':'ㅅ','h':'ㅇ','i':'ㅈ','j':'ㅊ',
    'k':'ㅋ','l':'ㅌ','m':'ㅍ','n':'ㅎ',
    'A':'ㅏ','B':'ㅐ','C':'ㅑ','D':'ㅒ','E':'ㅓ',
    'F':'ㅕ','G':'ㅖ','H':'ㅗ','I':'ㅛ','J':'ㅜ',
    'K':'ㅠ','L':'ㅡ','M':'ㅣ',
}


def load_font(size):
    for path in FONT_PATHS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

FONT_LARGE  = load_font(55)
FONT_MEDIUM = load_font(28)
FONT_SMALL  = load_font(19)
FONT_TINY   = load_font(16)

def draw_korean(frame, text, pos, font, color=(255,255,255), shadow=True):
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw    = ImageDraw.Draw(img_pil)
    x, y   = pos
    if shadow:
        draw.text((x+2, y+2), text, font=font, fill=(0,0,0))
    draw.text((x, y), text, font=font, fill=(color[2], color[1], color[0]))
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


def get_save_dir(label):
    if label in NUMBERS:      return NUM_DIR
    elif label in CONSONANTS: return CONS_DIR
    elif label in VOWELS:     return VOWEL_DIR
    return None


def get_next_idx(label):
    save_dir = get_save_dir(label)
    existing = [f for f in os.listdir(save_dir)
                if f.startswith(f"{label}_") and f.endswith('.mp4')]
    return len(existing) + 1


def draw_mapping_table(frame):
    h, w = frame.shape[:2]
    tx   = w - 250
    cv2.rectangle(frame, (tx-5, 0), (w, h), (15,15,15), -1)

    frame = draw_korean(frame, "[ 키 매핑표 ]",
                        (tx, 5), FONT_SMALL, (255,200,0), shadow=False)

    frame = draw_korean(frame, "─ 자음 (소문자) ─",
                        (tx, 30), FONT_TINY, (150,200,255), shadow=False)
    for idx, line in enumerate([
        "a=ㄱ  b=ㄴ  c=ㄷ  d=ㄹ",
        "e=ㅁ  f=ㅂ  g=ㅅ  h=ㅇ",
        "i=ㅈ  j=ㅊ  k=ㅋ  l=ㅌ",
        "m=ㅍ  n=ㅎ",
    ]):
        frame = draw_korean(frame, line, (tx, 50+idx*22), FONT_TINY, (200,220,255), shadow=False)

    frame = draw_korean(frame, "─ 모음 (대문자/Shift) ─",
                        (tx, 145), FONT_TINY, (255,180,150), shadow=False)
    for idx, line in enumerate([
        "A=ㅏ  B=ㅐ  C=ㅑ  D=ㅒ",
        "E=ㅓ  F=ㅕ  G=ㅖ  H=ㅗ",
        "I=ㅛ  J=ㅜ  K=ㅠ  L=ㅡ",
        "M=ㅣ ",
    ]):
        frame = draw_korean(frame, line, (tx, 165+idx*22), FONT_TINY, (255,210,190), shadow=False)

    frame = draw_korean(frame, "─ 숫자 ─",
                        (tx, 260), FONT_TINY, (150,255,150), shadow=False)
    frame = draw_korean(frame, "0~9 그대로 입력",
                        (tx, 278), FONT_TINY, (190,255,190), shadow=False)

    frame = draw_korean(frame, "─ 조작키 ─",
                        (tx, 310), FONT_TINY, (200,200,200), shadow=False)
    for idx, op in enumerate(["Enter: 확정","S: 건너뜀","X: 이전으로","Q: 종료"]):
        frame = draw_korean(frame, op, (tx, 328+idx*20), FONT_TINY, (180,180,180), shadow=False)

    return frame


def run():
    # 하위 폴더 제외하고 영상만
    video_files = sorted([
        f for f in os.listdir(SRC_DIR)
        if f.endswith('.mp4') and
        os.path.isfile(os.path.join(SRC_DIR, f))
    ])

    if not video_files:
        print("❌ 남은 영상이 없습니다. 모두 완료!")
        return

    print(f"총 {len(video_files)}개 영상 남음!")
    print(f"저장 위치: Camera Roll 내 폴더로 이동 (원본 삭제)\n")

    renamed       = []
    current_key   = ""
    current_label = ""
    i = 0

    while i < len(video_files):
        video_file = video_files[i]
        video_path = os.path.join(SRC_DIR, video_file)

        # 파일이 이미 없으면 스킵 (이미 이동됨)
        if not os.path.exists(video_path):
            i += 1
            continue

        cap       = cv2.VideoCapture(video_path)
        fps       = cap.get(cv2.CAP_PROP_FPS) or 30
        confirmed = False
        current_key   = ""
        current_label = ""

        # 남은 파일 수 실시간 반영
        remaining = len([f for f in os.listdir(SRC_DIR)
                         if f.endswith('.mp4') and os.path.isfile(os.path.join(SRC_DIR, f))])
        print(f"[{i+1}/{len(video_files)}] 남은파일: {remaining}개 | {video_file}")

        while True:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret: break

            frame = cv2.resize(frame, (1280,720))
            h, w  = frame.shape[:2]

            frame = draw_mapping_table(frame)

            overlay = frame.copy()
            cv2.rectangle(overlay, (0,0), (w-380,65), (20,20,20), -1)
            cv2.rectangle(overlay, (0,h-120), (w-380,h), (20,20,20), -1)
            cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

            frame = draw_korean(frame,
                                f"[{i+1}/{len(video_files)}] 남은: {remaining}개",
                                (5, 5), FONT_TINY, (200,200,200), shadow=False)
            frame = draw_korean(frame,
                                f"완료: {len(renamed)}개",
                                (5, 25), FONT_TINY, (0,200,100), shadow=False)

            key_display   = current_key   if current_key   else "?"
            label_display = current_label if current_label else "?"
            color = (0,255,150) if current_label in ALL_LABELS else (150,150,150)

            frame = draw_korean(frame,
                                f"입력: {key_display}  →  {label_display}",
                                (5, h-115), FONT_LARGE, color)

            if current_label in ALL_LABELS:
                next_idx  = get_next_idx(current_label)
                next_name = f"{current_label}_{next_idx:02d}.mp4"
                folder    = os.path.basename(get_save_dir(current_label))
                frame = draw_korean(frame,
                                    f"저장: {folder}/{next_name}",
                                    (5, h-45), FONT_SMALL, (255,200,0), shadow=False)

            if renamed:
                _, last, _ = renamed[-1]
                frame = draw_korean(frame,
                                    f"최근: {last}",
                                    (5, h-20), FONT_TINY, (0,180,100), shadow=False)

            cv2.imshow("영상 라벨링", frame)
            key = cv2.waitKey(int(1000/fps)) & 0xFF

            if key == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                _print_summary(renamed)
                return

            elif key == ord('s'):
                print(f"  ⏭️  건너뜀")
                break

            elif key == ord('x') and i > 0:
                if renamed:
                    old, new, saved_dir = renamed.pop()
                    moved_path = os.path.join(saved_dir, new)
                    if os.path.exists(moved_path):
                        # 원래 위치로 되돌리기
                        shutil.move(moved_path, os.path.join(SRC_DIR, old))
                        print(f"  ↩️  되돌림: {new} → {old}")
                i -= 1
                break

            elif key == 13:  # Enter
                if current_label in ALL_LABELS:
                    idx      = get_next_idx(current_label)
                    new_name = f"{current_label}_{idx:02d}.mp4"
                    save_dir = get_save_dir(current_label)
                    confirmed = True
                    break  # cap.release() 후에 이동
                else:
                    print(f"  ❌ 유효하지 않은 입력: '{current_key}'")
                    current_key   = ""
                    current_label = ""

            elif key == 8:
                current_key   = ""
                current_label = ""

            elif key != 255:
                char = chr(key) if key < 128 else ""
                if char:
                    current_key   = char
                    current_label = KEY_TO_LABEL.get(char, "")

        cap.release()

        # cap 닫은 후 파일 이동 (파일 잠금 해제 후)
        if confirmed:
            dst = os.path.join(save_dir, new_name)
            shutil.move(video_path, dst)
            renamed.append((video_file, new_name, save_dir))
            print(f"  ✅ → {os.path.basename(save_dir)}/{new_name}")

        if key == ord('x'):
            pass
        else:
            i += 1

    cv2.destroyAllWindows()
    _print_summary(renamed)


def _print_summary(renamed):
    from collections import Counter
    counts = Counter()
    for _, new_name, _ in renamed:
        label = new_name.rsplit('_', 1)[0]
        counts[label] += 1
    print(f"\n{'='*50}")
    print(f"🎉 완료! 총 {len(renamed)}개 변환")
    for label in sorted(counts):
        print(f"  {label}: {counts[label]}개")


if __name__ == "__main__":
    run()