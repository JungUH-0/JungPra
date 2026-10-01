# validate_stock.py
# ------------------------------------------------------------
# 뉴스 감성지수가 실제 주가 움직임과 맞았는지 비교하는 분석 스크립트.
#
#   1) news_sentiment.csv 읽기
#   2) FinanceDataReader로 일별 종가를 받아 등락률(%) 계산
#   3) 뉴스 수집 날짜를 거래일에 맞춤
#      - 주말·휴장일에 모은 뉴스는 다음 거래일로 붙임
#   4) 거래일별 평균 감성지수 vs
#      - 같은 날 등락률   (뉴스가 주가를 따라가는가)
#      - 다음 거래일 등락률 (뉴스가 주가를 앞서가는가)
#   5) 결과를 화면에 출력하고 validation_daily.csv, validation_chart.png로 저장
#
# 필요 패키지: pip install finance-datareader matplotlib pykrx
#   (pykrx는 코스피 지수를 한국거래소에서 직접 받는 데 씀. 없으면 다른 출처로 대신함)
# 실행: SHK 폴더에서  python validate_stock.py
# ------------------------------------------------------------
import os
from datetime import date, timedelta

import numpy as np
import pandas as pd

from collector import CSV_PATH, filter_by_keyword

# 키워드 -> FinanceDataReader 종목코드
TICKERS = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "코스피": "KS11",
}

# 기사 수가 이보다 적은 날은 "표본 적음"으로 표시 (감성 기준 문서의 표시 규칙과 같음)
MIN_ARTICLES = 5

DAILY_CSV = "validation_daily.csv"
CHART_PNG = "validation_chart.png"


# ------------------------------------------------------------
# 데이터 불러오기
# ------------------------------------------------------------
def load_news():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"{CSV_PATH}가 없습니다. SHK 폴더에서 실행하세요.")
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    if "sentiment_index" not in df.columns:
        raise ValueError("감성지수 열이 없습니다. repair_csv.py를 먼저 돌리세요.")
    df["collected_at"] = pd.to_datetime(df["collected_at"])
    return df


def _fdr_close(symbol, start, end):
    import FinanceDataReader as fdr
    prices = fdr.DataReader(symbol, start, end)
    close = prices["Close"].dropna()
    close.index = pd.to_datetime(close.index).date
    return close


def _pykrx_index_close(index_code, start, end):
    from pykrx import stock
    prices = stock.get_index_ohlcv(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), index_code)
    close = prices["종가"].dropna()
    close.index = pd.to_datetime(close.index).date
    return close


# 키워드별로 시도할 가격 출처 (위에서부터 차례로 시도하고, 가장 최근 날짜까지 있는 걸 씀)
# 코스피 지수는 FinanceDataReader의 KS11이 갱신이 늦을 때가 있어서 다른 출처도 같이 본다.
PRICE_SOURCES = {
    "005930": [("FinanceDataReader 005930", lambda s, e: _fdr_close("005930", s, e))],
    "000660": [("FinanceDataReader 000660", lambda s, e: _fdr_close("000660", s, e))],
    "KS11": [
        ("FinanceDataReader KS11", lambda s, e: _fdr_close("KS11", s, e)),
        ("pykrx 코스피(1001)", lambda s, e: _pykrx_index_close("1001", s, e)),
        ("FinanceDataReader 야후 ^KS11", lambda s, e: _fdr_close("YAHOO:^KS11", s, e)),
    ],
}


def fetch_close(code, start, end):
    """
    일별 종가를 날짜(date) 인덱스의 Series로 돌려준다.
    출처가 여러 개면 전부 시도해서 마지막 날짜가 가장 늦은 것을 고른다.
    """
    best, best_name, tried = None, None, []
    for name, loader in PRICE_SOURCES[code]:
        try:
            close = loader(start, end)
        except Exception as e:                      # 패키지가 없거나 접속 실패
            tried.append(f"{name}: 실패 ({type(e).__name__})")
            continue
        if close.empty:
            tried.append(f"{name}: 데이터 없음")
            continue
        tried.append(f"{name}: {min(close.index)} ~ {max(close.index)}")
        if best is None or max(close.index) > max(best.index):
            best, best_name = close, name

    if len(PRICE_SOURCES[code]) > 1:
        for line in tried:
            print(f"  [가격 출처] {line}")
    if best is None:
        raise RuntimeError(f"{code} 가격을 어느 출처에서도 받지 못했습니다.")
    if len(PRICE_SOURCES[code]) > 1:
        print(f"  [가격 출처] 사용: {best_name}")
    return best


