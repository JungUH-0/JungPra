from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import os

# 수집/필터/저장은 전부 collector.py에 있음
from collector import CSV_PATH, KEYWORD_SYNONYMS, collect as run_collect, filter_by_keyword
# 주가 비교 계산은 validate_stock.py에 있음
import validate_stock

app = FastAPI()

# 페이지 파일 (static/index.html, static/chart.umd.js)
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index_page():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/keywords")
def keywords():
    """페이지의 키워드 탭에 쓸 목록"""
    return {"keywords": list(KEYWORD_SYNONYMS.keys())}


@app.get("/validate/{keyword}")
def validate(keyword: str):
    """거래일별 감성지수와 주가 등락률, 방향 일치율과 기준선"""
    keyword = keyword.strip().upper()
    if keyword not in validate_stock.TICKERS:
        return {"error": f"'{keyword}'는 주가 비교 대상이 아닙니다"}
    if not os.path.exists(CSV_PATH):
        return {"error": "아직 수집된 데이터가 없습니다"}
    try:
        news = validate_stock.load_news()
        return validate_stock.validate_keyword(news, keyword)
    except Exception as e:
        return {"error": f"주가 비교를 계산하지 못했습니다: {e}"}


@app.get("/articles/{keyword}")
def articles(keyword: str, limit: int = 20):
    """최근 기사 목록 (최신순)"""
    keyword = keyword.strip().upper()
    df = load_df()
    if df is None:
        return {"error": "아직 수집된 데이터가 없습니다"}

    df_filtered = filter_by_keyword(df, keyword)
    df_filtered = df_filtered.sort_values("collected_at", ascending=False).head(limit)

    items = []
    for row in df_filtered.to_dict("records"):
        items.append({
            "title": row["title"],
            "label": row["label"],
            "sentiment_index": None if pd.isna(row["sentiment_index"]) else round(row["sentiment_index"], 3),
            "collected_at": row["collected_at"],
            "keywords": row["keyword"].split("|"),
            "link": row["link"],
        })
    return {"keyword": keyword, "articles": items}

# 응답 숫자 설명
#   avg_sentiment_index : 기사별 (긍정 확률 - 부정 확률)의 평균. -1(매우 부정) ~ +1(매우 긍정)
#                         트렌드와 비교에는 이 값을 쓴다.
#   avg_confidence      : 모델이 고른 라벨을 얼마나 확신했는지의 평균 (0 ~ 1)
#                         감성의 방향이나 세기가 아니므로 분위기 지표로 쓰지 않는다.


def load_df():
    if not os.path.exists(CSV_PATH):
        return None
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def summarize(df_filtered):
    label_counts = df_filtered["label"].value_counts().to_dict()
    total = len(df_filtered)
    return {
        "total_articles": total,
        "label_counts": label_counts,
        "label_ratio": {k: round(v / total, 2) for k, v in label_counts.items()},
        "avg_sentiment_index": round(df_filtered["sentiment_index"].mean(), 3),
        "avg_confidence": round(df_filtered["score"].mean(), 3),
    }


@app.post("/collect")
def collect(keyword: str, count: int = 30, min_hits: int = 1, pages: int = 3):
    return run_collect(keyword, count=count, min_hits=min_hits, pages=pages)


@app.get("/sentiment/{keyword}")
def sentiment(keyword: str):
    keyword = keyword.strip().upper()

    df = load_df()
    if df is None:
        return {"error": "아직 수집된 데이터가 없습니다"}

    df_filtered = filter_by_keyword(df, keyword)
    if len(df_filtered) == 0:
        return {"error": f"'{keyword}'에 대한 데이터가 없습니다"}

    return {"keyword": keyword, **summarize(df_filtered)}


@app.get("/compare")
def compare(keywords: str):
    df = load_df()
    if df is None:
        return {"error": "아직 수집된 데이터가 없습니다"}

    keyword_list = [k.strip().upper() for k in keywords.split(",")]

    result = {}
    for keyword in keyword_list:
        df_filtered = filter_by_keyword(df, keyword)
        if len(df_filtered) == 0:
            result[keyword] = {"error": "데이터 없음"}
            continue
        result[keyword] = summarize(df_filtered)

    valid = [(k, v) for k, v in result.items() if "error" not in v]

    sentiment_ranking = sorted(valid, key=lambda kv: kv[1]["avg_sentiment_index"], reverse=True)
    positive_ranking = sorted(valid, key=lambda kv: kv[1]["label_ratio"].get("positive", 0), reverse=True)

    return {
        "compared_keywords": keyword_list,
        "details": result,
        "sentiment_ranking": [
            {"keyword": k, "avg_sentiment_index": v["avg_sentiment_index"]} for k, v in sentiment_ranking
        ],
        "positive_ranking": [
            {"keyword": k, "positive_ratio": v["label_ratio"].get("positive", 0)} for k, v in positive_ranking
        ],
    }


@app.get("/trend/{keyword}")
def trend(keyword: str, days: int = 7):
    keyword = keyword.strip().upper()

    df = load_df()
    if df is None:
        return {"error": "아직 수집된 데이터가 없습니다"}

    df_filtered = filter_by_keyword(df, keyword).copy()
    if len(df_filtered) == 0:
        return {"error": f"'{keyword}'에 대한 데이터가 없습니다"}

    df_filtered["date"] = pd.to_datetime(df_filtered["collected_at"]).dt.date

    cutoff = pd.Timestamp.now().date() - pd.Timedelta(days=days)
    df_filtered = df_filtered[df_filtered["date"] >= cutoff]

    if len(df_filtered) == 0:
        return {"error": f"최근 {days}일간 데이터가 없습니다"}

    daily_stats = df_filtered.groupby("date").agg(
        total_articles=("label", "count"),
        avg_sentiment_index=("sentiment_index", "mean"),
        avg_confidence=("score", "mean"),
    ).reset_index()

    daily_sentiment = df_filtered.groupby(["date", "label"]).size().unstack(fill_value=0)

    trend_list = []
    for _, row in daily_stats.iterrows():
        date = row["date"]
        sentiment_row = daily_sentiment.loc[date] if date in daily_sentiment.index else {}

        trend_list.append({
            "date": str(date),
            "total_articles": int(row["total_articles"]),
            "avg_sentiment_index": round(row["avg_sentiment_index"], 3),
            "avg_confidence": round(row["avg_confidence"], 3),
            "positive": int(sentiment_row.get("positive", 0)),
            "neutral": int(sentiment_row.get("neutral", 0)),
            "negative": int(sentiment_row.get("negative", 0)),
        })

    return {
        "keyword": keyword,
        "period_days": days,
        "trend": trend_list
    }

# uvicorn start:app --reload
