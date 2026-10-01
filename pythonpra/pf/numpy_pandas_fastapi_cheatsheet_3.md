# numpy / pandas / FastAPI 기초 정리

## 1. numpy

### 배열 생성
| 함수 | 설명 |
|---|---|
| `np.array([...])` | 리스트를 numpy 배열로 변환 |
| `np.zeros(shape)` | 지정한 shape만큼 0으로 채운 배열 생성 |
| `np.ones(shape)` | 지정한 shape만큼 1로 채운 배열 생성 |
| `np.full(shape, value)` | 지정한 shape만큼 원하는 값으로 채운 배열 생성 |
| `np.arange(n)` | 0부터 n-1까지 연속된 정수 배열 생성 |
| `np.random.rand(shape)` | 0~1 사이 랜덤값으로 채운 배열 생성 |
| `np.random.randn(shape)` | 평균 0, 표준편차 1인 정규분포 랜덤값 배열 생성 |

### 속성 (함수 아님, 괄호 없이 사용)
| 속성 | 설명 |
|---|---|
| `.shape` | 각 차원의 크기 (튜플) |
| `.dtype` | 원소의 자료형 |
| `.ndim` | 차원 수 |
| `.size` | 전체 원소 개수 |
| `.T` | 전치행렬 (행/열 반전) |

### 인덱싱 / 슬라이싱
| 표현 | 설명 |
|---|---|
| `mat[0]` | 0번째 행 전체 |
| `mat[0, 1]` | 0행 1열 원소 하나 |
| `mat[:, 0]` | 모든 행의 0번째 열 |
| `mat[1:, :2]` | 1행부터 끝까지, 열은 0~1번째 (2 미포함) |
| `arr[arr > 0.5]` | 조건을 만족하는 원소만 필터링 |

### 연산 / 형태 변경
| 함수·연산자 | 설명 |
|---|---|
| `+`, `-`, `*` | 브로드캐스팅 연산 (원소별 계산, shape 달라도 자동 확장) |
| `@` 또는 `np.dot(a, b)` | 행렬곱 (행×열 곱하고 더함, `*`와 다른 연산) |
| `.reshape(a, b)` | 배열 형태 재구성 (원소 개수는 유지되어야 함), `-1`은 자동 계산 |
| `np.concatenate([a, b])` | 배열을 이어붙임 (차원 안 늘어남) |
| `np.stack([a, b])` | 배열을 새 축으로 쌓음 (차원 하나 늘어남) |
| `arr[:, np.newaxis]` 또는 `np.expand_dims(arr, axis=)` | 차원 하나 추가 (모델 입력에 배치 차원 추가할 때 자주 씀) |
| `.squeeze()` | 크기 1인 차원 제거 |
| `np.vstack([a, b])` | 세로로 쌓기 (2차원 이상 배열 합칠 때 stack 대신 자주 씀) |

### 통계 / 기타
| 함수 | 설명 |
|---|---|
| `.mean(axis=)` | 평균, axis=0(열끼리)/axis=1(행끼리) |
| `.std(axis=)` | 표준편차 |
| `.sum(axis=)` | 합계 |
| `np.argmax(arr)` | 가장 큰 값의 인덱스 (분류 결과 뽑을 때 사용) |
| `np.argmin(arr)` | 가장 작은 값의 인덱스 |
| `np.where(조건, a, b)` | 조건에 따라 값 선택 |
| `np.save("file.npy", arr)` | 배열을 파일로 저장 |
| `np.load("file.npy")` | 저장된 배열 불러오기 |

### 응용
| 함수 | 설명 |
|---|---|
| `np.unique(arr)` | 중복 제거한 고유값 목록 (라벨 종류 확인할 때 유용) |
| `np.unique(arr, return_counts=True)` | 고유값 + 각각의 개수까지 함께 반환 |
| `np.clip(arr, min, max)` | 값의 범위를 강제로 제한 (이상치 자르기) |
| `np.percentile(arr, q)` | 백분위수 계산 (이상치 판단 기준 잡을 때) |
| `np.median(arr)` | 중앙값 |
| `np.cumsum(arr)` | 누적합 |
| `np.pad(arr, pad_width)` | 배열 앞뒤로 값 채워서 크기 맞추기 (시퀀스 길이 통일할 때 자주 씀) |
| `np.tile(arr, reps)` | 배열을 반복해서 이어붙임 |
| `np.repeat(arr, n)` | 각 원소를 n번씩 반복 |
| `(arr > a) & (arr < b)` | 여러 조건 동시 적용 (파이썬 `and`/`or` 대신 `&`/`|` 사용, 각 조건은 괄호로 감싸야 함) |
| `np.select([조건들], [값들])` | 여러 조건에 따라 다른 값 선택 (if-elif 여러 개를 벡터화) |
| `np.linalg.norm(arr)` | 벡터의 크기(길이) 계산 (거리 계산, 정규화에 사용) |
| `np.random.seed(n)` | 랜덤 시드 고정 (실험 재현성 확보, 매번 같은 랜덤값 나오게 함) |
| `np.apply_along_axis(func, axis, arr)` | 특정 축을 따라 커스텀 함수 적용 (for문 대체) |