# ------------------------------------------------------------
# 계산
# ------------------------------------------------------------
def session_of(ts):
    """수집 시각이 장 시작 전 / 장중 / 장 마감 후 중 언제인지."""
    minutes = ts.hour * 60 + ts.minute
    if minutes < 9 * 60:
        return "장전"
    if minutes < 15 * 60 + 30:
        return "장중"
    return "장후"


def build_daily(news_kw, close):
    """
    키워드 하나의 기사들을 거래일별로 묶고 등락률을 붙인다.
    반환 열: trade_date, n_articles, avg_index, positive, neutral, negative,
            sessions, news_dates, ret_same, ret_next, few_articles
    """
    trade_days = sorted(close.index)
    ret = close.pct_change() * 100          # 전 거래일 종가 대비 등락률(%)

    news = news_kw.copy()
    news["news_date"] = news["collected_at"].dt.date
    news["session"] = news["collected_at"].apply(session_of)

    # 뉴스 날짜 -> 그날 또는 그 다음 첫 거래일
    positions = np.searchsorted(trade_days, news["news_date"].values, side="left")
    news["trade_date"] = [trade_days[p] if p < len(trade_days) else None for p in positions]

    # 가격 데이터가 뉴스보다 먼저 끝나면, 그 뒤 뉴스는 붙일 거래일이 없어서 빠진다.
    # 조용히 빠지지 않게 몇 건이 왜 빠졌는지 알려준다.
    dropped = news[news["trade_date"].isna()]
    if len(dropped):
        print(f"  [주의] 가격 데이터가 {trade_days[-1]}까지만 있어서, 그 뒤 뉴스 {len(dropped)}건"
              f"({min(dropped['news_date'])} ~ {max(dropped['news_date'])})은 비교에서 빠졌습니다."
              f" 그 뉴스를 붙일 다음 거래일이 아직 안 왔거나(주말·휴장), 가격 출처 갱신이 늦은 경우입니다.")
    news = news[news["trade_date"].notna()]

    rows = []
    for trade_date, group in news.groupby("trade_date"):
        i = trade_days.index(trade_date)
        next_day = trade_days[i + 1] if i + 1 < len(trade_days) else None
        rows.append({
            "trade_date": trade_date,
            "n_articles": len(group),
            "avg_index": group["sentiment_index"].mean(),
            "positive": int((group["label"] == "positive").sum()),
            "neutral": int((group["label"] == "neutral").sum()),
            "negative": int((group["label"] == "negative").sum()),
            "sessions": "/".join(sorted(group["session"].unique())),
            "news_dates": ",".join(sorted({d.strftime("%m-%d") for d in group["news_date"]})),
            "ret_same": ret.get(trade_date, np.nan),
            "ret_next": ret.get(next_day, np.nan) if next_day else np.nan,
        })

    daily = pd.DataFrame(rows)
    if len(daily):
        daily["few_articles"] = daily["n_articles"] < MIN_ARTICLES
    return daily


def hit_rate(index_values, returns):
    """
    감성 방향과 등락 방향이 같은 날의 비율.
    등락률이 정확히 0인 날은 방향이 없으니 제외한다.
    반환: (맞은 날 수, 비교한 날 수)
    """
    mask = returns.notna() & (returns != 0)
    s_idx = np.sign(index_values[mask])
    s_ret = np.sign(returns[mask])
    return int((s_idx == s_ret).sum()), int(mask.sum())


def evaluate(daily):
    """
    같은 날 / 다음 거래일 각각에 대해
      - 방향 일치율 (감성지수 부호 그대로)
      - 방향 일치율 (그 키워드 평균보다 긍정적이었나 기준)
      - 기준선: 기간 중 더 자주 나온 방향(상승 또는 하락)만 매일 찍었을 때 맞는 비율
      - 상관계수 (피어슨, 스피어만)
    """
    result = {}
    mean_index = daily["avg_index"].mean()

    for name, col in [("같은 날", "ret_same"), ("다음 거래일", "ret_next")]:
        part = daily[daily[col].notna()]
        returns = part[col]
        hit, n = hit_rate(part["avg_index"], returns)
        hit_rel, _ = hit_rate(part["avg_index"] - mean_index, returns)
        up_days = int((returns > 0).sum())
        down_days = int((returns < 0).sum())
        nonzero = up_days + down_days
        baseline = max(up_days, down_days)
        baseline_dir = "상승" if up_days >= down_days else "하락"

        pearson = spearman = np.nan
        if len(part) >= 3 and returns.std() > 0 and part["avg_index"].std() > 0:
            pearson = part["avg_index"].corr(returns)
            spearman = part["avg_index"].rank().corr(returns.rank())

        result[name] = {
            "days": n,
            "hit": hit,
            "hit_relative": hit_rel,
            "baseline": baseline,
            "baseline_dir": baseline_dir,
            "baseline_n": nonzero,
            "pearson": pearson,
            "spearman": spearman,
        }
    return result


