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
import csv
import os
import random
import time
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

CSV_PATH = "news_sentiment.csv"

# CSV 열 순서는 여기 한 곳에서만 정한다. (link는 항상 마지막)
#   label, score        : 모델이 고른 라벨과 그 확신도 (score는 감성 세기가 아님)
#   p_positive/neutral/negative : 세 라벨 각각의 확률 (합 1)
#   sentiment_index     : p_positive - p_negative, -1(매우 부정) ~ +1(매우 긍정)
COLUMNS = [
    "keyword", "title",
    "label", "score",
    "p_positive", "p_neutral", "p_negative", "sentiment_index",
    "collected_at", "link",
]

# 감성지수가 들어가기 전의 열 구성 (repair_csv.py가 옛 파일을 알아보는 데 씀)
OLD_COLUMNS = ["keyword", "title", "label", "score", "collected_at", "link"]

# keyword 칸 안에서 여러 키워드를 이을 때 쓰는 구분자
# 쉼표를 쓰면 CSV 칸이 나뉘어 버리므로 | 를 쓴다.
KEYWORD_SEP = "|"

# ------------------------------------------------------------
# 키워드별 동의어/관련어 사전
# 여기 적힌 순서가 keyword 칸에 이어 적을 때의 순서가 된다.
# ------------------------------------------------------------
KEYWORD_SYNONYMS = {
    # 삼전: 증권 기사에서 흔히 쓰는 줄임말 / 삼전닉스: 삼성전자+SK하이닉스를 묶어 부르는 말
    "삼성전자": ["삼성전자", "삼성 전자", "삼성전자우", "삼전", "삼전닉스"],
    # 하닉: SK하이닉스 줄임말 ("SK하닉", "삼전·하닉")
    # "닉스" 단독은 "피닉스" 같은 단어까지 걸려서 넣지 않고, "삼전·닉스"처럼 붙어 나올 때만 인정
    "SK하이닉스": ["SK하이닉스", "하이닉스", "하닉", "삼전닉스", "삼전·닉스"],
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


def analyze_title(title):
    """
    제목 하나를 감성 분석해서 라벨, 확신도, 세 라벨 확률, 감성지수를 돌려준다.

    top_k=None을 주면 모델이 1등 라벨만이 아니라 세 라벨의 확률을 모두 준다.
    transformers 버전에 따라 [{...}, {...}, {...}] 또는 [[{...}, ...]]로 나오므로 둘 다 처리한다.
    """
    output = get_classifier()(title, top_k=None, truncation=True)
    if output and isinstance(output[0], list):
        output = output[0]

    probs = {item["label"].lower(): float(item["score"]) for item in output}

    missing = {"positive", "neutral", "negative"} - probs.keys()
    if missing:
        raise ValueError(f"모델이 예상과 다른 라벨을 돌려줬습니다: {list(probs.keys())}")

    label = max(probs, key=probs.get)

    return {
        "label": label,
        "score": probs[label],
        "p_positive": probs["positive"],
        "p_neutral": probs["neutral"],
        "p_negative": probs["negative"],
        "sentiment_index": probs["positive"] - probs["negative"],
    }


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


SEARCH_URL = "https://search.naver.com/search.naver"
# 검색 화면에서 스크롤을 내릴 때 브라우저가 다음 기사를 받아오는 요청.
# 일반 검색 주소는 start 값을 무시해서 늘 1페이지만 주지만, 이 요청은 start에 맞는 기사를 준다.
# 응답은 JSON이고 collection[0].html 안에 기사 목록 HTML이 들어 있다.
MORE_URL = "https://s.search.naver.com/p/newssearch/3/api/tab/more"
SEARCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://search.naver.com/",
}
TITLE_SELECTOR = "span.sds-comps-text-type-headline1"
PAGE_SIZE = 10          # 한 번에 받는 기사 수

# 요청 사이 대기 (초). 최소 3초에서 4.5초 사이로 매번 조금씩 다르게 쉰다.
# 일정한 간격으로 기계적으로 요청하는 모습이 덜 드러나게 하기 위함.
DELAY_MIN = 3.0
DELAY_MAX = 4.5

# 요청 하나하나를 남기는 로그. 언제부터 막혔는지 확인하는 용도.
REQUEST_LOG = "request_log.csv"
REQUEST_LOG_COLUMNS = ["time", "keyword", "page", "source", "start",
                       "status", "titles", "new_titles", "elapsed_ms", "result"]

# 차단됐을 때 오는 상태코드
BLOCK_STATUS = {403, 429}
# 차단·자동입력 방지 화면에서 볼 수 있는 문구
BLOCK_WORDS = ["captcha", "자동입력", "비정상적인 접근", "비정상적인 트래픽"]


def wait():
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))


