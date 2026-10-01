# collector.py
# ------------------------------------------------------------
# 뉴스 수집 + 감성분석 + CSV 저장을 한 곳에 모은 공통 모듈.
# start.py(/collect)와 collectall.py 둘 다 이 파일을 불러다 쓴다.
# 수집 방식을 바꿀 때는 이 파일만 고치면 된다.
#
# 키워드 합치기 규칙
#   - 같은 기사(link)가 여러 키워드에 걸리면 한 행으로 저장하고
#     keyword 칸에 "삼성전자|SK하이닉스"처럼 | 로 이어서 적는다.
#   - 이미 저장된 기사가 새 키워드에 걸리면, 새 행을 만들지 않고
#     기존 행의 keyword 칸에 그 키워드를 추가한다.
# ------------------------------------------------------------
import os
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

CSV_PATH = "news_sentiment.csv"

# CSV 열 순서는 여기 한 곳에서만 정한다.
COLUMNS = ["keyword", "title", "label", "score", "collected_at", "link"]

# keyword 칸 안에서 여러 키워드를 이을 때 쓰는 구분자
# 쉼표를 쓰면 CSV 칸이 나뉘어 버리므로 | 를 쓴다.
KEYWORD_SEP = "|"

# ------------------------------------------------------------
# 키워드별 동의어/관련어 사전
# 여기 적힌 순서가 keyword 칸에 이어 적을 때의 순서가 된다.
# ------------------------------------------------------------
KEYWORD_SYNONYMS = {
    "삼성전자": ["삼성전자", "삼성 전자", "삼성전자우"],
    "SK하이닉스": ["SK하이닉스", "하이닉스"],
    "코스피": ["코스피", "코스피지수", "코스피200"],
}


# ------------------------------------------------------------
# 감성분석 모델 (처음 필요할 때 한 번만 로드)
# ------------------------------------------------------------
_classifier = None


def get_classifier():
    global _classifier
    if _classifier is None:
        from transformers import pipeline
        _classifier = pipeline("sentiment-analysis", model="snunlp/KR-FinBert-SC")
    return _classifier


# ------------------------------------------------------------
# keyword 칸 다루기
# ------------------------------------------------------------
def split_keywords(value):
    """'삼성전자|SK하이닉스' -> ['삼성전자', 'SK하이닉스']"""
    if not isinstance(value, str) or value == "":
        return []
    return [k for k in value.split(KEYWORD_SEP) if k]


def join_keywords(keywords):
    """중복을 없애고 KEYWORD_SYNONYMS 순서대로 정렬해서 | 로 잇는다."""
    order = list(KEYWORD_SYNONYMS.keys())
    unique = list(dict.fromkeys(keywords))
    unique.sort(key=lambda k: (order.index(k) if k in order else len(order), k))
    return KEYWORD_SEP.join(unique)


def filter_by_keyword(df, keyword):
    """keyword 칸에 해당 키워드가 들어 있는 행만 남긴다. (조회 엔드포인트용)"""
    mask = df["keyword"].apply(lambda v: keyword in split_keywords(v))
    return df[mask]


# ------------------------------------------------------------
# 수집
# ------------------------------------------------------------
def is_title_relevant(title, keyword, min_hits=1):
    """제목에 키워드(또는 동의어)가 min_hits번 이상 등장하는지 확인."""
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

        if not is_title_relevant(title, keyword, min_hits=min_hits):
            continue

        # 같은 실행 안에서 제목이 똑같은 기사는 하나만 남김 (사진기사 등)
        if title in seen_titles:
            continue
        seen_titles.add(title)

        articles.append({
            "title": title,
            "link": parent_a.get("href"),
        })

    return articles


# ------------------------------------------------------------
# 저장
# ------------------------------------------------------------
def load_existing():
    """기존 CSV를 읽고 형식이 맞는지 확인한다. 없으면 빈 DataFrame."""
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame(columns=COLUMNS)

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    if list(df.columns) != COLUMNS:
        raise ValueError(
            f"{CSV_PATH}의 열 순서가 예상과 다릅니다.\n"
            f"  파일: {list(df.columns)}\n"
            f"  예상: {COLUMNS}\n"
            f"repair_csv.py로 먼저 정리하세요."
        )

    if df["link"].duplicated().any():
        raise ValueError(
            f"{CSV_PATH}에 같은 link가 여러 행 있습니다. "
            f"repair_csv.py로 먼저 합치세요."
        )

    return df


