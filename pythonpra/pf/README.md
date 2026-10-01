# numpy · pandas · FastAPI 기초 학습

수어 인식 프로젝트(SignBridge)에 들어가기 전에 기초를 다진 폴더. 2026-07-28 ~ 07-31.
예제 데이터도 손 관절 좌표, 수어 자음 라벨(ㄱ·ㄴ·ㄷ…)처럼 프로젝트에서 쓸 형태로 만들었다.

---

## 학습 순서

| 순서 | 파일 | 해본 것 |
|---|---|---|
| 1 | `numpy1.py` | 배열 생성·속성(shape, ndim), 인덱싱·슬라이싱, 브로드캐스팅(손목 기준 상대좌표), reshape, axis별 평균, concatenate·stack, 조건 필터링, argmax, 차원 추가·제거, 행렬곱 |
| 2 | `minimodel.py` | numpy만으로 신경망 층 만들기 — `x @ W + b`(= `nn.Linear`), ReLU, 배치 입력, 2층 순전파, argmax로 예측 |
| 3 | `pandas1.py` | Series·DataFrame, 기본 정보 확인(info, describe), 열·행 선택, 결측치 처리, groupby, concat, merge, CSV 저장·불러오기 |
| 3-1 | `loc_iloc.py` | `loc`(이름 기준)와 `iloc`(위치 기준) 차이 — 인덱스를 10, 20, 30…으로 바꿔서 확인 |
| 4 | `main.py` | FastAPI — GET·POST·PUT·DELETE, 경로·쿼리 파라미터, Pydantic 요청 본문(손 좌표 받는 `/predict`), HTTPException, response_model |
| 5 | `numpy_pandas_fastapi_cheatsheet_3.md` | 세 가지를 표로 정리 + 다음에 볼 응용 함수 목록 |

`signbridge_meta.csv`는 `pandas1.py`가 CSV 저장 연습으로 만든 파일이다.

---

## 다시 돌려볼 때

```bash
python numpy1.py
uvicorn main:app --reload
```

FastAPI는 실행 후 http://127.0.0.1:8000/docs 에서 바로 테스트할 수 있다.

- `pandas1.py` 마지막 세 줄은 `read_csv` 옵션 예시라서 `파일.csv`가 없다는 오류로 끝난다
- `main.py`에 `GET /items/{item_id}`가 두 번 정의돼 있어 먼저 나온 쪽만 동작한다
  (아래쪽 response_model 예시는 호출되지 않는다)
