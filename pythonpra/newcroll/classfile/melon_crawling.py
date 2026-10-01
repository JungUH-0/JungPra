import csv
import os
import time
import requests
from bs4 import BeautifulSoup

# ------------------------------------------------------------
# 레고 노트북과 같은 패턴:
#   1) 요청 -> soup 생성
#   2) 반복되는 태그(곡 행) 찾기
#   3) 각 행에서 순위/곡명/가수/이미지 추출
#   4) 이미지 다운로드
#   5) CSV로 저장
# ------------------------------------------------------------

url = "https://www.melon.com/chart/index.htm"
hdr = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Referer': 'https://www.melon.com/',
}

res = requests.get(url, headers=hdr)
print(f"상태코드: {res.status_code}")

if res.status_code != 200:
    print("페이지를 불러오지 못했습니다.")
    raise SystemExit

soup = BeautifulSoup(res.text, "lxml")

song_list_div = soup.find("div", class_="service_list_song")
all_trs = song_list_div.find_all("tr")

# 헤더 행(th만 있는 행)은 제외하고, 실제 곡 정보가 든 행(td가 있는 행)만 사용
song_rows = [tr for tr in all_trs if tr.find("td")]
print(f"수집된 곡 수: {len(song_rows)}")

img_dir_name = "멜론앨범이미지"
if not os.path.isdir(img_dir_name):
    os.mkdir(img_dir_name)
cur_dir = os.getcwd()

filename = "멜론_차트.csv"
f = open(filename, "w", encoding="utf-8-sig", newline="")
writer = csv.writer(f)
writer.writerow(["순위", "곡명", "가수", "앨범", "이미지경로"])

for tr in song_rows:
    # 순위
    rank_tag = tr.find("span", class_="rank")
    rank = rank_tag.get_text(strip=True) if rank_tag else None

    # 곡명 (rank01), 가수/앨범 (rank02)
    title_tag = tr.find("div", class_="ellipsis rank01")
    title = None
    if title_tag:
        a_tag = title_tag.find("a")
        title = a_tag.get_text(strip=True) if a_tag else title_tag.get_text(strip=True)

    artist_tag = tr.find("div", class_="ellipsis rank02")
    artist = None
    album = None
    if artist_tag:
        a_tags = artist_tag.find_all("a")
        if len(a_tags) >= 1:
            artist = a_tags[0].get_text(strip=True)
        if len(a_tags) >= 2:
            album = a_tags[1].get_text(strip=True)

    # 앨범 이미지
    img_tag = tr.find("img")
    img_url = img_tag.get("src") if img_tag else None

    print(rank, title, artist, album)

    img_path = None
    if img_url and rank:
        img_path = f"{cur_dir}/{img_dir_name}/{rank}_{(title or 'unknown').replace('/', '_')}.jpg"
        try:
            img_res = requests.get(img_url, headers=hdr)
            with open(img_path, "wb") as out:
                out.write(img_res.content)
        except Exception as e:
            print(f"이미지 다운로드 실패: {e}")
            img_path = None

    writer.writerow([rank, title, artist, album, img_path])

f.close()
print(f"\n완료: {filename} 저장됨")
