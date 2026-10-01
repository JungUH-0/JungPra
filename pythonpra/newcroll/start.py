# from fastapi import FastAPI
# from bs4 import BeautifulSoup
# from transformers import pipeline
# import requests
# import pandas as pd
# import os
# from datetime import datetime

# app = FastAPI()

# # 모델은 서버 시작할 때 딱 한 번만 로드 (요청마다 로드하면 매우 느려짐)
# classifier = pipeline("sentiment-analysis", model="snunlp/KR-FinBert-SC")

# CSV_PATH = "news_sentiment.csv"


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


# @app.post("/collect")
# def collect(keyword: str, count: int = 10):
#     keyword = keyword.strip().upper()

#     articles = get_naver_news(keyword, count=count)

#     rows = []
#     for article in articles:
#         sentiment = classifier(article["title"])[0]
#         rows.append({
#             "keyword": keyword,
#             "title": article["title"],
#             "label": sentiment["label"],
#             "score": sentiment["score"],
#             "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "link": article["link"]

#         })

#     new_df = pd.DataFrame(rows)

#     if os.path.exists(CSV_PATH):
#         existing_df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
#         # 이미 저장된 link는 제외하고, 진짜 새 기사만 남김 (중복 수집 방지)
#         new_df = new_df[~new_df["link"].isin(existing_df["link"])]

#         if len(new_df) > 0:
#             new_df.to_csv(CSV_PATH, mode="a", header=False, index=False, encoding="utf-8-sig")
#     else:
#         new_df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

#     return {
#         "collected": len(new_df),
#         "keyword": keyword,
#         "duplicates_skipped": len(rows) - len(new_df)
#     }


# @app.get("/sentiment/{keyword}")
# def sentiment(keyword: str):
#     keyword = keyword.strip().upper()

#     if not os.path.exists(CSV_PATH):
#         return {"error": "아직 수집된 데이터가 없습니다"}

#     df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
#     df_filtered = df[df["keyword"] == keyword]

#     if len(df_filtered) == 0:
#         return {"error": f"'{keyword}'에 대한 데이터가 없습니다"}

#     label_counts = df_filtered["label"].value_counts().to_dict()
#     total = len(df_filtered)

#     return {
#         "keyword": keyword,
#         "total_articles": total,
#         "label_counts": label_counts,
#         "label_ratio": {k: round(v / total, 2) for k, v in label_counts.items()},
#         "avg_score": round(df_filtered["score"].mean(), 3)
#     }


# @app.get("/compare")
# def compare(keywords: str):
#     if not os.path.exists(CSV_PATH):
#         return {"error": "아직 수집된 데이터가 없습니다"}

#     df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
#     keyword_list = [k.strip().upper() for k in keywords.split(",")]

#     result = {}
#     for keyword in keyword_list:
#         df_filtered = df[df["keyword"] == keyword]

#         if len(df_filtered) == 0:
#             result[keyword] = {"error": "데이터 없음"}
#             continue

#         label_counts = df_filtered["label"].value_counts().to_dict()
#         total = len(df_filtered)

#         result[keyword] = {
#             "total_articles": total,
#             "label_ratio": {k: round(v / total, 2) for k, v in label_counts.items()},
#             "avg_score": round(df_filtered["score"].mean(), 3)
#         }

#     ranking = sorted(
#         [(k, v.get("label_ratio", {}).get("positive", 0)) for k, v in result.items() if "error" not in v],
#         key=lambda x: x[1],
#         reverse=True
#     )

#     return {
#         "compared_keywords": keyword_list,
#         "details": result,
#         "positive_ranking": [{"keyword": k, "positive_ratio": r} for k, r in ranking]
#     }


# @app.get("/trend/{keyword}")
# def trend(keyword: str, days: int = 7):
#     keyword = keyword.strip().upper()

#     if not os.path.exists(CSV_PATH):
#         return {"error": "아직 수집된 데이터가 없습니다"}

#     df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
#     df_filtered = df[df["keyword"] == keyword].copy()

#     if len(df_filtered) == 0:
#         return {"error": f"'{keyword}'에 대한 데이터가 없습니다"}

#     df_filtered["date"] = pd.to_datetime(df_filtered["collected_at"]).dt.date

#     cutoff = pd.Timestamp.now().date() - pd.Timedelta(days=days)
#     df_filtered = df_filtered[df_filtered["date"] >= cutoff]

#     if len(df_filtered) == 0:
#         return {"error": f"최근 {days}일간 데이터가 없습니다"}

#     daily_stats = df_filtered.groupby("date").agg(
#         total_articles=("label", "count"),
#         avg_score=("score", "mean")
#     ).reset_index()

#     daily_sentiment = df_filtered.groupby(["date", "label"]).size().unstack(fill_value=0)

#     trend_list = []
#     for date in daily_stats["date"]:
#         row = daily_stats[daily_stats["date"] == date].iloc[0]
#         sentiment_row = daily_sentiment.loc[date] if date in daily_sentiment.index else {}

#         trend_list.append({
#             "date": str(date),
#             "total_articles": int(row["total_articles"]),
#             "avg_score": round(row["avg_score"], 3),
#             "positive": int(sentiment_row.get("positive", 0)),
#             "neutral": int(sentiment_row.get("neutral", 0)),
#             "negative": int(sentiment_row.get("negative", 0))
#         })

