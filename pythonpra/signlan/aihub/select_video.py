import os
import shutil

# ──────────────────────────────────────────────
# 설정값 비디오 선택해서 프레임찢기
# ──────────────────────────────────────────────
BASE_DIR = r"D:\JungPra\pythonpra\signlan"
SRC_DIR  = os.path.join(BASE_DIR, "downloaded_videos")
DST_DIR  = os.path.join(BASE_DIR, "selected_videos")

os.makedirs(DST_DIR, exist_ok=True)

WORDS = [
    '가다', '만나다', '보다', '듣다', '씻다',
    '아름답다', '거짓', '기다랗다', '걱정', '두려움',
    '기도', '죽다', '살인', '준비', '발표',
    '수학', '사진', '통신', '버스', '김치',
    '냉장고', '뛰어나다', '미미하다', '근면', '내리다'
]

ok   = []
fail = []

for word in WORDS:
    src_file = os.path.join(SRC_DIR, f"{word}.mp4")
    dst_file = os.path.join(DST_DIR, f"{word}.mp4")

    if os.path.exists(src_file):
        shutil.copy(src_file, dst_file)
        ok.append(word)
        print(f"✅ {word}")
    else:
        fail.append(word)
        print(f"❌ {word} → 없음")

print(f"\n📊 성공: {len(ok)}개 | 실패: {len(fail)}개")
if fail:
    print(f"❌ 없는 단어: {fail}")