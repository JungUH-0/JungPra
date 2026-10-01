# # collect_all.py
# import requests
# from bs4 import BeautifulSoup
# from transformers import pipeline
# import pandas as pd
# import os
# from datetime import datetime

# CSV_PATH = "news_sentiment.csv"

# classifier = pipeline("sentiment-analysis", model="snunlp/KR-FinBert-SC")


# def get_naver_news(keyword, count=10):
#     url = "https://search.naver.com/search.naver"
#     params = {"where": "news", "query": keyword, "sort": "1"}
#     headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

#     res = requests.get(url, params=params, headers=headers)
#     soup = BeautifulSoup(res.text, "html.parser")

#     articles = []
#     title_spans = soup.select("span.sds-comps-text-type-headline1")[:count]
#     for span in title_spans:
#         parent_a = span.find_parent("a")
#         if parent_a:
#             articles.append({
#                 "title": span.get_text(strip=True),
#                 "link": parent_a.get("href")
#             })
#     return articles


# def collect(keyword, count=10):
#     keyword = keyword.strip().upper()
#     articles = get_naver_news(keyword, count=count)

#     rows = []
#     for article in articles:
#         sentiment = classifier(article["title"])[0]
#         rows.append({
#             "keyword": keyword,
#             "title": article["title"],
#             "link": article["link"],
#             "label": sentiment["label"],
#             "score": sentiment["score"],
#             "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         })

#     new_df = pd.DataFrame(rows)

#     if os.path.exists(CSV_PATH):
#         existing_df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
#         new_df = new_df[~new_df["link"].isin(existing_df["link"])]
#         if len(new_df) > 0:
#             new_df.to_csv(CSV_PATH, mode="a", header=False, index=False, encoding="utf-8-sig")
#     else:
#         new_df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

#     print(f"{keyword}: 신규 {len(new_df)}건 수집 (중복 {len(rows) - len(new_df)}건 제외)")


# if __name__ == "__main__":
#     keywords = ["삼성전자", "SK하이닉스", "코스피"]
#     for kw in keywords:
#         collect(kw, count=10)

#     print("전체 수집 완료")


# collect_all.py
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import pandas as pd
import os
from datetime import datetime

CSV_PATH = "news_sentiment.csv"

classifier = pipeline("sentiment-analysis", model="snunlp/KR-FinBert-SC")


# ------------------------------------------------------------
# 키워드별 동의어/관련어 사전
# 검색 키워드가 "코스피"여도 기사 제목엔 "코스피" 대신
# "코스피지수", "증시" 같은 표현만 있을 수 있어서, 동의어 목록을 같이 둠
# 필요한 키워드가 늘어나면 여기에 계속 추가하면 됨
# ------------------------------------------------------------
KEYWORD_SYNONYMS = {
    "삼성전자": ["삼성전자", "삼성 전자", "삼성전자우",],
    "SK하이닉스": ["SK하이닉스", "하이닉스"],
    "코스피": ["코스피", "코스피지수", "코스피200"],
}


def is_title_relevant(title, keyword, min_hits=1):
    """
    제목에 키워드(또는 동의어)가 min_hits번 이상 등장하는지 확인.
    "본문 마지막에 관련 없는 한 줄"만 있고 제목엔 키워드가 안 들어간
    기사를 걸러내기 위한 필터.
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
    # 필터링 후에도 count개를 채우기 위해 넉넉하게 더 많이 훑어봄
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
# 요청이 기사 수만큼 추가로 나가므로 속도가 느려지고 서버 부담도 커짐.
# 레벨 1(제목 필터)로도 걸러지지 않는 기사가 많을 때만 켤 것.
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
    # 본문 영역 class는 매체별/버전별로 다를 수 있어서
    # 실제 대상 기사 사이트에서 직접 확인 후 셀렉터를 맞춰야 함
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


def collect(keyword, count=10, min_hits=1):
    keyword = keyword.strip().upper()
    # min_hits 계산은 원본 키워드(대문자 변환 전) 기준으로 사전을 찾아야 하므로
    # KEYWORD_SYNONYMS 키도 대문자로 맞춰 등록해두거나, 아래처럼 원본을 따로 넘겨줌
    articles = get_naver_news(keyword, count=count, min_hits=min_hits)

    rows = []
    for article in articles:
        sentiment = classifier(article["title"])[0]
        rows.append({
            "keyword": keyword,
            "title": article["title"],
            "link": article["link"],
            "label": sentiment["label"],
            "score": sentiment["score"],
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    # 필터 조건이 너무 엄격했거나 이번 요청에서 관련 기사가 하나도 안 걸렸을 때
    # rows가 빈 리스트가 되고, 그러면 DataFrame에 컬럼 자체가 없어서
    # 바로 다음의 new_df["link"] 비교에서 KeyError가 납니다. 여기서 미리 걸러줍니다.
    if len(rows) == 0:
        print(f"{keyword}: 조건에 맞는 기사가 없어 건너뜀 (min_hits={min_hits})")
        return

    new_df = pd.DataFrame(rows)

    if os.path.exists(CSV_PATH):
        existing_df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        new_df = new_df[~new_df["link"].isin(existing_df["link"])]
        if len(new_df) > 0:
            new_df.to_csv(CSV_PATH, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        new_df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    print(f"{keyword}: 신규 {len(new_df)}건 수집 (중복 {len(rows) - len(new_df)}건 제외)")


if __name__ == "__main__":
    keywords = ["삼성전자", "SK하이닉스", "코스피"]
    for kw in keywords:
        collect(kw, count=20, min_hits=1)
        #https://search.naver.com/search.naver -> 네이버 검색이 스크롤없이는 최대 10개까지가 최대 그 후엔 추가 동작이 필요해서 의미가 없음 추가 기능을 적용해야함

    print("전체 수집 완료")