#     return {
#         "keyword": keyword,
#         "period_days": days,
#         "trend": trend_list
#     }

# uvicorn start:app --reload

from fastapi import FastAPI
from bs4 import BeautifulSoup
from transformers import pipeline
import requests
import pandas as pd
import os
from datetime import datetime

app = FastAPI()

# 모델은 서버 시작할 때 딱 한 번만 로드 (요청마다 로드하면 매우 느려짐)
classifier = pipeline("sentiment-analysis", model="snunlp/KR-FinBert-SC")

CSV_PATH = "news_sentiment.csv"


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
    candidates = get_naver_news(keyword, count=count * 2, min_hits=title_min_hits)

    articles = []
    for article in candidates:
        if len(articles) >= count:
            break
        if is_body_relevant(article["link"], keyword, min_hits=body_min_hits):
            articles.append(article)

    return articles
"""


@app.post("/collect")
def collect(keyword: str, count: int = 10, min_hits: int = 1):
    keyword = keyword.strip().upper()

    articles = get_naver_news(keyword, count=count, min_hits=min_hits)

    rows = []
    for article in articles:
        sentiment = classifier(article["title"])[0]
        rows.append({
            "keyword": keyword,
            "title": article["title"],
            "label": sentiment["label"],
            "score": sentiment["score"],
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "link": article["link"]

        })

    new_df = pd.DataFrame(rows)

    if os.path.exists(CSV_PATH):
        existing_df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        # 이미 저장된 link는 제외하고, 진짜 새 기사만 남김 (중복 수집 방지)
        new_df = new_df[~new_df["link"].isin(existing_df["link"])]

        if len(new_df) > 0:
            new_df.to_csv(CSV_PATH, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        new_df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    return {
        "collected": len(new_df),
        "keyword": keyword,
        "duplicates_skipped": len(rows) - len(new_df)
    }


@app.get("/sentiment/{keyword}")
def sentiment(keyword: str):
    keyword = keyword.strip().upper()

    if not os.path.exists(CSV_PATH):
        return {"error": "아직 수집된 데이터가 없습니다"}

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df_filtered = df[df["keyword"] == keyword]

    if len(df_filtered) == 0:
        return {"error": f"'{keyword}'에 대한 데이터가 없습니다"}

    label_counts = df_filtered["label"].value_counts().to_dict()
    total = len(df_filtered)

    return {
        "keyword": keyword,
        "total_articles": total,
        "label_counts": label_counts,
        "label_ratio": {k: round(v / total, 2) for k, v in label_counts.items()},
        "avg_score": round(df_filtered["score"].mean(), 3)
    }


@app.get("/compare")
def compare(keywords: str):
    if not os.path.exists(CSV_PATH):
        return {"error": "아직 수집된 데이터가 없습니다"}

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    keyword_list = [k.strip().upper() for k in keywords.split(",")]

    result = {}
    for keyword in keyword_list:
        df_filtered = df[df["keyword"] == keyword]

        if len(df_filtered) == 0:
            result[keyword] = {"error": "데이터 없음"}
            continue

        label_counts = df_filtered["label"].value_counts().to_dict()
        total = len(df_filtered)

        result[keyword] = {
            "total_articles": total,
            "label_ratio": {k: round(v / total, 2) for k, v in label_counts.items()},
            "avg_score": round(df_filtered["score"].mean(), 3)
        }

    ranking = sorted(
        [(k, v.get("label_ratio", {}).get("positive", 0)) for k, v in result.items() if "error" not in v],
        key=lambda x: x[1],
        reverse=True
    )

    return {
        "compared_keywords": keyword_list,
        "details": result,
        "positive_ranking": [{"keyword": k, "positive_ratio": r} for k, r in ranking]
    }


@app.get("/trend/{keyword}")
def trend(keyword: str, days: int = 7):
    keyword = keyword.strip().upper()

    if not os.path.exists(CSV_PATH):
        return {"error": "아직 수집된 데이터가 없습니다"}

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df_filtered = df[df["keyword"] == keyword].copy()

    if len(df_filtered) == 0:
        return {"error": f"'{keyword}'에 대한 데이터가 없습니다"}

    df_filtered["date"] = pd.to_datetime(df_filtered["collected_at"]).dt.date

    cutoff = pd.Timestamp.now().date() - pd.Timedelta(days=days)
    df_filtered = df_filtered[df_filtered["date"] >= cutoff]

    if len(df_filtered) == 0:
        return {"error": f"최근 {days}일간 데이터가 없습니다"}

    daily_stats = df_filtered.groupby("date").agg(
        total_articles=("label", "count"),
        avg_score=("score", "mean")
    ).reset_index()

    daily_sentiment = df_filtered.groupby(["date", "label"]).size().unstack(fill_value=0)

    trend_list = []
    for date in daily_stats["date"]:
        row = daily_stats[daily_stats["date"] == date].iloc[0]
        sentiment_row = daily_sentiment.loc[date] if date in daily_sentiment.index else {}

        trend_list.append({
            "date": str(date),
            "total_articles": int(row["total_articles"]),
            "avg_score": round(row["avg_score"], 3),
            "positive": int(sentiment_row.get("positive", 0)),
            "neutral": int(sentiment_row.get("neutral", 0)),
            "negative": int(sentiment_row.get("negative", 0))
        })

    return {
        "keyword": keyword,
        "period_days": days,
        "trend": trend_list
    }

# uvicorn start:app --reload