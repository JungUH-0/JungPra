from fastapi import FastAPI
import pandas as pd
import os

# 수집/필터/저장은 전부 collector.py에 있음
from collector import CSV_PATH, collect as run_collect

app = FastAPI()


@app.post("/collect")
def collect(keyword: str, count: int = 10, min_hits: int = 1):
    return run_collect(keyword, count=count, min_hits=min_hits)


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