---

## 2. pandas

### 자료구조 생성
| 함수 | 설명 |
|---|---|
| `pd.Series([...])` | 1차원 데이터 (인덱스가 붙은 리스트) |
| `pd.DataFrame({...})` | 2차원 데이터 (표) |

### 기본 정보 확인
| 메서드 | 설명 |
|---|---|
| `.head()` | 위에서 5개 행 미리보기 |
| `.shape` | (행 개수, 열 개수) |
| `.info()` | 열별 타입/결측치 요약 (유일하게 자체 출력함, print 불필요) |
| `.describe()` | 숫자 열들의 통계 요약 |
| `.columns` | 열 이름 목록 |
| `.dtypes` | 각 열의 자료형 |

### 선택 / 필터링
| 표현 | 설명 |
|---|---|
| `df["col"]` | 열 하나 선택 → Series 반환 |
| `df[["col1","col2"]]` | 열 여러 개 선택 → DataFrame 반환 |
| `df.loc[label]` | 인덱스 "이름" 기준 선택, 슬라이싱 시 끝값 포함 |
| `df.iloc[pos]` | 인덱스 "위치" 기준 선택, 슬라이싱 시 끝값 미포함 |
| `df.loc[조건, "col"]` | 조건 필터링 + 열 선택 결합 (실전에서 가장 많이 씀) |
| `df[df["col"] > n]` | 조건에 맞는 행만 필터링 |

### 결측치 처리
| 메서드 | 설명 |
|---|---|
| `.isna()` | 결측치 여부를 True/False로 반환 (결측치면 True) |
| `.notna()` | `.isna()`의 반대, 값이 있는 곳을 True로 반환 |
| `.isna().sum()` | 열별 결측치 개수 |
| `.notna().sum()` | 열별 값이 있는(결측치 아닌) 개수 |
| `.dropna()` | 결측치 있는 행 제거 (원본 유지, 새 DataFrame 반환) |
| `.dropna(subset=["col"])` | 특정 열에 결측치 있는 행만 제거 |
| `.fillna(value)` | 결측치를 지정한 값으로 채움 (0, 평균값 `.mean()` 등) |
| `.dropna(inplace=True)` / `.fillna(value, inplace=True)` | 원본 자체를 바로 수정 (재할당 없이). 단, 최근엔 `df = df.dropna()` 방식이 더 권장됨 |

### 그룹 / 통계
| 메서드 | 설명 |
|---|---|
| `df.groupby("col")` | 열 값 기준으로 그룹 나눔 |
| `df.groupby("col")["col2"].mean()` | 그룹별 평균 (그 외 sum/count/max/min 등 동일 패턴) |
| `.agg([...])` | 여러 통계를 한 번에 계산 |
| `df["col"].value_counts()` | 값별 개수 세기 (결과 이름 자동으로 "count") |
| `df.groupby("col").size()` | 그룹별 "행 개수" (결측치 상관없이 무조건 셈, count()와 다름) |
| `.rename("새이름")` | Series의 Name(이름표) 변경, 원본 안 바뀌고 새로 반환 |
| `series.name = "새이름"` | Series의 Name을 직접 대입해서 변경 (변수에 저장돼 있어야 가능) |
| `df.rename(columns={"기존":"새"})` | DataFrame의 "열 이름" 변경 (Series의 Name과는 다른 개념) |

### 병합
| 함수 | 설명 |
|---|---|
| `pd.concat([df1, df2], ignore_index=True)` | 위아래로 이어붙임, 인덱스 새로 정리 |
| `pd.merge(df1, df2, on="col", how=)` | 공통 열 기준으로 옆으로 합침. how: inner(기본)/left/right/outer |

### 파일 입출력
| 메서드 | 설명 |
|---|---|
| `df.to_csv("file.csv", index=False, encoding="utf-8-sig")` | CSV로 저장 (index=False로 불필요한 열 방지, utf-8-sig는 한글 엑셀 호환용) |
| `pd.read_csv("file.csv", encoding="utf-8-sig")` | CSV 불러오기 |
| `pd.read_csv("file.csv", nrows=5)` | 앞 N줄만 미리 읽기 (큰 파일 확인용) |
| `pd.read_csv("file.csv", usecols=["col1","col2"])` | 필요한 열만 선택해서 읽기 |
| `pd.read_csv("file.csv", dtype={"col":"str"})` | 읽을 때 열 타입 직접 지정 |

### 기타 참고
| 메서드 | 설명 |
|---|---|
| `df["col"].astype("string")` | pandas 전용 문자열 dtype으로 변환 (기본은 object/str) |
| `df["col"].str.split("구분자")` | 문자열 열을 구분자 기준으로 쪼갬 (groupby의 split과는 무관한 별개 기능) |

