# check_pages.py
# ------------------------------------------------------------
# 네이버 뉴스 검색에서 2·3페이지(start=11, 21)가 requests로 받아지는지 확인한다.
# 요청은 딱 3번만 보낸다. 한 번만 실행하면 된다.
# ------------------------------------------------------------
import time

import requests
from bs4 import BeautifulSoup

KEYWORD = "SK하이닉스"
URL = "https://search.naver.com/search.naver"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

pages = {}
for page, start in enumerate([1, 11, 21], start=1):
    params = {"where": "news", "query": KEYWORD, "sort": "1", "start": start}
    res = requests.get(URL, params=params, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")

    if page == 1:
        # 나중에 기사 작성 시각 위치를 찾을 때 쓰려고 1페이지 HTML을 남겨둔다
        with open("naver_page1.html", "w", encoding="utf-8") as f:
            f.write(res.text)

    items = []
    for span in soup.select("span.sds-comps-text-type-headline1"):
        a = span.find_parent("a")
        if a:
            items.append((span.get_text(strip=True), a.get("href")))
    pages[page] = items

    print(f"\n===== {page}페이지 (start={start}) 상태코드 {res.status_code}, 제목 {len(items)}개 =====")
    for title, _ in items:
        print("  ", title[:60])

    time.sleep(1.5)

links = {p: {link for _, link in items} for p, items in pages.items()}
print("\n===== 결과 =====")
print(f"1페이지와 2페이지 겹치는 기사: {len(links[1] & links[2])}개 / 2페이지 {len(links[2])}개")
print(f"1페이지와 3페이지 겹치는 기사: {len(links[1] & links[3])}개 / 3페이지 {len(links[3])}개")
print(f"세 페이지 합쳐 서로 다른 기사: {len(links[1] | links[2] | links[3])}개")

if links[2] and not (links[1] & links[2]):
    print("-> 페이지 넘김이 됩니다. requests로 2~3페이지까지 수집할 수 있습니다.")
elif links[2] and links[2] <= links[1]:
    print("-> 2페이지가 1페이지와 같습니다. requests로는 페이지가 안 넘어갑니다.")
else:
    print("-> 일부만 겹치거나 비었습니다. 위 제목 목록을 보여주세요.")
print("(1페이지 HTML은 naver_page1.html로 저장했습니다)")
