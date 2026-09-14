# 한국어 영화 리뷰 평점 예측

리뷰 글로 작성자가 준 실제 평점(0.5~5.0)을 예측하는 교육용 프로젝트입니다.
TF-IDF + Ridge부터 이해하고 이후 LSTM과 비교하는 것이 목표입니다.

## 데이터 준비
출처: https://www.kaggle.com/datasets/suminwang/korean-movie-review-data-30kbert
폴더명은 NSMC지만 표준 NSMC 이진 감성 데이터가 아닙니다.
원본을 다운로드하거나 기존 PC에서 복사해 이 폴더에 `Koreanmovie_review.csv`로 둡니다.
CSV는 저장소에 포함하지 않습니다. 데이터 재배포 조건은 별도로 확인해야 합니다.
`bert_label`, `neg_score`, `pos_score`는 기존 모델 예측이므로 정답으로 사용하지 않습니다.

## 새 PC에서 실행 (Windows PowerShell)
```powershell
git clone https://github.com/JungUH-0/JungPra.git
cd JungPra/pythonpra/NSMC
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe datachk.py
.\.venv\Scripts\python.exe split_data.py
.\.venv\Scripts\python.exe train_model.py
```
`datachk.py`는 현재 폴더 기준으로 CSV를 읽으므로 반드시 위 폴더에서 실행하세요.
기존 실행은 Python 3.14에서 이루어졌습니다. 패키지 버전은 아직 고정하지 않았으므로 환경에 따라 결과가 달라질 수 있습니다.

## 실행 흐름
1. `datachk.py`: 리뷰/평점 결측, 빈 리뷰와 완전 중복을 제거하고 clean/ready CSV를 저장합니다.
2. `split_data.py`: 같은 리뷰 문구가 양쪽에 들어가지 않도록 분리해 train/test CSV를 저장합니다.
3. `train_model.py`: 학습용에만 TF-IDF를 fit하고 Ridge를 학습해 predictions CSV를 저장합니다.
재실행하면 해당 출력 CSV를 덮어씁니다. 입력 원본은 수정하지 않습니다.

## 확인된 결과
- ready 26,321행, train 21,052행, test 5,269행, 양쪽 리뷰 교집합 0.
- 학습 행렬 (21052, 50000), 평가 행렬 (5269, 50000).
- 사용자 실행 결과: 평균 평점 기준 MAE 0.8913점, Ridge MAE 0.7464점.
- MAE는 평균 절대 오차이며 정확도 퍼센트가 아닙니다.
- 모델 설정: 문자 1~3그램, min_df=3, max_features=50000, sublinear_tf=True, Ridge alpha=10, solver=lsqr.
- predictions CSV: review, rating, predicted_rating, absolute_error.

## 평가의 한계
영화 단위 분리가 아니므로 새로운 영화에 대한 일반화 평가로 해석하지 않습니다.
플랫폼별 평점 척도 통일 여부는 미검증입니다.
튜닝은 기존 학습용 내부에서 리뷰 문구 기준으로 나눈 검증용 데이터로 진행합니다.
평가용은 설정을 선택하는 데 반복 사용하지 않습니다.

학습 진행 상황과 새 대화 시작 요청은 `HANDOFF.md`를 참고하세요.