### 응용
| 메서드 | 설명 |
|---|---|
| `df.apply(func, axis=)` | 행 또는 열 단위로 커스텀 함수 적용 (for문 대체, axis=1이면 행 기준) |
| `df["col"].map(func)` | Series의 각 원소에 함수/딕셔너리 매핑 (라벨을 숫자로 변환할 때 자주 씀) |
| `df.groupby("col").transform(func)` | 그룹별로 계산하되, 원본과 같은 행 개수로 결과 반환 (그룹 평균으로 정규화할 때 유용) |
| `df.sort_values("col", ascending=)` | 특정 열 기준 정렬 |
| `df.sort_index()` | 인덱스 기준 정렬 |
| `df.duplicated()` | 중복된 행 여부 확인 |
| `df.drop_duplicates()` | 중복된 행 제거 |
| `df.pivot_table(index=, columns=, values=, aggfunc=)` | 엑셀 피벗테이블처럼 표 재구성 (라벨×조건별 통계표 만들 때) |
| `pd.melt(df, id_vars=)` | 넓은 표를 긴 표로 변환 (pivot_table의 반대 개념) |
| `pd.cut(series, bins)` | 연속값을 구간별로 나눠 범주화 (예: frame_count를 짧음/보통/김으로 분류) |
| `df.query("조건식")` | 문자열 조건식으로 필터링 (`df.loc[조건]`의 대안 문법) |
| `df.sample(n)` | 무작위로 n개 행 추출 (train/test 분할 전 확인용) |
| `pd.get_dummies(df["col"])` | 범주형 데이터를 원-핫 인코딩 |
| `pd.crosstab(df["col1"], df["col2"])` | 두 범주형 열의 교차표 (빈도수 집계) |
| `df["col"].shift(n)` | 값을 n칸 밀기 (시퀀스 데이터에서 이전/다음 프레임과 비교할 때) |
| `df["col"].diff()` | 이전 행과의 차이 (프레임 간 움직임량 계산에 활용 가능) |
| `df["col"].rolling(window).mean()` | 이동평균 (시퀀스 데이터 스무딩) |

---

## 3. FastAPI

### 기본 구조
| 코드 | 설명 |
|---|---|
| `app = FastAPI()` | 앱 객체 생성 |
| `@app.get("/path")` | GET 요청 처리 (데이터 조회) |
| `@app.post("/path")` | POST 요청 처리 (데이터 전송/생성) |
| `@app.put("/path")` | PUT 요청 처리 (데이터 수정) |
| `@app.delete("/path")` | DELETE 요청 처리 (데이터 삭제) |

### 파라미터
| 패턴 | 설명 |
|---|---|
| `def f(id: int)` + `@app.get("/items/{id}")` | Path parameter (URL 경로에 포함) |
| `def f(keyword: str = "")` | Query parameter (`?keyword=값` 형태) |
| `class Req(BaseModel): ...` + `def f(req: Req)` | Request body (JSON, POST에서 주로 사용) |

### 응답 / 에러
| 코드 | 설명 |
|---|---|
| `return {...}` | 딕셔너리 반환 시 자동으로 JSON 응답 |
| `HTTPException(status_code=, detail=)` | 에러 응답을 명시적으로 발생시킴 |
| `@app.get(..., response_model=Model)` | 응답 데이터 형식을 강제/문서화 |

### 실행 / 확인
| 명령어·경로 | 설명 |
|---|---|
| `uvicorn main:app --reload` | 서버 실행 (파일명:앱객체, 코드 변경 시 자동 재시작) |
| `http://127.0.0.1:8000/docs` | 자동 생성된 Swagger UI (테스트용) |

### 기타 (참고용)
| 개념 | 설명 |
|---|---|
| `async def` | 비동기 처리 필요할 때 (DB, 외부 API 호출 등) |
| `CORSMiddleware` | 프론트엔드에서 요청 시 브라우저 차단 방지 설정 |

### 응용
| 코드/개념 | 설명 |
|---|---|
| `Depends(func)` | 의존성 주입. 인증 확인, DB 연결 등 여러 엔드포인트에서 반복되는 로직을 함수로 분리 |
| `@app.post("/upload")` + `file: UploadFile = File(...)` | 파일 업로드 처리 (이미지/영상 받을 때) |
| `BackgroundTasks` | 응답은 먼저 보내고, 오래 걸리는 작업(로그 기록 등)은 백그라운드로 처리 |
| `APIRouter()` | 엔드포인트를 파일별로 나눠서 관리 (프로젝트 커질 때) |
| `@app.exception_handler(예외타입)` | 특정 에러 타입에 대해 커스텀 에러 응답 정의 |
| `@app.on_event("startup")` / `"shutdown"` | 서버 시작/종료 시 한 번 실행할 로직 (모델 로드 등에 사용) |
| `@app.websocket("/ws")` | 실시간 양방향 통신 (실시간 스트리밍 데이터 처리 시) |
| `OAuth2PasswordBearer` | 토큰 기반 인증 처리의 기본 틀 |
| `StaticFiles` | 정적 파일(이미지, HTML 등) 서빙 |
| `TestClient` (from `fastapi.testclient`) | 서버 켜지 않고 코드로 API 테스트 자동화 |
| `Header()`, `Cookie()` | 요청 헤더/쿠키 값을 파라미터로 받기 |
