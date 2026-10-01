# import requests
# from bs4 import BeautifulSoup

# url = "https://search.naver.com/search.naver"
# params = {"where": "news", "query": "삼성전자", "sort": "1"}
# headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# res = requests.get(url, params=params, headers=headers)
# soup = BeautifulSoup(res.text, "html.parser")

# # 1. news_tit이라는 단어가 원본 HTML 안에 있는지 확인
# print("news_tit 포함 여부#####################")
# print("news_tit" in res.text)

# # 2. 받아온 HTML을 파일로 저장해서 직접 열어보기
# with open("naver_debug.html", "w", encoding="utf-8") as f:
#     f.write(res.text)

# # 3. <a> 태그들의 class 속성을 몇 개만 훑어보기
# print("A 태그 CLASS 샘플#####################")
# for a in soup.find_all("a")[:30]:
#     if a.get("class"):
#         print(a.get("class"))

import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

for keyword in ["삼성전자", "SK하이닉스"]:
    url = "https://search.naver.com/search.naver"
    params = {"where": "news", "query": keyword, "sort": "1"}
    res = requests.get(url, params=params, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    title_spans = soup.select("span.sds-comps-text-type-headline1")
    print(f"\n===== {keyword}: 찾은 제목 개수 {len(title_spans)} =====")
    for span in title_spans[:20]:
        print(span.get_text(strip=True))