# ------------------------------------------------------------
# 출력
# ------------------------------------------------------------
def pct(a, b):
    return f"{a}/{b} ({a / b:.0%})" if b else "-"


def print_report(keyword, daily, ev):
    if daily.empty:
        print("  비교할 거래일이 없습니다.")
        return

    view = daily.copy()
    view["trade_date"] = view["trade_date"].apply(lambda d: d.strftime("%m-%d"))
    view["avg_index"] = view["avg_index"].map(lambda v: f"{v:+.3f}")
    view["ret_same"] = view["ret_same"].map(lambda v: "" if pd.isna(v) else f"{v:+.2f}%")
    view["ret_next"] = view["ret_next"].map(lambda v: "" if pd.isna(v) else f"{v:+.2f}%")
    view["표본"] = view["few_articles"].map(lambda f: "적음" if f else "")
    view = view[["trade_date", "news_dates", "sessions", "n_articles", "avg_index",
                 "ret_same", "ret_next", "표본"]]
    view.columns = ["거래일", "뉴스날짜", "수집시각", "기사수", "감성지수", "당일등락", "다음날등락", "표본"]
    print(view.to_string(index=False))

    for name, r in ev.items():
        if r["days"] == 0:
            print(f"  [{name}] 비교 가능한 날 없음")
            continue
        corr = "" if pd.isna(r["pearson"]) else f", 상관 {r['pearson']:+.2f} (순위 {r['spearman']:+.2f})"
        print(f"  [{name}] 방향 일치 {pct(r['hit'], r['days'])}"
              f" | 평균 대비 기준 {pct(r['hit_relative'], r['days'])}"
              f" | 기준선(매일 {r['baseline_dir']}) {pct(r['baseline'], r['baseline_n'])}{corr}")


