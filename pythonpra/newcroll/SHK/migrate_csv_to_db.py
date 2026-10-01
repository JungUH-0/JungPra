# migrate_csv_to_db.py
# ------------------------------------------------------------
# 지금까지 모은 CSV를 news.db(SQLite)로 옮긴다.
#
# 사용법 (SHK 폴더에서)
#   python migrate_csv_to_db.py                  -> news_sentiment.csv + request_log.csv 를 옮김
#   python migrate_csv_to_db.py 다른파일.csv      -> 그 CSV의 기사를 DB에 합침
#                                                  (다른 환경에서 모은 데이터 합칠 때)
#
# 여러 번 돌려도 안전하다.
#   - 이미 DB에 있는 기사(link 같음)는 다시 넣지 않고, 빠진 키워드만 연결한다.
#   - 요청 로그도 같은 줄(시간·키워드·페이지·start 같음)은 다시 넣지 않는다.
#
# CSV 파일은 지우거나 고치지 않는다. 옮긴 뒤에도 그대로 두면 백업이 된다.
# ------------------------------------------------------------
import os
import sys

import pandas as pd

import db
from collector import CSV_PATH, KEYWORD_SYNONYMS, load_existing, split_keywords

REQUEST_LOG_CSV = "request_log.csv"
SENTIMENT_COLUMNS = ["p_positive", "p_neutral", "p_negative", "sentiment_index"]


def _value(v):
    """pandas의 빈칸(NaN)은 DB에 NULL로 넣는다."""
    return None if pd.isna(v) else v


def migrate_articles(path):
    try:
        df = load_existing(path)
    except ValueError as e:
        print(f"[중단] {e}")
        return False

    if len(df) == 0:
        print(f"{path}: 기사가 없거나 파일이 없습니다. 건너뜀.")
        return True

    missing = df[SENTIMENT_COLUMNS].isna().any(axis=1).sum()
    if missing:
        print(f"[알림] 감성지수가 비어 있는 행 {missing}건이 있습니다. "
              f"repair_csv.py로 채운 뒤 옮기는 걸 권장합니다. (빈 값은 NULL로 들어갑니다)")

    all_keywords = sorted({kw for v in df["keyword"] for kw in split_keywords(v)},
                          key=lambda k: list(KEYWORD_SYNONYMS).index(k) if k in KEYWORD_SYNONYMS else 99)
    unknown = [k for k in all_keywords if k not in KEYWORD_SYNONYMS]
    if unknown:
        print(f"[알림] 사전에 없는 키워드도 같이 옮깁니다: {unknown}")

    added, tagged, skipped = 0, 0, 0
    with db.session() as conn:
        kw_ids = db.ensure_keywords(conn, all_keywords) if all_keywords else {}
        existing = db.find_articles(conn, df["link"].tolist())

        for _, r in df.iterrows():
            link = r["link"]
            keywords = split_keywords(r["keyword"])

            if link in existing:
                article_id = existing[link]["id"]
                new_links = sum(db.link_keyword(conn, article_id, kw_ids[kw]) for kw in keywords)
                if new_links:
                    tagged += 1
                else:
                    skipped += 1
                continue

            article_id = db.insert_article(conn, {
                "link": link,
                "title": r["title"],
                "label": r["label"],
                "score": float(r["score"]),
                "p_positive": _value(r["p_positive"]),
                "p_neutral": _value(r["p_neutral"]),
                "p_negative": _value(r["p_negative"]),
                "sentiment_index": _value(r["sentiment_index"]),
                "collected_at": str(r["collected_at"]),
            })
            for kw in keywords:
                db.link_keyword(conn, article_id, kw_ids[kw])
            added += 1

    print(f"{path}: {len(df)}행 읽음 -> 새로 저장 {added}, "
          f"기존 기사에 키워드 추가 {tagged}, 이미 있음 {skipped}")
    return True


def migrate_request_log(path=REQUEST_LOG_CSV):
    if not os.path.exists(path):
        print(f"{path}: 없음. 건너뜀.")
        return

    logs = pd.read_csv(path, encoding="utf-8-sig", dtype=str).fillna("")
    with db.session() as conn:
        seen = {tuple(row) for row in conn.execute(
            "SELECT time, keyword, page, start FROM request_logs").fetchall()}

    added = 0
    for _, r in logs.iterrows():
        page = int(r["page"]) if r["page"] else None
        start = int(r["start"]) if r["start"] else None
        if (r["time"], r["keyword"], page, start) in seen:
            continue
        db.log_request(
            time=r["time"], keyword=r["keyword"], page=page, source=r["source"], start=start,
            status=r["status"],
            titles=int(r["titles"]) if r["titles"] else None,
            new_titles=int(r["new_titles"]) if r["new_titles"] else None,
            elapsed_ms=int(float(r["elapsed_ms"])) if r["elapsed_ms"] else None,
            result=r["result"],
        )
        added += 1
    print(f"{path}: {len(logs)}줄 읽음 -> 새로 저장 {added}")


def main():
    paths = sys.argv[1:] or [CSV_PATH]
    print(f"DB 파일: {db.DB_PATH}")

    for path in paths:
        if not migrate_articles(path):
            sys.exit(1)

    # 인자 없이 돌렸을 때만 요청 로그도 옮김
    if not sys.argv[1:]:
        migrate_request_log()

    c = db.counts()
    print()
    print(f"DB 현황: 기사 {c['articles']}건 ({c['first']} ~ {c['last']})")
    for name, n in c["per_keyword"].items():
        print(f"  {name}: {n}건")


if __name__ == "__main__":
    main()
