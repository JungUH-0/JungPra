# import pandas as pd
# df = pd.read_csv("news_sentiment.csv", encoding="utf-8-sig")
# print(repr(df["link"].iloc[85]))
# import pandas as pd

# df = pd.read_csv("news_sentiment.csv", encoding="utf-8-sig")

# # 링크에 콤마가 섞여 들어간 이상한 행 찾기
# broken = df[df["link"].str.contains(",", na=False)]
# print("문제 있는 행 개수:", len(broken))
# print(broken[["title", "link"]].head(10))

import pandas as pd
 
CSV_PATH = "news_sentiment.csv"
 
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
 
# link를 맨 뒤로 보내서 title의 콤마 등이 있어도 엑셀에서 옆 칸과 안 헷갈리게 함
new_order = ["keyword", "title", "label", "score", "collected_at", "link"]
df = df[new_order]
 
df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
 
print(f"완료: {len(df)}행, 열 순서 -> {list(df.columns)}")