def log_request(**row):
    """요청 한 건을 request_log.csv에 한 줄 추가한다."""
    is_new = not os.path.exists(REQUEST_LOG)
    with open(REQUEST_LOG, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REQUEST_LOG_COLUMNS)
        if is_new:
            writer.writeheader()
        writer.writerow({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), **row})


def _request_page(keyword, page):
    """
    검색 결과 한 페이지를 요청한다.
      1페이지: 일반 검색 화면 (HTML)
      2페이지부터: 스크롤 요청 (JSON, collection[0].html 안에 기사 목록)
    반환: (기사 목록 HTML, 로그용 정보 dict)
    네트워크 오류는 그대로 예외로 올린다.
    """
    if page == 0:
        source, start = "search", 1
        params = {"where": "news", "query": keyword, "sort": "1"}
        url = SEARCH_URL
    else:
        source, start = "more", page * PAGE_SIZE + 1      # 11, 21, 31 ...
        params = {
            "ssc": "tab.news.all",
            "query": keyword,
            "sort": "1",                                   # 최신순
            "start": start,
            "nso": "so:dd,p:all,a:all",
        }
        url = MORE_URL

    began = time.perf_counter()
    res = requests.get(url, params=params, headers=SEARCH_HEADERS, timeout=10)
    info = {"source": source, "start": start, "status": res.status_code,
            "elapsed_ms": int((time.perf_counter() - began) * 1000)}

    if page == 0:
        html = res.text
    else:
        try:
            data = res.json()
            html = "".join(item.get("html", "") for item in data.get("collection", [])
                           if isinstance(item, dict))
        except ValueError:
            html = ""
            info["not_json"] = True
            info["raw"] = res.text

    info.setdefault("raw", res.text if page == 0 else "")
    return html, info


def _looks_blocked(info, titles_found, page):
    """
    차단 의심이면 이유 문자열, 아니면 None.
      - 상태코드 403/429
      - 제목을 하나도 못 받았는데 응답에 자동입력 방지 문구가 있음
      - 1페이지가 200인데 제목이 0개 (차단 화면이거나 네이버 화면 구조가 바뀐 경우)

    제목을 정상으로 받았으면 차단이 아니다.
    (정상 검색 페이지도 스크립트 안에 captcha 같은 단어가 들어 있어서,
     응답 전체에서 문구만 찾으면 정상 페이지를 차단으로 오인한다)

    2페이지 이후에서 JSON이 아니거나 제목이 0개인 건 차단이 아니라 '더 없음'으로 보고 그 키워드만 멈춘다.
    """
    if info["status"] in BLOCK_STATUS:
        return f"상태코드 {info['status']}"
    if titles_found > 0:
        return None
    lowered = info.get("raw", "").lower()
    if any(word.lower() in lowered for word in BLOCK_WORDS):
        return "자동입력 방지 화면"
    if page == 0 and info["status"] == 200:
        return "1페이지 제목 0개 (차단 화면 또는 화면 구조 변경)"
    return None


def search_candidates(keyword, pages=1):
    """
    검색 결과를 1페이지부터 pages페이지까지 받아서 (제목, 링크) 후보를 모은다.
    요청마다 request_log.csv에 한 줄씩 남긴다.

    - 어떤 페이지에서 새 기사가 하나도 안 나오면 그 키워드는 거기서 멈춘다.
    - 차단이 의심되면 바로 멈추고 이유를 돌려준다. (호출한 쪽에서 남은 키워드도 멈춤)
      그때까지 모은 후보는 버리지 않는다.
    - 요청하는 사이에 새 기사가 올라와 목록이 밀려도, 링크 기준으로 한 번만 담는다.

    반환: (후보 목록, 실제로 쓴 페이지 수, 차단 의심 이유 또는 None)
    """
    candidates = []
    seen_links = set()
    pages_used = 0

    for page in range(pages):
        if page > 0:
            wait()

        try:
            html, info = _request_page(keyword, page)
        except requests.RequestException as e:
            log_request(keyword=keyword, page=page + 1, source="search" if page == 0 else "more",
                        start=page * PAGE_SIZE + 1, status="ERR", titles=0, new_titles=0,
                        elapsed_ms="", result=f"네트워크 오류 {type(e).__name__}")
            return candidates, pages_used, f"네트워크 오류 ({type(e).__name__})"

        soup = BeautifulSoup(html, "html.parser")
        titles = soup.select(TITLE_SELECTOR)

        new_in_page = 0
        for span in titles:
            parent_a = span.find_parent("a")
            if not parent_a:
                continue
            link = parent_a.get("href")
            if not link or link in seen_links:
                continue
            seen_links.add(link)
            candidates.append((span.get_text(strip=True), link))
            new_in_page += 1

        blocked = _looks_blocked(info, len(titles), page)
        if blocked:
            result = f"차단 의심: {blocked}"
        elif info.get("not_json"):
            result = "JSON 아님 -> 이 키워드 멈춤"
        elif new_in_page == 0:
            result = "새 기사 없음 -> 이 키워드 멈춤"
        else:
            result = "정상"

        log_request(keyword=keyword, page=page + 1, source=info["source"], start=info["start"],
                    status=info["status"], titles=len(titles), new_titles=new_in_page,
                    elapsed_ms=info["elapsed_ms"], result=result)

        if new_in_page:
            pages_used += 1
        if blocked:
            return candidates, pages_used, blocked
        if new_in_page == 0:
            break

    return candidates, pages_used, None


