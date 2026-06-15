# import os
# import requests
# import json
# import xml.etree.ElementTree as ET
# from urllib.parse import unquote
# from dotenv import load_dotenv

# # 1. .env 로드 및 API 키 가져오기
# env_path = r"D:\JungPra\pythonpra\signlan\.env"
# load_dotenv(dotenv_path=env_path)

# API_KEY = os.environ.get("CULTURE_API_KEY")
# if API_KEY:
#     API_KEY = unquote(API_KEY.strip())

# BASE_URL = "http://api.kcisa.kr/openapi/service/rest/meta13/getCTE01701"

# # 저장 폴더 설정
# BASE_DIR = r"D:\JungPra\pythonpra\signlan"
# SAVE_DIR = os.path.join(BASE_DIR, "raw_json")
# os.makedirs(SAVE_DIR, exist_ok=True)

# def fetch_sign_language_xml():
#     if not API_KEY:
#         print("❌ 에러: .env 파일에서 키를 읽지 못했습니다.")
#         return

#     # curl로 성공하셨던 검증된 주소 조합 그대로 사용합니다.
#     final_url = f"{BASE_URL}?serviceKey={API_KEY}&numOfRows=10&pageNo=1"
    
#     print("🔄 서버에 데이터를 요청 중입니다 (XML 대응 모드)...")
    
#     try:
#         response = requests.get(final_url, timeout=10)
        
#         if response.status_code == 200:
#             print("📡 서버 응답 성공! XML 데이터 파싱을 시작합니다.")
            
#             # XML 데이터 파싱
#             root = ET.fromstring(response.text.strip())
            
#             # AI 학습에 쓰기 편하게 JSON(dict) 구조로 변환할 리스트
#             sign_items = []
            
#             # XML에서 각 <item> 태그를 찾아서 반복문 처리
#             for item in root.findall('.//item'):
#                 item_dict = {
#                     "title": item.findtext('title', '').strip(),                        # 수어 단어 명칭
#                     "alternativeTitle": item.findtext('alternativeTitle', '').strip(),  # 대체 명칭
#                     "regDate": item.findtext('regDate', '').strip(),                    # 등록 날짜
#                     "collectionDb": item.findtext('collectionDb', '').strip(),          # 컬렉션 이름
#                     "imageUrl": item.findtext('referenceIdentifier', '').strip(),       # 수어 대표 이미지 URL
#                     "videoUrl": item.findtext('subDescription', '').strip(),            # 수어 동영상 URL
#                     "description": item.findtext('signDescription', '').strip(),        # 수어 설명 텍스트
#                     "signImages": item.findtext('signImages', '').strip()                # 연속 동작 이미지들
#                 }
#                 sign_items = [item_dict] + sign_items # 리스트에 누적
            
#             # 최종 정형화된 데이터 구조 생성
#             final_data = {
#                 "totalCount": len(sign_items),
#                 "items": sign_items
#             }
            
#             # 화면에 변환된 데이터 샘플 출력 (첫 번째 아이템만 보기 좋게)
#             if sign_items:
#                 print("\n=== [변환 가공 완료된 데이터 샘플] ===")
#                 print(json.dumps(sign_items[0], ensure_ascii=False, indent=2))
#                 print("========================================\n")
            
#             # 💾 파일 저장 완료
#             output_filepath = os.path.join(SAVE_DIR, "test_page_1.json")
#             with open(output_filepath, "w", encoding="utf-8") as f:
#                 json.dump(final_data, f, ensure_ascii=False, indent=4)
                
#             print(f"💾 [성공] 공공 API 데이터를 깔끔한 JSON 파일로 가공하여 저장했습니다!")
#             print(f"📂 저장 경로: {output_filepath}")
            
#         else:
#             print(f"❌ API 연결 실패 (HTTP 상태 코드: {response.status_code})")
            
#     except Exception as e:
#         print(f"❌ 오류 발생: {e}")