def write_all(df):
    """CSV 전체를 다시 쓴다. 임시 파일에 먼저 쓰고 바꿔치기해서 중간에 깨지지 않게 한다."""
    tmp_path = CSV_PATH + ".tmp"
    df[COLUMNS].to_csv(tmp_path, index=False, encoding="utf-8-sig")
    os.replace(tmp_path, CSV_PATH)


def collect_many(keywords, count=10, min_hits=1):
    """
    여러 키워드를 한 번에 수집해서 합친 뒤 저장한다.

    1) 키워드마다 검색 -> 제목 필터
    2) link 기준으로 합치기 (한 기사에 걸린 키워드를 모음)
    3) 이미 저장된 기사: 빠진 키워드만 기존 행에 추가
       새 기사: 감성분석 한 번 돌리고 새 행으로 추가
    4) 저장

    반환값: 키워드별 결과 목록
      found     : 제목 필터를 통과한 기사 수
      new       : 새로 저장된 기사 수 (다른 키워드와 같이 걸린 것 포함)
      tagged    : 이미 있던 기사에 이 키워드를 새로 붙인 수
      duplicate : 이미 이 키워드로 저장돼 있던 기사 수
    """
    keywords = [k.strip().upper() for k in keywords]

    # 1) 검색
    found = {}                      # keyword -> [article, ...]
    for kw in keywords:
        found[kw] = get_naver_news(kw, count=count, min_hits=min_hits)

    # 2) link 기준으로 합치기 (먼저 나온 제목을 씀)
    merged = {}                     # link -> {"title": ..., "keywords": [...]}
    for kw in keywords:
        for article in found[kw]:
            item = merged.setdefault(article["link"], {"title": article["title"], "keywords": []})
            if kw not in item["keywords"]:
                item["keywords"].append(kw)

    # 3) 기존 데이터와 비교
    existing = load_existing()
    link_to_index = {link: idx for idx, link in zip(existing.index, existing["link"])}

    stats = {kw: {"keyword": kw, "found": len(found[kw]), "new": 0, "tagged": 0, "duplicate": 0}
             for kw in keywords}
    changed_existing = False
    new_items = []

    for link, item in merged.items():
        if link in link_to_index:
            idx = link_to_index[link]
            current = split_keywords(existing.at[idx, "keyword"])
            for kw in item["keywords"]:
                if kw in current:
                    stats[kw]["duplicate"] += 1
                else:
                    current.append(kw)
                    stats[kw]["tagged"] += 1
                    changed_existing = True
            existing.at[idx, "keyword"] = join_keywords(current)
        else:
            new_items.append((link, item))
            for kw in item["keywords"]:
                stats[kw]["new"] += 1

    # 새 기사만 감성분석 (겹친 기사는 한 번만 돌아감)
    new_rows = []
    if new_items:
        classifier = get_classifier()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for link, item in new_items:
            sentiment = classifier(item["title"])[0]
            new_rows.append({
                "keyword": join_keywords(item["keywords"]),
                "title": item["title"],
                "label": sentiment["label"],
                "score": sentiment["score"],
                "collected_at": now,
                "link": link,
            })

    # 4) 저장
    #    기존 행을 고쳤으면 파일 전체를 다시 쓰고, 새 행만 있으면 뒤에 이어 붙인다.
    new_df = pd.DataFrame(new_rows, columns=COLUMNS)

    if changed_existing:
        write_all(pd.concat([existing, new_df], ignore_index=True))
    elif len(new_df) > 0:
        if os.path.exists(CSV_PATH):
            new_df.to_csv(CSV_PATH, mode="a", header=False, index=False, encoding="utf-8-sig")
        else:
            new_df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    return [stats[kw] for kw in keywords]


def collect(keyword, count=10, min_hits=1):
    """키워드 하나만 수집. start.py의 /collect가 쓴다."""
    return collect_many([keyword], count=count, min_hits=min_hits)[0]


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
