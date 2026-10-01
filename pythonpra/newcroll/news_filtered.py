import requests
from bs4 import BeautifulSoup

# ------------------------------------------------------------
# 키워드별 동의어/관련어 사전
# 검색 키워드가 "코스피"여도 기사 제목엔 "코스피" 대신
# "코스피지수", "증시" 같은 표현만 있을 수 있어서, 동의어 목록을 같이 둠
# ------------------------------------------------------------
KEYWORD_SYNONYMS = {
    "코스피": ["코스피", "코스피지수", "증시", "국내증시"],
    "삼성전자": ["삼성전자", "삼성전자우"],
    "하이닉스": ["하이닉스", "SK하이닉스"],
}


def is_title_relevant(title, keyword, min_hits=1):
    """
    제목에 키워드(또는 동의어)가 min_hits번 이상 등장하는지 확인.
    지금처럼 "본문 마지막에 관련 없는 한 줄"만 있고,
    제목 자체엔 키워드가 안 들어간 기사를 걸러내는 용도.
    """
    synonyms = KEYWORD_SYNONYMS.get(keyword, [keyword])
    hit_count = sum(title.count(word) for word in synonyms)
    return hit_count >= min_hits


def get_naver_news(keyword, count=10, min_hits=1):
    url = "https://search.naver.com/search.naver"
    params = {"where": "news", "query": keyword, "sort": "1"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    res = requests.get(url, params=params, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    articles = []
    # 필터링 후에도 count개를 채우기 위해, 넉넉하게 더 많이 훑어봄
    title_spans = soup.select("span.sds-comps-text-type-headline1")[:count * 3]

    for span in title_spans:
        if len(articles) >= count:
            break

        parent_a = span.find_parent("a")
        if not parent_a:
            continue

        title = span.get_text(strip=True)

        # ---- 레벨 1: 제목에 키워드(동의어 포함)가 있는지 확인 ----
        if not is_title_relevant(title, keyword, min_hits=min_hits):
            continue

        articles.append({
            "title": title,
            "link": parent_a.get("href")
        })

    return articles


# ------------------------------------------------------------
# [레벨 2 - 필요시 주석 해제해서 사용]
# 본문까지 들어가서 키워드 등장 횟수를 세는 더 정확한 필터.
# 요청이 기사 수만큼 추가로 나가므로 (예: count=10이면 최대 30번 요청)
# 속도가 느려지고 서버 부담도 커짐. 레벨 1로 부족할 때만 켤 것.
# ------------------------------------------------------------
"""
import time

def get_article_body(link):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(link, headers=headers, timeout=5)
        time.sleep(1)
    except Exception:
        return ""

    if res.status_code != 200:
        return ""

    soup = BeautifulSoup(res.text, "html.parser")
    # 네이버 뉴스 본문 영역 class는 매체별/버전별로 다를 수 있어서
    # 실제 대상 사이트에서 직접 확인 후 아래 셀렉터를 맞춰야 함
    body_tag = soup.select_one("article#dic_area") or soup.select_one("div#articleBodyContents")
    return body_tag.get_text(strip=True) if body_tag else ""


def is_body_relevant(link, keyword, min_hits=3):
    synonyms = KEYWORD_SYNONYMS.get(keyword, [keyword])
    body_text = get_article_body(link)
    hit_count = sum(body_text.count(word) for word in synonyms)
    return hit_count >= min_hits


def get_naver_news_strict(keyword, count=10, title_min_hits=1, body_min_hits=3):
    # 레벨 1(제목)로 1차 필터링한 뒤, 레벨 2(본문)로 한 번 더 검증
    candidates = get_naver_news(keyword, count=count * 2, min_hits=title_min_hits)

    articles = []
    for article in candidates:
        if len(articles) >= count:
            break
        if is_body_relevant(article["link"], keyword, min_hits=body_min_hits):
            articles.append(article)

    return articles
"""


if __name__ == "__main__":
    results = get_naver_news("코스피", count=10, min_hits=1)
    for r in results:
        print(r["title"])
        print(r["link"])
        print("-" * 40)
