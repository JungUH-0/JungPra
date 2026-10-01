# import requests
# from bs4 import BeautifulSoup

# url = "https://search.naver.com/search.naver"
# params = {"where": "news", "query": "삼성전자", "sort": "1"}
# headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# res = requests.get(url, params=params, headers=headers)
# soup = BeautifulSoup(res.text, "html.parser")

# title_spans = soup.select("span.sds-comps-text-type-headline1")
# print(f"찾은 제목 개수: {len(title_spans)}")

# print("\n실제 제목들 (필터링 전)#####################")
# for span in title_spans[:15]:
#     print(span.get_text(strip=True))

import requests
from bs4 import BeautifulSoup
 
url = "https://search.naver.com/search.naver"
params = {"where": "news", "query": "코스피", "sort": "1"}
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
 
res = requests.get(url, params=params, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")
 
title_spans = soup.select("span.sds-comps-text-type-headline1")
print(f"찾은 제목 개수: {len(title_spans)}")
 
print("\n실제 제목들 (필터링 전)#####################")
for span in title_spans[:15]:
    print(span.get_text(strip=True))
