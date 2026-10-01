# newcroll

파이썬 웹 크롤링 연습과, 주식 뉴스 감성 분석 프로젝트의 초기 테스트를 모아 둔 폴더.

완성된 프로젝트는 **[SHK](./SHK)** 폴더에 있다.

| 폴더 | 내용 |
|---|---|
| [`SHK/`](./SHK) | **주식 뉴스 감성 분석 파이프라인** (최종본). 수집 → SQLite 저장 → API·웹 페이지 → 주가 비교 |
| `classfile/` | 수업 크롤링 실습 (멜론 차트, 레고 제품, 네이버 지도·뉴스) |
| (이 폴더 바로 아래) | SHK로 옮기기 전의 뉴스 크롤링·감성분석 테스트 코드 |

---

## classfile · 크롤링 실습

| 파일 | 내용 |
|---|---|
| `melon_crawling.py`, `melon_crawling.ipynb` | 멜론 차트 순위·곡명·가수·앨범 이미지 수집 → CSV |
| `melon_detail_crawling.ipynb` | 멜론 곡 상세 페이지 수집 |
| `melon_check.py` | 멜론 페이지 응답·HTML 구조 확인 |
| `lego_crawling.ipynb` | 레고 제품 정보·이미지 수집 → CSV |
| `naverMap.ipynb` | 네이버 지도 크롤링 실습 |
| `naverNews.ipynb` | 네이버 뉴스 크롤링 실습 |

공통 흐름: 요청 → BeautifulSoup으로 파싱 → 반복되는 태그 찾기 → 필요한 값 추출 → 이미지 저장 → CSV 저장

---

## 뉴스 감성 분석 초기 테스트

SHK 프로젝트로 정리하기 전에 단계별로 하나씩 확인한 코드.

| 순서 | 파일 | 확인한 것 |
|---|---|---|
| 1 | `news.py` | 네이버 뉴스 검색 결과에서 제목·링크 가져오기 |
| 2 | `chk.py`, `check_samsung.py` | 네이버 화면 구조가 바뀐 뒤 제목이 들어 있는 태그 찾기, 키워드별 제목 확인 |
| 3 | `huggingchk.py` | KR-FinBert 감성 모델이 뉴스 제목 하나를 판정하는지 |
| 4 | `setipipline.py` | 크롤링 + 감성분석을 이어 붙인 첫 파이프라인 |
| 5 | `news_filtered.py` | 관련 없는 기사를 거르는 제목 필터와 동의어 사전 |
| 6 | `start.py`, `collectall.py` | FastAPI 수집·조회 API와 일괄 수집 첫 버전 |
| - | `chkjson.py` | CSV의 link 열 위치 정리 |

여기서 확인한 내용을 공통 모듈(`collector.py`)로 모으고, 페이지 확장·차단 대비·DB 저장을 더해 SHK에서 완성했다.
과정은 [SHK/README.md](./SHK/README.md) 참고.

---

## 사용 기술

Python, requests, BeautifulSoup, pandas, Jupyter Notebook, Hugging Face transformers, FastAPI

---

## .gitignore

```
__pycache__/
.vscode/
*_debug.html
naver_page1.html
*.csv
classfile/레고이미지/
classfile/멜론앨범이미지/
SHK/news.db
SHK/news.db-wal
SHK/news.db-shm
SHK/backup/
SHK/price_cache/
SHK/collect_log.txt
SHK/validation_daily.csv
SHK/validation_chart.png
```

수집한 이미지와 데이터는 각 사이트와 언론사에 권리가 있어서 올리지 않는다.
