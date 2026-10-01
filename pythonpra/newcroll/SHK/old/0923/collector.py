# collector.py
# ------------------------------------------------------------
# 뉴스 수집 + 감성분석 + CSV 저장을 한 곳에 모은 공통 모듈.
# start.py(/collect)와 collect_all.py 둘 다 이 파일을 불러다 쓴다.
# 수집 방식을 바꿀 때는 이 파일만 고치면 된다.
# ------------------------------------------------------------
import os
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

CSV_PATH = "news_sentiment.csv"

# CSV 열 순서는 여기 한 곳에서만 정한다.
# 저장할 때 항상 이 순서로 맞춰서 쓰기 때문에, 열이 밀리는 일이 다시 생기지 않는다.
COLUMNS = ["keyword", "title", "label", "score", "collected_at", "link"]

# ------------------------------------------------------------
# 키워드별 동의어/관련어 사전
# 필요한 키워드가 늘어나면 여기에 계속 추가하면 됨
# ------------------------------------------------------------
KEYWORD_SYNONYMS = {
    "삼성전자": ["삼성전자", "삼성 전자", "삼성전자우"],
    "SK하이닉스": ["SK하이닉스", "하이닉스"],
    "코스피": ["코스피", "코스피지수", "코스피200"],
}


# ------------------------------------------------------------
# 감성분석 모델
# 처음 필요할 때 한 번만 로드해서 계속 재사용한다.
# (import만 했을 때 바로 로드하지 않아서, 조회만 하는 경우엔 모델을 안 불러옴)
# ------------------------------------------------------------
_classifier = None


def get_classifier():
    global _classifier
    if _classifier is None:
        from transformers import pipeline
        _classifier = pipeline("sentiment-analysis", model="snunlp/KR-FinBert-SC")
    return _classifier


def is_title_relevant(title, keyword, min_hits=1):
    """
    제목에 키워드(또는 동의어)가 min_hits번 이상 등장하는지 확인.
    검색엔진이 관련 있다고 끼워넣었지만 제목엔 키워드가 없는 기사를 걸러낸다.
    """
    synonyms = KEYWORD_SYNONYMS.get(keyword, [keyword])
    hit_count = sum(title.count(word) for word in synonyms)
    return hit_count >= min_hits


def get_naver_news(keyword, count=10, min_hits=1):
    url = "https://search.naver.com/search.naver"
    params = {"where": "news", "query": keyword, "sort": "1"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    res = requests.get(url, params=params, headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")

    articles = []
    seen_titles = set()
    # 스크롤 없이 받아오는 첫 화면은 최대 10개라, count를 늘려도 그 이상은 안 나온다.
    title_spans = soup.select("span.sds-comps-text-type-headline1")[:count * 3]

    for span in title_spans:
        if len(articles) >= count:
            break

        parent_a = span.find_parent("a")
        if not parent_a:
            continue

        title = span.get_text(strip=True)

        # 제목에 키워드(동의어 포함)가 있는지 확인
        if not is_title_relevant(title, keyword, min_hits=min_hits):
            continue

        # 같은 실행 안에서 제목이 똑같은 기사는 하나만 남김
        # (연합뉴스 사진기사처럼 사진만 다르고 설명 문구가 같은 경우)
        if title in seen_titles:
            continue
        seen_titles.add(title)

        articles.append({
            "title": title,
            "link": parent_a.get("href"),
        })

    return articles


def save_rows(rows):
    """
    수집한 행들을 CSV에 이어 붙인다.
    - 이미 저장된 link는 건너뜀
    - 항상 COLUMNS 순서로 맞춰서 저장
    - 기존 CSV의 헤더가 COLUMNS와 다르면 저장하지 않고 에러를 낸다
      (조용히 이어 붙이다 열이 밀리는 사고를 막기 위함)
    반환값: 실제로 저장된 행 수
    """
    if len(rows) == 0:
        return 0

    new_df = pd.DataFrame(rows)
    new_df = new_df[COLUMNS]
    new_df = new_df.drop_duplicates(subset="link")

    if os.path.exists(CSV_PATH):
        existing_df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

        if list(existing_df.columns) != COLUMNS:
            raise ValueError(
                f"{CSV_PATH}의 열 순서가 예상과 다릅니다.\n"
                f"  파일: {list(existing_df.columns)}\n"
                f"  예상: {COLUMNS}\n"
                f"repair_csv.py로 먼저 정리하세요."
            )

        new_df = new_df[~new_df["link"].isin(existing_df["link"])]
        if len(new_df) > 0:
            new_df.to_csv(CSV_PATH, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        new_df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    return len(new_df)


def collect(keyword, count=10, min_hits=1):
    """
    키워드 하나에 대해 수집 -> 감성분석 -> 저장까지 한 번에 처리.
    start.py의 /collect와 collect_all.py가 둘 다 이 함수를 호출한다.
    """
    keyword = keyword.strip().upper()
    articles = get_naver_news(keyword, count=count, min_hits=min_hits)

    if len(articles) == 0:
        return {
            "keyword": keyword,
            "collected": 0,
            "duplicates_skipped": 0,
            "message": f"조건에 맞는 기사가 없어 건너뜀 (min_hits={min_hits})",
        }

    classifier = get_classifier()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    for article in articles:
        sentiment = classifier(article["title"])[0]
        rows.append({
            "keyword": keyword,
            "title": article["title"],
            "label": sentiment["label"],
            "score": sentiment["score"],
            "collected_at": now,
            "link": article["link"],
        })

    saved = save_rows(rows)

    return {
        "keyword": keyword,
        "collected": saved,
        "duplicates_skipped": len(rows) - saved,
    }


# ------------------------------------------------------------
# [레벨 2 - 필요시 주석 해제해서 사용]
# 본문까지 들어가서 키워드 등장 횟수를 세는 더 정확한 필터.
# 요청이 기사 수만큼 추가로 나가므로 속도가 느려지고 서버 부담도 커짐.
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
    # 본문 영역 class는 매체별로 다를 수 있어서 실제 사이트에서 확인 후 맞춰야 함
    body_tag = soup.select_one("article#dic_area") or soup.select_one("div#articleBodyContents")
    return body_tag.get_text(strip=True) if body_tag else ""


def is_body_relevant(link, keyword, min_hits=3):
    synonyms = KEYWORD_SYNONYMS.get(keyword, [keyword])
    body_text = get_article_body(link)
    hit_count = sum(body_text.count(word) for word in synonyms)
    return hit_count >= min_hits


def get_naver_news_strict(keyword, count=10, title_min_hits=1, body_min_hits=3):
    candidates = get_naver_news(keyword, count=count * 2, min_hits=title_min_hits)

    articles = []
    for article in candidates:
        if len(articles) >= count:
            break
        if is_body_relevant(article["link"], keyword, min_hits=body_min_hits):
            articles.append(article)

    return articles
"""
