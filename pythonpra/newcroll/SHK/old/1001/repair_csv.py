# repair_csv.py
# ------------------------------------------------------------
# news_sentiment.csv 한 번 정리용 스크립트.
#   1) 원본을 날짜시각 붙여서 백업
#   2) 열이 밀려서 저장된 행(label 칸에 URL이 들어간 행)을 원래 순서로 되돌림
#   3) 같은 키워드 + 같은 link 중복 제거 (먼저 저장된 것 남김)
#   4) 같은 키워드 + 같은 날짜 + 같은 제목 중복 제거 (연합뉴스 사진기사 등)
#   5) 다른 키워드끼리 같은 기사(link)는 한 행으로 합치고
#      keyword 칸을 "삼성전자|SK하이닉스"처럼 이어 적음
#
# 여러 번 실행해도 결과가 같다 (이미 정리된 파일이면 바뀌는 것 없음).
# ------------------------------------------------------------
import csv
import os
import shutil
from datetime import datetime

import pandas as pd

from collector import CSV_PATH, COLUMNS, KEYWORD_SEP, split_keywords, join_keywords


def main():
    if not os.path.exists(CSV_PATH):
        print(f"{CSV_PATH}가 없습니다.")
        return

    # 1) 백업
    backup_path = f"news_sentiment_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    shutil.copy(CSV_PATH, backup_path)
    print(f"백업: {backup_path}")

    # 2) 한 줄씩 읽으면서 밀린 행 되돌리기
    #    pandas로 바로 읽으면 헤더 이름대로 칸을 붙여버려서, 밀린 행을 구분하기 어려움
    #    그래서 csv 모듈로 칸 순서 그대로 읽는다
    records = []
    shifted_count = 0
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)

        if header != COLUMNS:
            print(f"헤더가 예상과 다릅니다: {header}")
            print("수동 확인이 필요해서 중단합니다. (원본은 그대로, 백업도 남아 있음)")
            return

        for row in reader:
            if not row:
                continue
            keyword, title, c3, c4, c5, c6 = row

            if c3.startswith("http"):
                # 밀린 행: keyword, title, link, label, score, collected_at 순서로 저장돼 있음
                link, label, score, collected_at = c3, c4, c5, c6
                shifted_count += 1
            else:
                # 정상 행: keyword, title, label, score, collected_at, link
                label, score, collected_at, link = c3, c4, c5, c6

            records.append({
                "keyword": keyword,
                "title": title,
                "label": label,
                "score": float(score),
                "collected_at": collected_at,
                "link": link,
            })

    df = pd.DataFrame(records, columns=COLUMNS)
    total_before = len(df)

    # 3) 같은 키워드 + 같은 link 중복 제거
    before = len(df)
    df = df.drop_duplicates(subset=["keyword", "link"], keep="first")
    link_dup_count = before - len(df)

    # 4) 같은 키워드 + 같은 날짜 + 같은 제목 중복 제거
    before = len(df)
    df["_date"] = df["collected_at"].str[:10]
    df = df.drop_duplicates(subset=["keyword", "_date", "title"], keep="first")
    df = df.drop(columns="_date")
    title_dup_count = before - len(df)

    # 5) 다른 키워드끼리 같은 기사(link)는 한 행으로 합치기
    #    먼저 저장된 행의 제목·감성·수집시각을 남기고, keyword 칸만 "삼성전자|SK하이닉스"처럼 합침
    before = len(df)
    merged_rows = {}
    for row in df.to_dict("records"):
        link = row["link"]
        if link not in merged_rows:
            row["_kws"] = split_keywords(row["keyword"])
            merged_rows[link] = row
        else:
            merged_rows[link]["_kws"] += split_keywords(row["keyword"])
    for row in merged_rows.values():
        row["keyword"] = join_keywords(row.pop("_kws"))
    df = pd.DataFrame(list(merged_rows.values()), columns=COLUMNS)
    cross_merge_count = before - len(df)

    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    multi = df["keyword"].str.contains(KEYWORD_SEP, regex=False).sum()

    print(f"\n원래 행 수: {total_before}")
    print(f"  열 순서 되돌린 행: {shifted_count}")
    print(f"  같은 키워드 link 중복 제거: {link_dup_count}")
    print(f"  같은 날 같은 제목 중복 제거: {title_dup_count}")
    print(f"  다른 키워드 중복을 한 행으로 합침: {cross_merge_count}")
    print(f"정리 후 행 수: {len(df)}")
    print(f"\n(참고) 키워드가 2개 이상 붙은 기사: {multi}건")


if __name__ == "__main__":
    main()
