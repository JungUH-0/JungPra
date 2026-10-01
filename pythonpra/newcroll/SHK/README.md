# 주식 뉴스 감성 분석 파이프라인

네이버 뉴스 제목을 크롤링해서 한국어 금융 감성 모델로 긍정·중립·부정을 판정하고,
날짜별 감성 흐름을 실제 주가 움직임과 비교하는 프로젝트.

> **뉴스 감성은 주가의 거울인가, 나침반인가?**
> 뉴스 분위기가 그날의 주가를 반영하는지(거울), 다음 날의 주가를 앞서가는지(나침반)를 데이터로 확인한다.

- 대상: 삼성전자, SK하이닉스, 코스피
- 감성 모델: [`snunlp/KR-FinBert-SC`](https://huggingface.co/snunlp/KR-FinBert-SC)
- 수집: 하루 4번 자동 (Windows 작업 스케줄러)
- 저장: SQLite (`news.db`)
- 서버: FastAPI + 정적 페이지 (Chart.js)
- 수집 시작: 2026-09-14

---

## 목차

1. [파이프라인](#1-파이프라인)
2. [기술 스택](#2-기술-스택)
3. [파일 구성](#3-파일-구성)
4. [DB 설계](#4-db-설계)
5. [감성 값 기준](#5-감성-값-기준)
6. [실행 방법](#6-실행-방법)
7. [API](#7-api)
8. [진행 과정과 문제 해결](#8-진행-과정과-문제-해결)
9. [주가 비교 결과 (첫 점검)](#9-주가-비교-결과-첫-점검)
10. [한계와 다음 단계](#10-한계와-다음-단계)

---

## 1. 파이프라인

```
[수집]                         [처리]                        [저장]       [활용]
작업 스케줄러                   collector.py                  db.py
 └ run_collect.bat ─┐           ├ 네이버 뉴스 검색 (3페이지)    │           ├─ start.py ─> 웹 페이지 / 조회 API
    └ collectall.py ├────────>  ├ 제목 필터 (키워드·동의어)  ──> news.db ──┼─ validate_stock.py ─> 주가 비교
FastAPI POST /collect ┘         ├ 키워드별 결과 합치기                      └─ export_db_to_csv.py ─> CSV 백업
                                └ KR-FinBert 감성분석
```

1. **수집**: 키워드마다 네이버 뉴스 최신순 검색 결과를 3페이지(최대 30건)까지 가져온다.
2. **필터**: 제목에 키워드나 동의어가 없는 기사는 버린다.
3. **합치기**: 같은 기사가 여러 키워드에 걸리면 한 건으로 합치고 키워드만 여러 개 붙인다.
4. **감성분석**: 새 기사만 모델에 넣어 세 라벨의 확률과 감성지수를 계산한다.
5. **저장**: 한 회차를 SQLite에 한 번에 커밋한다.
6. **활용**: 웹 페이지에서 키워드별 감성 흐름을 보고, 실제 주가 등락률과 비교한다.

---

## 2. 기술 스택

| 구분 | 사용 |
|---|---|
| 언어 | Python |
| 크롤링 | requests, BeautifulSoup |
| 감성 모델 | Hugging Face transformers, KR-FinBert-SC |
| 데이터 처리 | pandas, numpy |
| DB | SQLite (`sqlite3` 기본 모듈) |
| 서버 | FastAPI, uvicorn |
| 프론트 | HTML, JavaScript, Chart.js |
| 주가 | FinanceDataReader, pykrx |
| 시각화 | matplotlib |
| 자동 실행 | Windows 작업 스케줄러 + bat |

---

## 3. 파일 구성

| 파일 | 역할 |
|---|---|
| `collector.py` | 검색, 제목 필터, 동의어 사전, 감성분석, DB 저장. 수집 로직은 전부 여기 |
| `collectall.py` | 키워드 3개를 한 번에 수집하고 결과 출력 |
| `db.py` | DB 연결, 테이블 생성, 저장·조회 함수. DB를 쓰는 곳은 전부 이 파일을 거침 |
| `start.py` | FastAPI 서버. 웹 페이지와 조회 API |
| `static/index.html` | 웹 페이지 |
| `static/chart.umd.js` | Chart.js (CDN 대신 파일로 포함) |
| `validate_stock.py` | 뉴스 감성 vs 주가 등락률 비교. 직접 실행하면 표·그래프 생성 |
| `run_collect.bat` | 작업 스케줄러가 실행. 결과를 `collect_log.txt`에 남김 |
| `migrate_csv_to_db.py` | 기존 CSV를 DB로 옮김. 다른 환경에서 모은 CSV 합치기에도 사용 |
| `export_db_to_csv.py` | DB 내용을 `backup/` 폴더에 CSV로 내보냄 |
| `repair_csv.py` | DB 도입 전 CSV 정리(열 밀림 복구, 중복 합치기, 감성지수 채우기) |
| `check_pages.py`, `check_more_api.py` | 검색 페이지 넘김 방식 확인용 (한 번만 사용) |

---

## 4. DB 설계

### 왜 CSV에서 DB로 옮겼나

| 해야 하는 일 | CSV일 때 | DB로 바꾼 뒤 |
|---|---|---|
| 같은 기사 두 번 저장 방지 | 코드로 link를 하나씩 비교 | `link UNIQUE` 제약 |
| 한 기사에 키워드 여러 개 | `삼성전자\|SK하이닉스` 문자열로 이어 붙임 | 기사-키워드 연결 테이블 |
| 기존 기사에 키워드 추가 | 파일 전체를 다시 씀 | 연결 테이블에 한 줄 INSERT |
| 수집 중간에 실패 | 파일이 깨질 수 있음 | 한 회차를 한 번에 커밋, 실패하면 통째로 취소 |
| 수집 중에 서버가 읽기 | 쓰는 도중의 파일을 읽을 수 있음 | WAL 모드로 동시에 읽기 가능 |

SQLite를 고른 이유: DB 서버 설치가 필요 없고(파일 하나), 파이썬에 기본으로 들어 있으며, 하루 수십 건 규모에 충분하다.
SQL은 표준이라 나중에 MySQL·PostgreSQL로 옮겨도 `db.py`의 연결 부분만 바꾸면 된다.

### 테이블

```
articles                         article_keywords              keywords
--------------------------       ---------------------         ---------------
id (PK)                  <────── article_id (FK)          ┌──> id (PK)
link (UNIQUE)                    keyword_id (FK) ─────────┘    name (UNIQUE)
title, label, score              PK (article_id, keyword_id)
p_positive, p_neutral, p_negative
sentiment_index
collected_at

request_logs
-------------------------------------------------------------------------
id, time, keyword, page, source, start, status, titles, new_titles, elapsed_ms, result
```

| 테이블 | 내용 |
|---|---|
| `articles` | 기사 한 건 = 한 행. 제목, 감성 라벨, 확률, 감성지수, 수집 시각 |
| `keywords` | 삼성전자, SK하이닉스, 코스피 |
| `article_keywords` | 기사와 키워드의 다대다 연결 |
| `request_logs` | 네이버에 보낸 요청 하나하나의 기록. 차단 시점 확인용 |

한 기사가 여러 키워드에 걸릴 수 있어서 `articles`에는 키워드 칸이 없다. 키워드까지 보려면 JOIN한다.

```sql
SELECT a.id,
       GROUP_CONCAT(k.name, '|') AS keyword,
       a.title, a.label, a.sentiment_index, a.collected_at
FROM articles a
JOIN article_keywords ak ON ak.article_id = a.id
JOIN keywords k          ON k.id = ak.keyword_id
GROUP BY a.id
ORDER BY a.collected_at DESC;
```

### 저장 흐름

1. 검색 결과의 link로 DB에 이미 있는 기사인지 조회
2. 새 기사만 감성분석 (DB 연결을 잡지 않은 상태에서 먼저 실행)
3. 새 기사는 `articles`에 INSERT, 키워드는 `article_keywords`에 연결
4. 이미 있는 기사가 새 키워드에 걸리면 연결만 추가
5. 한 회차를 한 번에 `commit`

### JDBC 방식과 비교

| 항목 | Java + JDBC (Tomcat) | Python + SQLite |
|---|---|---|
| DB 서버 | Oracle/MySQL 서버를 따로 실행 | 없음. 파일 하나 |
| 드라이버 | `ojdbc.jar`, `mysql-connector.jar` | `sqlite3` 기본 내장 |
| 연결 정보 | URL, 계정, 비밀번호 | 파일 경로 |
| 연결 관리 | 커넥션 풀 (`context.xml`) | 필요할 때 열고 닫음 |
| DAO | `ArticleDAO.java` | `db.py` |
| 파라미터 바인딩 | `PreparedStatement`의 `?` | `conn.execute(sql, params)`의 `?` |

---

## 5. 감성 값 기준

| 값 | 뜻 |
|---|---|
| `label` | positive / neutral / negative (세 확률 중 가장 큰 것) |
| `score` | label의 확률. 감성의 세기가 아니라 모델의 **확신도** |
| `p_positive`, `p_neutral`, `p_negative` | 세 라벨 각각의 확률 (합 1) |
| `sentiment_index` | `p_positive − p_negative`. −1(부정) ~ +1(긍정). 트렌드와 주가 비교에 쓰는 값 |

`score`만 평균 내면 `negative 0.99`와 `positive 0.99`가 같은 값이 되어 분위기를 나타내지 못한다.
그래서 세 확률을 모두 받아 감성지수를 따로 계산한다. 화면 색은 국내 증시 관례대로 긍정 빨강, 부정 파랑.

---

## 6. 실행 방법

### 설치

```
pip install fastapi uvicorn pandas numpy requests beautifulsoup4 transformers torch finance-datareader pykrx matplotlib
```

감성 모델은 처음 실행할 때 Hugging Face에서 자동으로 내려받는다.

### 처음 한 번: 기존 CSV를 DB로

```
python migrate_csv_to_db.py
```

여러 번 실행해도 같은 기사가 두 번 들어가지 않는다. 다른 환경에서 모은 CSV는 `python migrate_csv_to_db.py 파일명.csv`로 합친다.

### 수집

```
python collectall.py
```

자동 수집은 작업 스케줄러에 `run_collect.bat`을 등록한다. (08:30 / 09:05 / 15:40 / 22:00)

### 서버

```
uvicorn start:app
```

브라우저에서 `http://127.0.0.1:8000/`

### 주가 비교 (표·그래프)

```
python validate_stock.py
```

### CSV로 내보내기

```
python export_db_to_csv.py
```

`backup/` 폴더에 기사와 요청 기록 CSV가 생긴다.

---

## 7. API

| 경로 | 내용 |
|---|---|
| `GET /` | 웹 페이지 |
| `GET /db/status` | DB에 쌓인 기사 수, 기간, 키워드별 건수 |
| `GET /sentiment/{keyword}` | 기사 수, 라벨 비율, 평균 감성지수, 평균 확신도 |
| `GET /trend/{keyword}?days=7` | 날짜별 감성지수와 라벨 수 |
| `GET /compare?keywords=...` | 키워드별 비교와 감성지수 순위 |
| `GET /validate/{keyword}` | 거래일별 감성지수와 주가 등락률, 방향 일치율, 기준선 |
| `GET /articles/{keyword}?limit=20` | 최근 기사 목록 |
| `GET /keywords` | 키워드 목록 |
| `POST /collect` | 키워드 하나 수집 (공개 배포 시 막아야 함) |

---

## 8. 진행 과정과 문제 해결

### 9/14 · 초기 구조
- `start.py` 하나에 수집과 조회 API를 두고, 하루 1번 키워드당 검색 첫 화면 10건을 수집

### 9/18 · 관련 없는 기사가 섞임 → 제목 필터와 동의어 사전
- 문제: "코스피" 검색에 일본 개각, 국민연금 기념 기사처럼 본문 끝에만 단어가 나오는 기사가 섞임
- 해결: 제목에 키워드나 동의어가 있어야 저장

  | 키워드 | 동의어 |
  |---|---|
  | 삼성전자 | 삼성전자, 삼성 전자, 삼성전자우, 삼전, 삼전닉스 |
  | SK하이닉스 | SK하이닉스, 하이닉스, 하닉, 삼전닉스, 삼전·닉스 |
  | 코스피 | 코스피, 코스피지수, 코스피200 |

- "삼성" 단독은 삼성물산·삼성생명이 섞이고, "닉스" 단독은 "피닉스"가 걸려서 제외

### 9/23 · 열 밀림 버그 → 공통 모듈
- 문제: 수집 코드가 두 파일에 따로 있어서 한쪽만 열 순서가 바뀌었고, 98행이 열이 밀린 채 저장됨. 그 결과 link 기준 중복 제거가 작동하지 않음
- 해결: 수집·필터·저장을 `collector.py` 하나로 모으고 열 순서를 한 곳에서 관리. `repair_csv.py`로 184행 → 175행 복구 (열 되돌림 98, 중복 제거 9)

### 9/23 · 같은 기사가 한 키워드에만 저장됨 → 키워드 합치기
- 문제: 삼성전자와 SK하이닉스 검색에 같이 나온 기사가 먼저 돈 키워드에만 저장됨
- 해결: 세 키워드 결과를 link 기준으로 합친 뒤 한 번에 저장. 감성분석도 기사당 한 번만

### 9/23 · 확신도 평균의 함정 → 감성지수
- 문제: `score` 평균은 긍정·부정 구분 없이 확신도만 평균 낸 값
- 해결: 세 라벨 확률을 모두 받아 `sentiment_index = p_positive − p_negative` 저장. 기존 기사도 다시 계산

### 9/26 · 주가 비교와 웹 페이지
- 뉴스 날짜를 거래일에 맞추고(주말 뉴스는 다음 거래일), 같은 날·다음 거래일 등락률과 방향을 비교
- 방향 일치율만 보면 착시가 생겨서, 뉴스 없이 더 자주 나온 방향만 찍었을 때의 **기준선**을 같이 표시
- 문제: 코스피 지수 데이터가 9/17에서 갱신이 멈춰 그 뒤 뉴스가 조용히 빠짐
- 해결: 가격 출처를 여러 개 시도해서 가장 최근까지 있는 것을 쓰고, 빠진 뉴스가 있으면 경고
- FastAPI가 정적 페이지까지 제공. 감성지수 선과 등락률 막대를 위아래로 두고 같은 날짜를 함께 강조

### 9/30 · 표본 부족 → 검색 2~3페이지 확장
- 문제: 제목 필터 후 키워드당 하루 몇 건밖에 남지 않음. 검색 주소에 `start`를 붙여도 네이버가 무시하고 늘 첫 페이지만 줌
- 분석: 브라우저 개발자 도구 Network 탭에서, 스크롤할 때 다음 기사를 받아오는 요청을 찾음
- 해결: 2페이지부터는 그 요청으로 받아 키워드당 후보 10건 → 최대 30건. Selenium 없이 requests만으로 처리
- 키워드당 필터 통과 기사가 늘어남 (SK하이닉스는 줄임말 추가 후 3건 → 13건)

### 9/30 · 차단 대비
- 요청 간격 3~4.5초 무작위, 회차당 요청 9번
- 상태코드 403/429, 자동입력 방지 화면, 첫 페이지 0건이면 차단 의심으로 보고 남은 키워드 중단. 모은 기사는 저장
- 요청 하나하나를 로그로 남겨 언제부터 막혔는지 확인 가능
- 정상 페이지 스크립트에도 "captcha" 단어가 들어 있어 오탐이 났던 문제 → 제목을 하나도 못 받았을 때만 문구 검사

### 9/30 · 하루 4번 자동 수집
- 08:30(장 전) / 09:05(장 시작 직후) / 15:40(장 마감 후) / 22:00(저녁)
- 한글이 들어간 bat 파일이 cmd에서 깨지는 문제 → bat은 영문만 사용

### 10/1 · SQLite 연결
- 수집 → 저장 → 조회 → 분석을 하나의 DB로 연결 (4장)
- 확인 (9/14 ~ 9/23 데이터 165건)
  - CSV → DB 옮긴 뒤 키워드별 건수 동일, 다시 실행해도 중복 없음
  - 조회 API와 주가 비교 결과가 CSV 때와 값이 같음
  - 키워드 합치기, 중복 처리, 중간 차단 시 부분 저장이 DB에서도 그대로 동작

---

## 9. 주가 비교 결과 (첫 점검)

9/14 ~ 9/23, 8거래일. 제목 필터 적용 전 데이터가 섞여 있고 수집은 대부분 하루 한 번(09시대)이었다.

| 키워드 | 같은 날 일치 | 기준선 | 다음 거래일 일치 | 기준선 |
|---|---|---|---|---|
| 삼성전자 | 7/8 | 7/8 | 5/7 | 7/7 |
| SK하이닉스 | 7/8 | 6/8 | 3/7 | 6/7 |
| 코스피 | 6/8 | 5/8 | 4/7 | 5/7 |

- **같은 날 (거울)**: 기준선과 같거나 약간 높음. 장중 기사는 이미 일어난 움직임을 보도하는 경우가 많아 반영에 가깝다.
- **다음 거래일 (나침반)**: 세 키워드 모두 기준선보다 낮음. 예측력은 아직 보이지 않는다.
- 현재 결론: "뉴스 감성은 그날 시장 분위기를 반영한다"까지만 말할 수 있는 단계. 거래일이 적어 확정할 수 없다.

---

## 10. 한계와 다음 단계

### 한계
- 수집 시점 기준 최신 30건이라 "그날 기사 전부"가 아니다.
- 제목만 분석한다. 본문의 맥락은 반영되지 않는다.
- 수집 시각 기준으로 날짜를 나눈다. 기사가 실제로 나온 시각과 다를 수 있다.
- 거래일 수가 적어 통계적으로 확정할 수 없다.
- 네이버 검색 화면 구조가 바뀌면 수집 코드를 고쳐야 한다.

### 다음 단계
- 기사 작성 시각(`published_at`) 저장
- 시간대별 비교: 장 전·전날 저녁 기사 → 그날 등락률(예측), 장중·마감 기사 → 그날 등락률(보도)
- 거래일 20일 이상 쌓이면 다시 비교
- 날짜 지정 수집으로 빠진 날 채우기
- 링크 정규화, 언론사 저장
- 배포 (공개 시 `/collect` 차단)

---

## 참고

- 이 프로젝트의 결과는 학습 목적의 분석이며 투자 판단의 근거가 아니다.
- 뉴스 제목은 각 언론사에 저작권이 있다. 저장소에는 수집 데이터를 올리지 않는다.

### .gitignore

```
news.db
news.db-wal
news.db-shm
backup/
price_cache/
__pycache__/
collect_log.txt
request_log.csv
news_sentiment.csv
validation_daily.csv
validation_chart.png
```
