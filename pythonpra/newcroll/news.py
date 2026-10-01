import requests
from bs4 import BeautifulSoup

def get_naver_news(keyword, count=10):
    url = "https://search.naver.com/search.naver"
    params = {
        "where": "news",
        "query": keyword,
        "sort": "1"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    res = requests.get(url, params=params, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    articles = []
    # 새 구조: 제목은 이 클래스를 가진 span 안에 있고, 그 부모 a태그에 링크가 있음
    title_spans = soup.select("span.sds-comps-text-type-headline1")[:count]

    for span in title_spans:
        parent_a = span.find_parent("a")
        if parent_a:
            articles.append({
                "title": span.get_text(strip=True),
                "link": parent_a.get("href")
            })

    return articles


if __name__ == "__main__":
    results = get_naver_news("삼성전자", count=10)
    for r in results:
        print(r["title"])
        print(r["link"])
        print("-" * 40)