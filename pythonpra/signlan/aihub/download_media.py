# import os
# import time
# import urllib.request
# import requests
# from bs4 import BeautifulSoup

# def download_sign_language_data():
#     # 🌟 핵심: 방화벽을 속이기 위한 크롬 브라우저 가짜 신분증(User-Agent)
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#     }

#     # 저장할 폴더 생성
#     os.makedirs("./downloaded_images", exist_ok=True)
#     os.makedirs("./downloaded_videos", exist_ok=True)

#     # 테스트용 국립국어원 수어 단어 URL (예시 주소입니다. 본인의 대상 URL로 바꾸셔도 됩니다)
#     # 여기서는 예시로 '차다' 단어 페이지나 메인 오픈 API 상세 페이지 주소를 넣습니다.
#     target_url = "https://sldict.korean.go.kr/front/main/main.do" 
    
#     print("🚀 [신분 우회] 국립국어원 서버 연결 시도 중...")
    
#     try:
#         # 헤더를 첨부하여 브라우저인 척 요청 보냄
#         response = requests.get(target_url, headers=headers, timeout=10)
        
#         if response.status_code == 200:
#             print("✅ [성공] 서버 연결에 성공했습니다! 방어벽을 우회했습니다.")
            
#             # 여기에 기존에 작성하셨던 동영상/이미지 다운로드 url 파싱 및 추출 로직이 들어갑니다.
#             # 예시로 미디어 파일 url이 있다고 가정하고 다운로드할 때도 헤더를 적용해야 합니다:
#             """
#             video_url = "http://sldict.korean.go.kr/multimedia/..."
#             req = urllib.request.Request(video_url, headers=headers)
#             with urllib.request.urlopen(req) as video_response, open("./downloaded_videos/차다.mp4", "wb") as out_file:
#                 out_file.write(video_response.read())
#             """
            
#         else:
#             print(f"❌ 서버가 응답했으나 거절되었습니다. 상태코드: {response.status_code}")
            
#     except requests.exceptions.Timeout:
#         print("❌ 타임아웃 에러: 서버가 여전히 응답하지 않습니다.")
#     except Exception as e:
#         print(f"❌ 기타 에러 발생: {e}")

# if __name__ == "__main__":
#     download_sign_language_data()

import os
import json
import time
import requests
import glob

# ──────────────────────────────────────────────
# 설정값 영상/사진 저장
# ──────────────────────────────────────────────
BASE_DIR  = r"D:\JungPra\pythonpra\signlan"
JSON_DIR  = os.path.join(BASE_DIR, "raw_json")
VIDEO_DIR = os.path.join(BASE_DIR, "downloaded_videos")
IMAGE_DIR = os.path.join(BASE_DIR, "downloaded_images")

SITE_URL   = "https://sldict.korean.go.kr/front/main/main.do"
CHUNK_SIZE = 8192
TIMEOUT    = 30
DELAY      = 0.3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://sldict.korean.go.kr/",
    "Accept": "*/*",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Connection": "keep-alive",
}


# ──────────────────────────────────────────────
# http → https 변환
# ──────────────────────────────────────────────
def to_https(url: str) -> str:
    if url.startswith("http://"):
        return "https://" + url[7:]
    return url


# ──────────────────────────────────────────────
# 세션 초기화
# ──────────────────────────────────────────────
def init_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        res = session.get(SITE_URL, timeout=TIMEOUT)
        print(f"   🔑 세션 발급 완료 (상태: {res.status_code})")
    except Exception as e:
        print(f"   ⚠️  세션 발급 실패 ({e}) → 쿠키 없이 진행")
    return session


# ──────────────────────────────────────────────
# 스트리밍 다운로드
# ──────────────────────────────────────────────
def stream_download(session: requests.Session, url: str, save_path: str) -> bool:
    try:
        res = session.get(url, timeout=TIMEOUT, stream=True)

        if res.status_code == 403:
            print(f"   ❌ 403 Forbidden")
            return False
        if res.status_code == 404:
            print(f"   ❌ 404 Not Found → 파일 없음")
            return False

        res.raise_for_status()

        with open(save_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

        if os.path.getsize(save_path) < 1024:
            os.remove(save_path)
            print(f"   ❌ 응답이 비어있음 (차단 의심)")
            return False

        return True

    except requests.exceptions.Timeout:
        print(f"   ⏱️  타임아웃 ({TIMEOUT}s 초과)")
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ 연결 실패: {e}")
    except Exception as e:
        print(f"   ❌ 에러: {e}")

    if os.path.exists(save_path):
        os.remove(save_path)
    return False


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def download_media():
    os.makedirs(VIDEO_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)

    json_files = sorted(glob.glob(os.path.join(JSON_DIR, "test_page_*.json")))
    if not json_files:
        print("❌ raw_json 폴더에 JSON 파일이 없습니다.")
        return

    print(f"📂 JSON 파일 {len(json_files)}개 발견")
    print("🚀 세션 초기화 중...")
    session = init_session()

    total_v_ok = total_v_fail = 0
    total_i_ok = total_i_fail = 0

    for json_path in json_files:
        print(f"\n{'='*55}")
        print(f"📖 {os.path.basename(json_path)}")
        print(f"{'='*55}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for idx, item in enumerate(data.get("items", [])):
            word_name  = item["title"].split(",")[0].strip()
            safe_name  = "".join(c for c in word_name if c not in r'\/:*?"<>|')
            video_url  = to_https(item.get("videoUrl", "").strip())
            image_url  = to_https(item.get("imageUrl", "").strip())

            print(f"\n🎯 [{safe_name}]")
            print(f"   📎 영상 URL: {video_url}")

            # 50개마다 세션 갱신
            if idx > 0 and idx % 50 == 0:
                print("🔄 세션 자동 갱신...")
                session = init_session()

            # ── 동영상 ──────────────────────────────
            if video_url:
                v_path = os.path.join(VIDEO_DIR, f"{safe_name}.mp4")
                if os.path.exists(v_path) and os.path.getsize(v_path) > 1024:
                    print(f"   ⏭️  이미 존재, 건너뜀")
                else:
                    ok = stream_download(session, video_url, v_path)
                    if ok:
                        kb = os.path.getsize(v_path) // 1024
                        print(f"   ✅ 영상 저장 완료 ({kb}KB)")
                        total_v_ok += 1
                    else:
                        # 1회 재시도
                        print("   🔄 세션 재발급 후 재시도...")
                        session = init_session()
                        ok = stream_download(session, video_url, v_path)
                        if ok:
                            kb = os.path.getsize(v_path) // 1024
                            print(f"   ✅ 재시도 성공 ({kb}KB)")
                            total_v_ok += 1
                        else:
                            total_v_fail += 1

            # ── 이미지 ──────────────────────────────
            if image_url:
                i_path = os.path.join(IMAGE_DIR, f"{safe_name}.jpg")
                if os.path.exists(i_path) and os.path.getsize(i_path) > 1024:
                    print(f"   ⏭️  이미지 이미 존재, 건너뜀")
                else:
                    ok = stream_download(session, image_url, i_path)
                    if ok:
                        print(f"   ✅ 이미지 저장 완료")
                        total_i_ok += 1
                    else:
                        total_i_fail += 1

            time.sleep(DELAY)

    print(f"\n{'🎉'*20}")
    print(f"📊 최종 결과")
    print(f"   영상   성공: {total_v_ok}개 | 실패: {total_v_fail}개")
    print(f"   이미지 성공: {total_i_ok}개 | 실패: {total_i_fail}개")
    print(f"{'🎉'*20}")


if __name__ == "__main__":
    download_media()