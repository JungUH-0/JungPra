# repair_csv.py
# ------------------------------------------------------------
# news_sentiment.csv 정리용 스크립트.
#   1) 원본을 날짜시각 붙여서 백업
#   2) 열이 밀려서 저장된 행(label 칸에 URL이 들어간 행)을 원래 순서로 되돌림
#   3) 같은 키워드 + 같은 link 중복 제거 (먼저 저장된 것 남김)
#   4) 같은 키워드 + 같은 날짜 + 같은 제목 중복 제거 (연합뉴스 사진기사 등)
#   5) 다른 키워드끼리 같은 기사(link)는 한 행으로 합치고
#      keyword 칸을 "삼성전자|SK하이닉스"처럼 이어 적음
#   6) 감성지수(세 라벨 확률)가 비어 있는 기사는 저장된 제목으로 모델을 다시 돌려 채움
#
# 감성지수 열이 없는 옛 파일(6열)과 새 파일(10열)을 둘 다 읽을 수 있다.
# 여러 번 실행해도 결과가 같다 (이미 정리된 파일이면 바뀌는 것 없음).
# ------------------------------------------------------------
import csv
import os
import shutil
from datetime import datetime

import pandas as pd

from collector import (
    CSV_PATH, COLUMNS, OLD_COLUMNS, KEYWORD_SEP,
    split_keywords, join_keywords, analyze_title,
)

SENTIMENT_COLUMNS = ["p_positive", "p_neutral", "p_negative", "sentiment_index"]


def to_float(value):
    return float(value) if value not in ("", None) else float("nan")


def read_rows():
    """
    CSV를 한 줄씩 칸 순서 그대로 읽는다.
    pandas로 바로 읽으면 헤더 이름대로 칸을 붙여버려서, 밀린 행을 구분하기 어렵기 때문.
    반환: (records, 밀린 행 수) / 헤더를 모르면 None
    """
    records = []
    shifted_count = 0

    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)

        if header == OLD_COLUMNS:
            for row in reader:
                if not row:
                    continue
                keyword, title, c3, c4, c5, c6 = row
                if c3.startswith("http"):
                    # 밀린 행: keyword, title, link, label, score, collected_at
                    link, label, score, collected_at = c3, c4, c5, c6
                    shifted_count += 1
                else:
                    label, score, collected_at, link = c3, c4, c5, c6

                record = {
                    "keyword": keyword, "title": title,
                    "label": label, "score": float(score),
                    "collected_at": collected_at, "link": link,
                }
                for col in SENTIMENT_COLUMNS:
                    record[col] = float("nan")
                records.append(record)

        elif header == COLUMNS:
            for row in reader:
                if not row:
                    continue
                record = dict(zip(COLUMNS, row))
                record["score"] = to_float(record["score"])
                for col in SENTIMENT_COLUMNS:
                    record[col] = to_float(record[col])
                records.append(record)

        else:
            print(f"헤더가 예상과 다릅니다: {header}")
            return None

    return records, shifted_count


def main():
    if not os.path.exists(CSV_PATH):
        print(f"{CSV_PATH}가 없습니다.")
        return

    # 1) 백업
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"news_sentiment_backup_{stamp}.csv"
    n = 2
    while os.path.exists(backup_path):          # 같은 초에 두 번 돌려도 이전 백업을 덮어쓰지 않게
        backup_path = f"news_sentiment_backup_{stamp}_{n}.csv"
        n += 1
    shutil.copy(CSV_PATH, backup_path)
    print(f"백업: {backup_path}")

    # 2) 읽으면서 밀린 행 되돌리기
    result = read_rows()
    if result is None:
        print("수동 확인이 필요해서 중단합니다. (원본은 그대로, 백업도 남아 있음)")
        return
    records, shifted_count = result

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
    #    먼저 저장된 행의 제목·감성·수집시각을 남기고, keyword 칸만 합침
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
    df = pd.DataFrame(list(merged_rows.values()), columns=COLUMNS).reset_index(drop=True)
    cross_merge_count = before - len(df)

    # 6) 감성지수가 비어 있는 기사 채우기
    #    기존 label/score는 그대로 두고, 세 라벨 확률과 감성지수만 새로 넣는다.
    #    모델은 같은 제목에 항상 같은 결과를 내므로, 다시 돌린 1등 라벨이 기존 label과 같아야 정상.
    need = df["sentiment_index"].isna()
    filled_count = int(need.sum())
    label_mismatch = 0

    if filled_count > 0:
        print(f"\n감성지수 채우는 중: {filled_count}건 (모델 로드에 잠깐 걸림)")
        for i, idx in enumerate(df.index[need], start=1):
            result = analyze_title(df.at[idx, "title"])
            for col in SENTIMENT_COLUMNS:
                df.at[idx, col] = result[col]
            if result["label"] != df.at[idx, "label"]:
                label_mismatch += 1
            if i % 50 == 0 or i == filled_count:
                print(f"  {i}/{filled_count}")

    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    multi = df["keyword"].str.contains(KEYWORD_SEP, regex=False).sum()

    print(f"\n원래 행 수: {total_before}")
    print(f"  열 순서 되돌린 행: {shifted_count}")
    print(f"  같은 키워드 link 중복 제거: {link_dup_count}")
    print(f"  같은 날 같은 제목 중복 제거: {title_dup_count}")
    print(f"  다른 키워드 중복을 한 행으로 합침: {cross_merge_count}")
    print(f"  감성지수 새로 채움: {filled_count}")
    if filled_count > 0:
        print(f"    (다시 돌린 라벨이 기존 label과 다른 기사: {label_mismatch}건 - 0이 정상)")
    print(f"정리 후 행 수: {len(df)}")
    print(f"\n(참고) 키워드가 2개 이상 붙은 기사: {multi}건")


if __name__ == "__main__":
    main()
