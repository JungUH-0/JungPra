import os
import cv2
import time
import numpy as np

# ──────────────────────────────────────────────
# 설정값
# ──────────────────────────────────────────────
BASE_DIR       = r"D:\JungPra\pythonpra\signlan"
REF_VIDEO_DIR  = os.path.join(BASE_DIR, "selected_videos")       # 국립국어원 참고 영상
SAVE_VIDEO_DIR = os.path.join(BASE_DIR, "my_recorded_videos")    # 본인 녹화 영상
os.makedirs(SAVE_VIDEO_DIR, exist_ok=True)

RECORD_SEC     = 3      # 녹화 시간 (초)
COUNTDOWN_SEC  = 3      # 카운트다운 (초)
SAMPLES_PER_WORD = 10   # 단어당 몇 번 녹화할지

# 학습할 단어 목록
WORDS = [
    '가다', '만나다', '보다', '듣다', '씻다',
    '아름답다', '거짓', '기다랗다', '걱정', '두려움',
    '기도', '죽다', '살인', '준비', '발표',
    '수학', '사진', '통신', '버스', '김치',
    '냉장고', '뛰어나다', '미미하다', '근면', '내리다'
]


# ──────────────────────────────────────────────
# 텍스트 그리기
# ──────────────────────────────────────────────
def draw_text(frame, text, pos, scale=1.0, color=(255,255,255), thickness=2):
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX,
                scale, (0,0,0), thickness+2, cv2.LINE_AA)
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thickness, cv2.LINE_AA)


# ──────────────────────────────────────────────
# 참고 영상 재생
# ──────────────────────────────────────────────
def play_reference(word):
    ref_path = os.path.join(REF_VIDEO_DIR, f"{word}.mp4")
    if not os.path.exists(ref_path):
        print(f"   ⚠️  참고 영상 없음: {word}.mp4")
        return

    cap = cv2.VideoCapture(ref_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    print(f"   📺 참고 영상 재생 중... (반복 재생, 아무 키나 누르면 종료)")

    # 3번 반복 재생
    for repeat in range(3):
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (640, 480))
            overlay = frame.copy()
            cv2.rectangle(overlay, (0,0), (640, 60), (20,20,20), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

            draw_text(frame, f"[{repeat+1}/3] REF: {word}", (10, 40), 0.9, (0, 255, 200))
            draw_text(frame, "Any key: next / Q: skip", (10, 460), 0.5, (150,150,150), 1)

            cv2.imshow("Reference Video", frame)
            key = cv2.waitKey(int(1000/fps)) & 0xFF
            if key != 255:
                cap.release()
                cv2.destroyWindow("Reference Video")
                return

    cap.release()
    cv2.destroyWindow("Reference Video")


# ──────────────────────────────────────────────
# 웹캠 녹화
# ──────────────────────────────────────────────
def record_sample(word, sample_idx, webcam):
    save_path = os.path.join(SAVE_VIDEO_DIR, f"{word}_{sample_idx:02d}.mp4")

    # 이미 녹화된 샘플이면 스킵
    if os.path.exists(save_path):
        print(f"   ⏭️  이미 존재: {word}_{sample_idx:02d}.mp4")
        return True

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    w = int(webcam.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(webcam.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = None

    # ── 카운트다운 ──────────────────────────────
    start = time.time()
    while time.time() - start < COUNTDOWN_SEC:
        ret, frame = webcam.read()
        if not ret:
            break
        frame   = cv2.flip(frame, 1)
        remain  = COUNTDOWN_SEC - int(time.time() - start)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0,0), (w, 80), (20,20,20), -1)
        cv2.rectangle(overlay, (0, h-60), (w, h), (20,20,20), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        draw_text(frame, f"Word: {word}  [{sample_idx+1}/{SAMPLES_PER_WORD}]",
                  (10, 40), 0.8, (255, 200, 0))
        draw_text(frame, f"Ready: {remain}",
                  (w//2 - 60, h//2), 2.0, (0, 100, 255), 4)
        draw_text(frame, "Q: quit  S: skip word",
                  (10, h-20), 0.5, (150,150,150), 1)

        cv2.imshow("Record", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return False
        if key == ord('s'):
            return "skip"

    # ── 녹화 ───────────────────────────────────
    writer    = cv2.VideoWriter(save_path, fourcc, 30, (w, h))
    rec_start = time.time()

    while time.time() - rec_start < RECORD_SEC:
        ret, frame = webcam.read()
        if not ret:
            break
        frame    = cv2.flip(frame, 1)
        elapsed  = time.time() - rec_start
        progress = elapsed / RECORD_SEC

        writer.write(frame)

        # 녹화 중 UI
        overlay = frame.copy()
        cv2.rectangle(overlay, (0,0), (w, 80), (20,20,20), -1)
        cv2.rectangle(overlay, (0, h-60), (w, h), (20,20,20), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # 녹화 진행바
        bar_w = int((w-20) * progress)
        cv2.rectangle(frame, (10, h-40), (w-10, h-20), (50,50,50), -1)
        cv2.rectangle(frame, (10, h-40), (10+bar_w, h-20), (0, 0, 200), -1)

        draw_text(frame, f"REC  {word}  [{sample_idx+1}/{SAMPLES_PER_WORD}]",
                  (10, 40), 0.8, (0, 0, 255))
        draw_text(frame, f"{RECORD_SEC - elapsed:.1f}s",
                  (w-100, 40), 0.8, (0,0,255))

        # 녹화 중 빨간 점
        cv2.circle(frame, (w-30, 30), 12, (0,0,255), -1)

        cv2.imshow("Record", frame)
        cv2.waitKey(1)

    writer.release()
    print(f"   ✅ 저장: {word}_{sample_idx:02d}.mp4")
    return True


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def run():
    print("🎬 수어 데이터 직접 녹화 도구")
    print(f"   단어 수: {len(WORDS)}개")
    print(f"   단어당 샘플: {SAMPLES_PER_WORD}개")
    print(f"   총 녹화 예정: {len(WORDS) * SAMPLES_PER_WORD}개\n")
    print("   조작법: Q=종료 / S=이 단어 건너뜀 / Space=참고영상 다시보기\n")

    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("❌ 웹캠을 열 수 없습니다.")
        return

    webcam.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    for word_idx, word in enumerate(WORDS):
        print(f"\n{'='*55}")
        print(f"📝 [{word_idx+1}/{len(WORDS)}] 단어: {word}")
        print(f"{'='*55}")

        # 참고 영상 먼저 보여주기
        play_reference(word)

        # 샘플 녹화
        for sample_idx in range(SAMPLES_PER_WORD):
            result = record_sample(word, sample_idx, webcam)

            if result == False:   # Q 누름 → 전체 종료
                webcam.release()
                cv2.destroyAllWindows()
                print("\n👋 녹화 종료!")
                return
            if result == "skip":  # S 누름 → 다음 단어
                print(f"   ⏭️  [{word}] 건너뜀")
                break

            # 샘플 간 잠깐 대기
            time.sleep(0.5)

        print(f"✨ [{word}] 완료!")

    webcam.release()
    cv2.destroyAllWindows()
    print(f"\n🎉 모든 녹화 완료!")
    print(f"📂 저장 폴더: {SAVE_VIDEO_DIR}")
    print(f"\n다음 단계:")
    print(f"  1. preprocess_videos.py 에서 SRC_VIDEO_DIR = my_recorded_videos 로 변경")
    print(f"  2. python preprocess_videos.py")
    print(f"  3. python trainhandle_torch.py")


if __name__ == "__main__":
    run()