# if __name__ == "__main__":
#     fetch_sign_language_xml()

import os
import requests
import json
import time
import xml.etree.ElementTree as ET
from urllib.parse import unquote
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# 설정값 json 파일 생성
# ──────────────────────────────────────────────
env_path = r"D:\JungPra\pythonpra\signlan\.env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.environ.get("CULTURE_API_KEY")
if API_KEY:
    API_KEY = unquote(API_KEY.strip())

BASE_URL = "http://api.kcisa.kr/openapi/service/rest/meta13/getCTE01701"
BASE_DIR = r"D:\JungPra\pythonpra\signlan"
SAVE_DIR = os.path.join(BASE_DIR, "raw_json")
os.makedirs(SAVE_DIR, exist_ok=True)

ROWS_PER_PAGE = 10   # 페이지당 항목 수
DELAY_SEC     = 1    # 페이지 간 대기 (서버 보호)


def fetch_multi_pages(start_page=1, end_page=10):
    if not API_KEY:
        print("❌ .env 파일에서 API 키를 읽지 못했습니다.")
        return

    print(f"🚀 {start_page}페이지 ~ {end_page}페이지 수집 시작")
    print(f"   예상 데이터: 최대 {(end_page - start_page + 1) * ROWS_PER_PAGE}개\n")

    total_items = 0
    fail_pages  = []

    for page in range(start_page, end_page + 1):
        url = f"{BASE_URL}?serviceKey={API_KEY}&numOfRows={ROWS_PER_PAGE}&pageNo={page}"
        print(f"🔄 [{page:02d}/{end_page}페이지] 요청 중...")

        try:
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                print(f"   ❌ HTTP {response.status_code} → 건너뜀")
                fail_pages.append(page)
                continue

            root       = ET.fromstring(response.text.strip())
            sign_items = []

            for item in root.findall('.//item'):
                sign_items.append({
                    "title":            item.findtext('title',               '').strip(),
                    "alternativeTitle": item.findtext('alternativeTitle',    '').strip(),
                    "regDate":          item.findtext('regDate',             '').strip(),
                    "collectionDb":     item.findtext('collectionDb',        '').strip(),
                    "imageUrl":         item.findtext('referenceIdentifier', '').strip(),
                    "videoUrl":         item.findtext('subDescription',      '').strip(),
                    "description":      item.findtext('signDescription',     '').strip(),
                    "signImages":       item.findtext('signImages',          '').strip(),
                })

            if not sign_items:
                print(f"   ⚠️  데이터 없음 → 마지막 페이지일 수 있음, 종료")
                break

            save_path = os.path.join(SAVE_DIR, f"test_page_{page:03d}.json")
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump({"totalCount": len(sign_items), "items": sign_items},
                          f, ensure_ascii=False, indent=4)

            total_items += len(sign_items)
            print(f"   ✅ {len(sign_items)}개 저장 완료 → test_page_{page:03d}.json")

        except ET.ParseError:
            print(f"   ❌ XML 파싱 실패 (응답이 XML이 아님)")
            fail_pages.append(page)
        except requests.exceptions.Timeout:
            print(f"   ⏱️  타임아웃 → 건너뜀")
            fail_pages.append(page)
        except Exception as e:
            print(f"   ❌ 에러: {e}")
            fail_pages.append(page)

        print("-" * 50)
        time.sleep(DELAY_SEC)

    # ── 결과 요약 ──
    print(f"\n{'='*50}")
    print(f"📊 수집 완료!")
    print(f"   총 수집 항목: {total_items}개")
    print(f"   실패 페이지: {fail_pages if fail_pages else '없음'}")
    print(f"   저장 폴더: {SAVE_DIR}")
    print(f"{'='*50}")


if __name__ == "__main__":
    fetch_multi_pages(start_page=1, end_page=50)  # ← 숫자 바꾸면 더 많이 수집 가능