# db.py
# ------------------------------------------------------------
# SQLite DB 연결, 테이블 생성, 저장·조회 함수.
# 수집(collector.py), 조회 API(start.py), 주가 비교(validate_stock.py)가 전부 이 파일을 통해 DB를 쓴다.
#
# 테이블
#   articles          기사 한 건 = 한 행. link는 UNIQUE라서 같은 기사가 두 번 들어가지 않음
#   keywords          삼성전자, SK하이닉스, 코스피
#   article_keywords  기사와 키워드 연결 (한 기사가 여러 키워드에 걸릴 수 있음)
#   request_logs      네이버에 보낸 요청 하나하나의 기록 (차단 확인용)
#
# DB 파일은 이 파일과 같은 폴더의 news.db.
# 어느 폴더에서 실행해도 같은 DB를 쓰도록 경로를 이 파일 기준으로 잡는다.
# ------------------------------------------------------------
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent / "news.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    link            TEXT    NOT NULL UNIQUE,
    title           TEXT    NOT NULL,
    label           TEXT    NOT NULL,       -- positive / neutral / negative
    score           REAL    NOT NULL,       -- label의 확률 (확신도. 감성 세기 아님)
    p_positive      REAL,
    p_neutral       REAL,
    p_negative      REAL,
    sentiment_index REAL,                   -- p_positive - p_negative, -1 ~ +1
    collected_at    TEXT    NOT NULL        -- 'YYYY-MM-DD HH:MM:SS'
);

CREATE TABLE IF NOT EXISTS keywords (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS article_keywords (
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    keyword_id INTEGER NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, keyword_id)
);

CREATE TABLE IF NOT EXISTS request_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    time        TEXT NOT NULL,
    keyword     TEXT,
    page        INTEGER,
    source      TEXT,       -- search(1페이지) / more(스크롤 요청)
    start       INTEGER,
    status      TEXT,       -- 상태코드, 네트워크 오류면 ERR
    titles      INTEGER,
    new_titles  INTEGER,
    elapsed_ms  INTEGER,
    result      TEXT
);

CREATE INDEX IF NOT EXISTS idx_articles_collected_at ON articles(collected_at);
CREATE INDEX IF NOT EXISTS idx_article_keywords_keyword ON article_keywords(keyword_id);
"""

# CSV로 내보내거나, 예전 CSV 형식으로 DataFrame을 돌려줄 때의 열 순서 (link는 마지막)
ARTICLE_COLUMNS = [
    "keyword", "title",
    "label", "score",
    "p_positive", "p_neutral", "p_negative", "sentiment_index",
    "collected_at", "link",
]


def connect():
    """
    DB에 연결한다. 테이블이 없으면 만든다.
    WAL 모드: 수집이 쓰는 중에도 서버가 읽을 수 있게 함.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def session():
    """
    with session() as conn: ... 형태로 쓰면
    끝날 때 커밋하고(오류면 취소) 연결을 닫는다.
    (sqlite3의 기본 with는 커밋만 하고 연결을 닫지 않아서 따로 만듦)
    """
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def has_data():
    """기사가 한 건이라도 있는지"""
    if not DB_PATH.exists():
        return False
    with session() as conn:
        return conn.execute("SELECT EXISTS(SELECT 1 FROM articles)").fetchone()[0] == 1


# ------------------------------------------------------------
# 저장
# ------------------------------------------------------------
def ensure_keywords(conn, names):
    """키워드가 없으면 만들고, {이름: id}를 돌려준다."""
    for name in names:
        conn.execute("INSERT OR IGNORE INTO keywords(name) VALUES (?)", (name,))
    placeholders = ",".join("?" * len(names))
    rows = conn.execute(f"SELECT id, name FROM keywords WHERE name IN ({placeholders})", list(names))
    return {row["name"]: row["id"] for row in rows}


def find_articles(conn, links):
    """
    이미 저장된 기사를 찾는다.
    반환: {link: {"id": 기사 id, "keywords": {붙어 있는 키워드 이름들}}}
    """
    found = {}
    links = list(links)
    # SQLite는 한 번에 넣을 수 있는 ? 개수에 제한이 있어서 나눠서 조회
    for i in range(0, len(links), 500):
        chunk = links[i:i + 500]
        placeholders = ",".join("?" * len(chunk))
        rows = conn.execute(f"""
            SELECT a.id, a.link, k.name
            FROM articles a
            LEFT JOIN article_keywords ak ON ak.article_id = a.id
            LEFT JOIN keywords k ON k.id = ak.keyword_id
            WHERE a.link IN ({placeholders})
        """, chunk)
        for row in rows:
            item = found.setdefault(row["link"], {"id": row["id"], "keywords": set()})
            if row["name"]:
                item["keywords"].add(row["name"])
    return found


