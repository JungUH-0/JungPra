# collectall.py
# 수집/필터/저장은 전부 collector.py에 있음. 여기서는 키워드만 돌려준다.
from collector import collect

KEYWORDS = ["삼성전자", "SK하이닉스", "코스피"]

if __name__ == "__main__":
    for kw in KEYWORDS:
        # 네이버 검색은 스크롤 없이 첫 화면에 최대 10개만 나오므로 count는 10이면 충분
        result = collect(kw, count=10, min_hits=1)

        if "message" in result:
            print(f"{result['keyword']}: {result['message']}")
        else:
            print(f"{result['keyword']}: 신규 {result['collected']}건 수집 "
                  f"(중복 {result['duplicates_skipped']}건 제외)")

    print("전체 수집 완료")
