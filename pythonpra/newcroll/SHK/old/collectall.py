# collectall.py
# 수집/필터/저장은 전부 collector.py에 있음.
# 여기서는 키워드 3개를 한 번에 넘겨서, 겹치는 기사가 한 행으로 합쳐지게 한다.
# 요청 하나하나의 기록은 request_log.csv에 남는다.
from datetime import datetime

from collector import collect_many, REQUEST_LOG

KEYWORDS = ["삼성전자", "SK하이닉스", "코스피"]

# 검색 페이지 수: 1페이지에 기사 10개. 3이면 키워드당 후보 최대 30개
PAGES = 3

if __name__ == "__main__":
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] 수집 시작")
    results = collect_many(KEYWORDS, count=PAGES * 10, min_hits=1, pages=PAGES)

    for r in results:
        if r["status"].startswith("건너뜀"):
            print(f"{r['keyword']}: {r['status']}")
            continue
        filtered_out = r["candidates"] - r["found"]
        print(f"{r['keyword']}: 후보 {r['candidates']}건({r['pages']}페이지) -> "
              f"필터 통과 {r['found']}건 (탈락 {filtered_out}) -> "
              f"신규 {r['new']}, 기존 기사에 키워드 추가 {r['tagged']}, 중복 {r['duplicate']}"
              f"{'' if r['status'] == '정상' else '  [' + r['status'] + ']'}")

    if any(r["status"] != "정상" for r in results):
        print(f"!! 차단 의심으로 중간에 멈췄습니다. 모은 기사까지는 저장했습니다. "
              f"자세한 기록은 {REQUEST_LOG}를 확인하세요.")
    print("전체 수집 완료")
