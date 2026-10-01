# import requests
# from bs4 import BeautifulSoup

# url = "https://www.melon.com/chart/index.htm"
# hdr = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
#     'Referer': 'https://www.melon.com/',
# }

# res = requests.get(url, headers=hdr)
# print("상태코드:", res.status_code)

# with open("melon_debug.html", "w", encoding="utf-8") as f:
#     f.write(res.text)

# soup = BeautifulSoup(res.text, "lxml")

# # 차트 표를 감싸는 tbody 찾기 (멜론은 보통 id="tb_list"인 tbody 안에 tr들이 있음)
# tbody = soup.select_one("tbody#tb_list")
# print("\ntbody#tb_list 존재 여부:", tbody is not None)

# if tbody:
#     rows = tbody.find_all("tr")
#     print("행(tr) 개수:", len(rows))

#     if rows:
#         first = rows[0]
#         print("\n첫 번째 행 축약 미리보기#####################")
#         print(str(first)[:1500])
# else:
#     # 못 찾으면 class에 'chart' 들어간 table/tbody 후보 훑기
#     print("\ntable/tbody class 후보#####################")
#     for tag in soup.find_all(["table", "tbody"], class_=True):
#         print(tag.name, tag.get("class"), tag.get("id"))

# print("\n본문에 '차트' 텍스트 포함 개수:", res.text.count("차트"))

# import requests
# from bs4 import BeautifulSoup
# import re

# url = "https://www.melon.com/chart/index.htm"
# hdr = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
#     'Referer': 'https://www.melon.com/',
# }

# res = requests.get(url, headers=hdr)
# print("상태코드:", res.status_code)
# print("응답 길이:", len(res.text))

# with open("melon_debug.html", "w", encoding="utf-8") as f:
#     f.write(res.text)

# soup = BeautifulSoup(res.text, "lxml")

# # 1. 모든 table 태그 훑기 (id/class 상관없이)
# tables = soup.find_all("table")
# print("\ntable 태그 총 개수:", len(tables))
# for i, t in enumerate(tables):
#     print(f"  table[{i}] id={t.get('id')} class={t.get('class')}")

# # 2. id에 'list' 또는 'chart' 포함된 아무 태그나
# print("\nid에 'list' 또는 'chart' 포함된 태그#####################")
# for tag in soup.find_all(id=re.compile("list|chart", re.I)):
#     print(f"  <{tag.name}> id={tag.get('id')}")

# # 3. class에 'song' 또는 'rank' 포함된 아무 태그나 (상위 20개만)
# print("\nclass에 'song' 또는 'rank' 포함된 태그#####################")
# found = soup.find_all(class_=re.compile("song|rank", re.I))
# for tag in found[:20]:
#     print(f"  <{tag.name}> class={tag.get('class')}")

# # 4. <title> 태그 확인 (혹시 차단 페이지인지)
# title_tag = soup.find("title")
# print("\n<title> 내용:", title_tag.get_text() if title_tag else None)

# # 5. 캡차/로봇 확인 문구 체크
# for kw in ["captcha", "robot", "차단", "비정상"]:
#     if kw in res.text.lower():
#         print(f"'{kw}' 키워드 발견 -> 봇 차단 가능성")

import requests
from bs4 import BeautifulSoup

url = "https://www.melon.com/chart/index.htm"
hdr = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Referer': 'https://www.melon.com/',
}

res = requests.get(url, headers=hdr)
soup = BeautifulSoup(res.text, "lxml")

tb_list = soup.find("div", id="tb_list")

# tb_list 안에서 곡 한 곡을 감싸는 반복 단위 후보들을 찾아본다
# service_list_song 안의 li 또는 tr 구조를 확인
song_list_div = soup.find("div", class_="service_list_song")
print("service_list_song 존재:", song_list_div is not None)

if song_list_div:
    # 그 하위에서 가장 바깥 반복 태그 찾기 (보통 tr 또는 li)
    trs = song_list_div.find_all("tr")
    lis = song_list_div.find_all("li")
    print("tr 개수:", len(trs))
    print("li 개수:", len(lis))

    # 더 많이 반복되는 쪽을 한 곡 단위로 추정
    unit = trs if len(trs) > len(lis) else lis
    if unit:
        print("\n한 곡 단위 HTML 미리보기#####################")
        print(str(unit[0])[:2000])