def get_naver_news(keyword, count=30, min_hits=1, pages=3):
    """
    검색 후보를 모은 뒤 제목 필터를 통과한 기사만 최대 count개 돌려준다.
    반환: {"articles": [...], "candidates": 후보 수, "pages": 쓴 페이지 수, "blocked": 이유 또는 None}
    """
    candidates, pages_used, blocked = search_candidates(keyword, pages=pages)

    articles = []
    seen_titles = set()
    for title, link in candidates:
        if len(articles) >= count:
            break

        if not is_title_relevant(title, keyword, min_hits=min_hits):
            continue

        # 같은 실행 안에서 제목이 똑같은 기사는 하나만 남김 (사진기사 등)
        if title in seen_titles:
            continue
        seen_titles.add(title)

        articles.append({"title": title, "link": link})

    return {"articles": articles, "candidates": len(candidates), "pages": pages_used, "blocked": blocked}


# ------------------------------------------------------------
# 저장
# ------------------------------------------------------------
def load_existing():
    """기존 CSV를 읽고 형식이 맞는지 확인한다. 없으면 빈 DataFrame."""
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame(columns=COLUMNS)

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    if list(df.columns) == OLD_COLUMNS:
        raise ValueError(
            f"{CSV_PATH}에 감성지수 열이 아직 없습니다. "
            f"repair_csv.py를 한 번 돌려서 기존 기사의 감성지수를 채우세요."
        )

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


def collect_many(keywords, count=30, min_hits=1, pages=3):
    """
    여러 키워드를 한 번에 수집해서 합친 뒤 저장한다.

    1) 키워드마다 검색(최대 pages페이지) -> 제목 필터
    2) link 기준으로 합치기 (한 기사에 걸린 키워드를 모음)
    3) 이미 저장된 기사: 빠진 키워드만 기존 행에 추가
       새 기사: 감성분석 한 번 돌리고 새 행으로 추가
    4) 저장

    반환값: 키워드별 결과 목록
      candidates: 검색 결과에서 모은 후보 기사 수 (필터 전)
      pages     : 실제로 받은 검색 페이지 수
      found     : 제목 필터를 통과한 기사 수
      new       : 새로 저장된 기사 수 (다른 키워드와 같이 걸린 것 포함)
      tagged    : 이미 있던 기사에 이 키워드를 새로 붙인 수
      duplicate : 이미 이 키워드로 저장돼 있던 기사 수
      status    : "정상" / "차단 의심: 이유" / "건너뜀 (앞에서 차단 의심)"

    차단이 의심되면 남은 키워드는 요청하지 않는다.
    그때까지 모은 기사는 정상적으로 저장한다.
    """
    keywords = [k.strip().upper() for k in keywords]

    # 1) 검색
    found = {}                      # keyword -> [article, ...]
    search_info = {}                # keyword -> {"candidates", "pages", "status"}
    blocked_reason = None
    for i, kw in enumerate(keywords):
        if blocked_reason:
            found[kw] = []
            search_info[kw] = {"candidates": 0, "pages": 0, "status": "건너뜀 (앞에서 차단 의심)"}
            continue
        if i > 0:
            wait()
        result = get_naver_news(kw, count=count, min_hits=min_hits, pages=pages)
        found[kw] = result["articles"]
        status = "정상"
        if result["blocked"]:
            blocked_reason = result["blocked"]
            status = f"차단 의심: {blocked_reason}"
        search_info[kw] = {"candidates": result["candidates"], "pages": result["pages"], "status": status}

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

    stats = {kw: {"keyword": kw, **search_info[kw], "found": len(found[kw]),
                  "new": 0, "tagged": 0, "duplicate": 0}
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
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for link, item in new_items:
            new_rows.append({
                "keyword": join_keywords(item["keywords"]),
                "title": item["title"],
                **analyze_title(item["title"]),
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


def collect(keyword, count=30, min_hits=1, pages=3):
    """키워드 하나만 수집. start.py의 /collect가 쓴다."""
    return collect_many([keyword], count=count, min_hits=min_hits, pages=pages)[0]


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
    candidates = get_naver_news(keyword, count=count * 2, min_hits=title_min_hits)["articles"]

    articles = []
    for article in candidates:
        if len(articles) >= count:
            break
        if is_body_relevant(article["link"], keyword, min_hits=body_min_hits):
            articles.append(article)

    return articles
"""
