# export_db_to_csv.py
# ------------------------------------------------------------
# news.db의 내용을 CSV로 내보낸다. (백업 / 엑셀로 열어보기 / 제출용)
#
# 사용법 (SHK 폴더에서)
#   python export_db_to_csv.py
#
# backup 폴더에 날짜·시간이 붙은 파일 두 개가 생긴다.
#   news_sentiment_YYYYMMDD_HHMM.csv   기사 (예전 news_sentiment.csv와 같은 열 구성)
#   request_log_YYYYMMDD_HHMM.csv      요청 기록
#
# DB가 원본이고 이 파일들은 복사본이다. 이 CSV를 고쳐도 DB에는 반영되지 않는다.
# ------------------------------------------------------------
from datetime import datetime
from pathlib import Path

import db

BACKUP_DIR = Path(__file__).resolve().parent / "backup"


def main():
    if not db.has_data():
        print("DB에 기사가 없습니다. 먼저 migrate_csv_to_db.py 또는 collectall.py를 돌리세요.")
        return

    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")

    articles = db.articles_df()
    articles_path = BACKUP_DIR / f"news_sentiment_{stamp}.csv"
    articles.to_csv(articles_path, index=False, encoding="utf-8-sig")   # 엑셀에서 한글 안 깨지게

    logs = db.request_logs_df().drop(columns=["id"])
    logs_path = BACKUP_DIR / f"request_log_{stamp}.csv"
    logs.to_csv(logs_path, index=False, encoding="utf-8-sig")

    print(f"기사 {len(articles)}건 -> {articles_path}")
    print(f"요청 기록 {len(logs)}줄 -> {logs_path}")


if __name__ == "__main__":
    main()
