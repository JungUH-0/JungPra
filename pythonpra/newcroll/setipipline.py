import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import pandas as pd

def get_naver_news(keyword, count=10):
    url = "https://search.naver.com/search.naver"
    params = {"where": "news", "query": keyword, "sort": "1"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    res = requests.get(url, params=params, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    articles = []
    title_spans = soup.select("span.sds-comps-text-type-headline1")[:count]
    for span in title_spans:
        parent_a = span.find_parent("a")
        if parent_a:
            articles.append({
                "title": span.get_text(strip=True),
                "link": parent_a.get("href")
            })
    return articles


def analyze_sentiment(articles, classifier):
    results = []
    for article in articles:
        sentiment = classifier(article["title"])[0]
        results.append({
            "title": article["title"],
            "link": article["link"],
            "label": sentiment["label"],
            "score": sentiment["score"]
        })
    return results


if __name__ == "__main__":
    classifier = pipeline("sentiment-analysis", model="snunlp/KR-FinBert-SC")

    keyword = "삼성전자"
    articles = get_naver_news(keyword, count=10)
    results = analyze_sentiment(articles, classifier)

    df = pd.DataFrame(results)
    print(df)

    print("SENTIMENT DISTRIBUTION#####################")
    print(df["label"].value_counts())