def draw_chart(results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    # 한글 폰트 (윈도우: 맑은 고딕, 없으면 설치된 다른 한글 폰트)
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in ["Malgun Gothic", "AppleGothic", "NanumGothic",
                 "Noto Sans CJK KR", "Noto Sans KR", "Noto Sans CJK JP"]:
        if name in installed:
            plt.rcParams["font.family"] = name
            break
    else:
        print("  (한글 폰트를 못 찾아서 그래프의 한글이 네모로 보일 수 있습니다)")
    plt.rcParams["axes.unicode_minus"] = False

    INK, MUTED, GRID = "#1b2120", "#5a6562", "#dde2df"
    LINE = "#0e5f5b"             # 감성지수
    UP, DOWN = "#c8323b", "#2657b3"   # 국내 관례: 상승 빨강, 하락 파랑

    keywords = [k for k in results if not results[k].empty]
    if not keywords:
        return None

    fig, axes = plt.subplots(2, len(keywords), figsize=(5.2 * len(keywords), 6.4),
                             sharex="col", gridspec_kw={"height_ratios": [1, 1]},
                             squeeze=False)

    for col, kw in enumerate(keywords):
        daily = results[kw]
        x = np.arange(len(daily))
        labels = [d.strftime("%m-%d") for d in daily["trade_date"]]
        ax_i, ax_r = axes[0, col], axes[1, col]

        # 위: 감성지수 (-1 ~ +1 고정, 0 기준선)
        ax_i.axhline(0, color=MUTED, linewidth=1)
        ax_i.plot(x, daily["avg_index"], color=LINE, linewidth=2, zorder=2)
        few = daily["few_articles"].values
        ax_i.scatter(x[~few], daily["avg_index"][~few], s=64, color=LINE, zorder=3,
                     edgecolors="white", linewidths=2)
        ax_i.scatter(x[few], daily["avg_index"][few], s=64, facecolors="white",
                     edgecolors=LINE, linewidths=2, zorder=3)
        ax_i.set_ylim(-1.08, 1.08)          # -1, +1에 딱 붙은 점도 잘리지 않게 여백
        ax_i.set_yticks([-1, -0.5, 0, 0.5, 1])
        ax_i.set_title(kw, color=INK, fontsize=13, loc="left", fontweight="bold")
        ax_i.set_ylabel("감성지수", color=MUTED)

        # 아래: 당일 등락률 막대
        rets = daily["ret_same"]
        colors = [UP if (not pd.isna(r) and r >= 0) else DOWN for r in rets]
        ax_r.axhline(0, color=MUTED, linewidth=1)
        ax_r.bar(x, rets.fillna(0), color=colors, width=0.6, edgecolor="white", linewidth=2)
        ax_r.set_ylabel("당일 등락률 (%)", color=MUTED)
        lim = max(1.0, np.nanmax(np.abs(rets.values)) * 1.25) if rets.notna().any() else 1.0
        ax_r.set_ylim(-lim, lim)
        ax_r.set_xticks(x)
        ax_r.set_xticklabels(labels, rotation=45, ha="right")

        for ax in (ax_i, ax_r):
            ax.grid(axis="y", color=GRID, linewidth=0.8)
            ax.set_axisbelow(True)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            for side in ("left", "bottom"):
                ax.spines[side].set_color(GRID)
            ax.tick_params(colors=MUTED)

    fig.suptitle("뉴스 감성지수와 당일 주가 등락률", color=INK, fontsize=15, x=0.01, ha="left")
    fig.text(0.01, 0.005, f"속 빈 점: 기사 {MIN_ARTICLES}건 미만인 날 (참고용)   ·   막대: 빨강 상승, 파랑 하락",
             color=MUTED, fontsize=9)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))

    # 윈도우에서 이전 그래프를 사진 뷰어 등으로 열어두면 파일이 잠겨서 덮어쓰기가 실패한다.
    # 그럴 땐 이름에 시각을 붙여서 따로 저장한다.
    path = CHART_PNG
    try:
        fig.savefig(path, dpi=150)
    except OSError:
        from datetime import datetime
        path = f"validation_chart_{datetime.now().strftime('%H%M%S')}.png"
        fig.savefig(path, dpi=150)
        print(f"  ({CHART_PNG}가 다른 프로그램에 열려 있어서 {path}로 저장했습니다)")
    plt.close(fig)
    return path


# ------------------------------------------------------------
def main():
    news = load_news()

    first_day = news["collected_at"].min().date()
    start = first_day - timedelta(days=10)   # 첫 거래일의 전일 종가가 필요해서 여유 있게
    end = date.today()

    print(f"뉴스 기간: {first_day} ~ {news['collected_at'].max().date()} ({len(news)}건)")
    print(f"주가 기간: {start} ~ {end}")

    results, all_daily = {}, []
    for keyword, code in TICKERS.items():
        print(f"\n===== {keyword} ({code}) =====")
        close = fetch_close(code, start, end)
        daily = build_daily(filter_by_keyword(news, keyword), close)
        results[keyword] = daily
        ev = evaluate(daily) if len(daily) else {}
        print_report(keyword, daily, ev)
        if len(daily):
            all_daily.append(daily.assign(keyword=keyword, code=code))

    if all_daily:
        out = pd.concat(all_daily, ignore_index=True)
        cols = ["keyword", "code"] + [c for c in out.columns if c not in ("keyword", "code")]
        out[cols].to_csv(DAILY_CSV, index=False, encoding="utf-8-sig")
        print(f"\n날짜별 비교표: {DAILY_CSV}")

    chart = draw_chart(results)
    if chart:
        print(f"그래프: {chart}")

    print("\n읽는 법")
    print("  방향 일치: 감성지수가 +면 상승, -면 하락으로 보고 맞은 날의 비율")
    print("  평균 대비 기준: 그 키워드 평소 감성보다 높았으면 상승으로 본 비율")
    print("                  (중립 기사가 많아 감성지수가 대부분 +로 나오는 치우침을 줄인 값)")
    print("  기준선: 뉴스를 안 보고 기간 중 더 자주 나온 방향(상승/하락)만 매일 찍었을 때 맞는 비율")
    print("          방향 일치가 이보다 높아야 감성이 뭔가 알려준다고 볼 수 있음")
    print("  거래일이 10일 안팎이라 우연의 영향이 큽니다. 경향을 보는 용도로만 해석하세요.")


if __name__ == "__main__":
    main()