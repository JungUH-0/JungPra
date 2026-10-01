# check_more_api.py
# ------------------------------------------------------------
# 네이버 뉴스 검색에서 스크롤할 때 부르는 요청(api/tab/more)이
#   1) requests로 받아지는지
#   2) 응답이 어떤 형식인지 (JSON 안에 HTML이 들어 있는지)
#   3) start 값에 따라 다른 기사가 오는지
#   4) ds/de 날짜 범위가 먹히는지
# 확인한다. 요청은 5번만 보낸다. 한 번만 실행하면 된다.
# 응답 원본은 more_*.txt 파일로 저장한다.
# ------------------------------------------------------------
import json
import time

import requests
from bs4 import BeautifulSoup

KEYWORD = "SK하이닉스"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://search.naver.com/",
}
SEARCH_URL = "https://search.naver.com/search.naver"
MORE_URL = "https://s.search.naver.com/p/newssearch/3/api/tab/more"
TITLE_SELECTOR = "span.sds-comps-text-type-headline1"


def titles_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for span in soup.select(TITLE_SELECTOR):
        a = span.find_parent("a")
        if a:
            out.append((span.get_text(strip=True), a.get("href")))
    return out


def find_html_strings(obj, path="", found=None):
    """JSON 안을 돌면서 HTML 조각으로 보이는 문자열의 위치를 찾는다."""
    if found is None:
        found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            find_html_strings(v, f"{path}.{k}", found)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_html_strings(v, f"{path}[{i}]", found)
    elif isinstance(obj, str) and "<" in obj and len(obj) > 200:
        found.append((path, obj))
    return found


def show(name, res):
    print(f"\n===== {name} =====")
    print(f"상태코드 {res.status_code} | Content-Type {res.headers.get('Content-Type')} | 길이 {len(res.text)}")
    with open(f"more_{name}.txt", "w", encoding="utf-8") as f:
        f.write(res.text)

    items = []
    try:
        data = res.json()
        print("JSON 맨 위 키:", list(data.keys()) if isinstance(data, dict) else type(data).__name__)
        for path, html in find_html_strings(data):
            got = titles_from_html(html)
            print(f"  HTML 조각 위치: {path} (길이 {len(html)}) -> 제목 {len(got)}개")
            items.extend(got)
    except ValueError:
        print("JSON이 아닙니다. HTML로 보고 읽습니다.")
        items = titles_from_html(res.text)

    print(f"찾은 제목 {len(items)}개")
    for title, _ in items[:5]:
        print("  ", title[:60])
    return items


def more_params(start, full=False, day=None):
    params = {
        "ssc": "tab.news.all",
        "query": KEYWORD,
        "sort": "1",
        "start": start,
        "nso": "so:dd,p:all,a:all",
    }
    if day:
        params.update({"pd": "3", "ds": day, "de": day,
                       "nso": f"so:dd,p:from{day.replace('.', '')}to{day.replace('.', '')},a:all"})
    if full:   # 브라우저가 보낸 것과 비슷하게 나머지 값도 채움
        params.update({"abt": "null", "field": "0", "is_dts": "0", "is_sug_officeid": "0", "mynews": "0",
                       "office_category": "0", "office_section_code": "0", "office_type": "0",
                       "photo": "0", "qdt": "0", "rev": "0", "service_area": "0", "sm": "tab_smr",
                       "spq": "0"})
    return params


results = {}

res = requests.get(SEARCH_URL, params={"where": "news", "query": KEYWORD, "sort": "1"}, headers=HEADERS, timeout=10)
results["page1"] = show("page1", res)
time.sleep(1.5)

res = requests.get(MORE_URL, params=more_params(11), headers=HEADERS, timeout=10)
results["start11_min"] = show("start11_min", res)
time.sleep(1.5)

res = requests.get(MORE_URL, params=more_params(11, full=True), headers=HEADERS, timeout=10)
results["start11_full"] = show("start11_full", res)
time.sleep(1.5)

res = requests.get(MORE_URL, params=more_params(21), headers=HEADERS, timeout=10)
results["start21_min"] = show("start21_min", res)
time.sleep(1.5)

res = requests.get(MORE_URL, params=more_params(1, day="2026.09.29"), headers=HEADERS, timeout=10)
results["day_0929"] = show("day_0929", res)

links = {k: {l for _, l in v} for k, v in results.items()}
print("\n===== 결과 =====")
print(f"1페이지 vs start=11(최소 파라미터) 겹침: {len(links['page1'] & links['start11_min'])} / {len(links['start11_min'])}")
print(f"1페이지 vs start=11(전체 파라미터) 겹침: {len(links['page1'] & links['start11_full'])} / {len(links['start11_full'])}")
print(f"start=11 vs start=21 겹침: {len(links['start11_min'] & links['start21_min'])} / {len(links['start21_min'])}")
print(f"세 페이지 합쳐 서로 다른 기사: {len(links['page1'] | links['start11_min'] | links['start21_min'])}")
print(f"9/29 날짜 지정 결과: {len(links['day_0929'])}개 (위 제목이 9/29 기사인지 확인)")
print("응답 원본은 more_*.txt 파일에 저장했습니다.")