def insert_article(conn, row):
    """기사 한 건을 넣고 id를 돌려준다. 이미 있는 link면 기존 id를 돌려준다."""
    conn.execute("""
        INSERT OR IGNORE INTO articles
            (link, title, label, score, p_positive, p_neutral, p_negative, sentiment_index, collected_at)
        VALUES (:link, :title, :label, :score, :p_positive, :p_neutral, :p_negative, :sentiment_index, :collected_at)
    """, row)
    return conn.execute("SELECT id FROM articles WHERE link = ?", (row["link"],)).fetchone()["id"]


def link_keyword(conn, article_id, keyword_id):
    """기사에 키워드를 붙인다. 이미 붙어 있으면 아무 일도 안 함."""
    cur = conn.execute("INSERT OR IGNORE INTO article_keywords(article_id, keyword_id) VALUES (?, ?)",
                       (article_id, keyword_id))
    return cur.rowcount == 1


def log_request(**row):
    """요청 한 건을 request_logs에 남긴다."""
    with session() as conn:
        conn.execute("""
            INSERT INTO request_logs (time, keyword, page, source, start, status, titles, new_titles, elapsed_ms, result)
            VALUES (:time, :keyword, :page, :source, :start, :status, :titles, :new_titles, :elapsed_ms, :result)
        """, {k: row.get(k) for k in
              ["time", "keyword", "page", "source", "start", "status", "titles", "new_titles", "elapsed_ms", "result"]})


# ------------------------------------------------------------
# 조회
# ------------------------------------------------------------
def articles_df(keyword=None, order_by_latest=False, limit=None):
    """
    기사를 예전 CSV와 같은 열 구성의 DataFrame으로 돌려준다.
    keyword를 주면 그 키워드가 붙은 기사만.
    keyword 열에는 그 기사에 붙은 키워드 전부가 "삼성전자|SK하이닉스"처럼 들어간다.
    """
    from collector import join_keywords   # 키워드 표시 순서를 collector와 맞춤

    where, params = "", []
    if keyword:
        where = """WHERE a.id IN (
                       SELECT ak2.article_id FROM article_keywords ak2
                       JOIN keywords k2 ON k2.id = ak2.keyword_id
                       WHERE k2.name = ?)"""
        params.append(keyword)

    order = "ORDER BY a.collected_at DESC, a.id DESC" if order_by_latest else "ORDER BY a.id"
    limit_sql = f"LIMIT {int(limit)}" if limit else ""

    sql = f"""
        SELECT a.id, a.title, a.label, a.score, a.p_positive, a.p_neutral, a.p_negative,
               a.sentiment_index, a.collected_at, a.link,
               GROUP_CONCAT(k.name, '|') AS keyword
        FROM articles a
        LEFT JOIN article_keywords ak ON ak.article_id = a.id
        LEFT JOIN keywords k ON k.id = ak.keyword_id
        {where}
        GROUP BY a.id
        {order}
        {limit_sql}
    """
    with session() as conn:
        df = pd.read_sql_query(sql, conn, params=params)

    df["keyword"] = df["keyword"].fillna("").apply(lambda v: join_keywords(v.split("|")) if v else "")
    return df[ARTICLE_COLUMNS]


def request_logs_df():
    with session() as conn:
        return pd.read_sql_query("SELECT * FROM request_logs ORDER BY id", conn)


def counts():
    """간단한 현황: 기사 수, 키워드별 기사 수, 기간"""
    with session() as conn:
        total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        period = conn.execute("SELECT MIN(collected_at), MAX(collected_at) FROM articles").fetchone()
        per_kw = conn.execute("""
            SELECT k.name, COUNT(*) AS n FROM article_keywords ak
            JOIN keywords k ON k.id = ak.keyword_id GROUP BY k.name ORDER BY k.id
        """).fetchall()
    return {"articles": total, "first": period[0], "last": period[1],
            "per_keyword": {row["name"]: row["n"] for row in per_kw}}
