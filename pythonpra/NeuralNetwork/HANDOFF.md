# Food-11 이미지 분류 — 프로젝트 인수인계 문서

새 세션/새 PC에서 이어받을 때 이 파일부터 읽으면 됩니다.
결과 표는 아티팩트에, **결정의 이유와 주의사항은 여기에** 정리돼 있습니다.

- 아티팩트(결과 전체): https://claude.ai/code/artifact/152cfb3a-8394-46b6-9587-843a299ab858
  (Claude Code에서만 읽힘. 일반 채팅에서는 브라우저로 열어 복사해야 함)
- 데이터셋: https://www.kaggle.com/datasets/trolukovich/food11-image-dataset

---

## 1. 무엇을 하는 프로젝트인가

Food-11(음식 사진 11개 클래스, 16,643장)로 **하이퍼파라미터가 성능에 어떤 영향을 주는지**
Keras와 PyTorch 양쪽에서 비교하는 실험. 학부 발표용.

**발표 논지**: "하이퍼파라미터에 정답은 없다 — 구조가 바뀌면 최적값도 바뀐다"

의도적으로 **"이미지엔 CNN이 좋다"를 결론으로 삼지 않았다.** 교과서적 사실이라
발표 논지로 세우면 아는 답을 확인하는 꼴이 되기 때문. CNN은 "이후 실험의 무대"로만 쓴다.

---

## 2. 현재 상태 (2026-09-09 기준)

- 실험 조합 **30개** 완료 (전체 실험 기록 표의 행 수 그대로)
- 그중 **6개 조건은 재현 실행(2회차)까지 완료** — 총 36회 학습
- 최고 기록 **61.9%** (PyTorch · 3Conv+BN · AdamW + ReduceLR)
- 발표 자료 PPT **18장** 완성, 학습 곡선 **7칸 삽입** (7·9·12번 슬라이드)
- 파일명이 `food11_정의형.pptx`로 바뀌었다. `build.js`와 **완전 동기화 상태**이므로
  재빌드해도 아무것도 사라지지 않는다 (`ppt_build/food11_presentation.pptx`를 복사하면 됨)
- 재현 실행 표 슬라이드는 **삭제했다** — 표 전체는 아티팩트에만 있다.
  대신 14번(전체 요약)이 핵심 수치(59.2·61.9, test 편차 최대 4.6%p)를 떠안고,
  13번 ⑤단계와 15번 한계 ③이 재현 결과를 반영한 문장으로 바뀌어 있다
- 곡선 라벨 오류(keras4·keras6·torch4·torch5의 제목이 "SGD") **수정 완료** —
  PNG 제목을 다시 그려 넣었고 원본은 `curves/orig/`에 있다
- **남은 것**
  - `curve_keras3.png` · `curve_keras6.png` · `curve_torch3.png` · `curve_torch5.png` 는
    슬라이드에 안 붙었다. 넣으려면 슬라이드를 새로 만들어야 해서 보류 중
  - torch5는 1회 실행뿐이라 2회차를 돌리면 "구조가 커지면 옵티마이저 차이가 사라진다"를
    범위 비교로 확정할 수 있다 (지금은 편차 범위 안이라 단정 불가)

### PPT 구성 (18장)

```
 1 표지                        11 EarlyStopping이 놓친 지점
 2 데이터셋 — Food-11          12 학습 곡선 — 두 프레임워크
 3 실험 설계                   13 CNN 개선 경로
 4 출발점 — ANN과 DNN          14 전체 요약
 5 기준 모델 선정 — CNN        15 실험의 한계 (4개)
 6 옵티마이저 비교             16 61.9%에서 멈춘 이유
 7 학습 곡선 — 옵티마이저      17 추가 하이퍼파라미터 실험
 8 과적합과 대응               18 결론
 9 학습 곡선 — 과적합 대응 전후
10 구조 및 학습 안정화
```

**8·9는 과적합 묶음, 10~12는 구조 개선과 그 부작용·분석.**
10(구조)이 11(EarlyStopping 함정)보다 앞에 와야 한다 — 11이 BatchNorm을 근거로 들기 때문.
12(프레임워크)가 13(Keras/PyTorch 열 표) 바로 앞에 있어야 표를 읽는 법이 깔린다.
이 순서를 바꾸려면 `build.js`에서 세 블록(`9. ARCHITECTURE` / `9-2. EARLYSTOP` / `9-3. FRAMEWORK`)
위치만 옮기면 된다.

3번 하단에 **프레임워크 불일치 예고 한 줄**을 넣어뒀다. 뒤에서 Keras·PyTorch를 계속
나란히 비교하는데 두 모델의 분류 헤드가 애초에 달랐다는 사실을 미리 밝혀두는 장치다.
빼면 6번에서 "두 모델 구조는 같나요"라는 질문에 답을 뒤로 미뤄야 한다.

15·16·17번 하단 요약 줄은 **의도적으로 지웠다.** 내용은 발표자 노트에 있으니 말로 하면 된다.

---

## 3. 파일 목록

```
colab_final/          ← 실제로 돌리는 코드 (Colab 붙여넣기용)
  keras1.py    2 Conv · Adam · 15 epoch · 증강 없음
  keras2.py    3 Conv+BN+He · Adam · 증강 · EarlyStop p=3
  keras3.py    3 Conv+BN+He · AdamW+ReduceLR · EarlyStop p=7
  keras4.py    keras1과 옵티마이저만 다름 (SGD+momentum) — 실행 완료
  torch1.py    2 Conv · SGD+momentum · 15 epoch · 증강 없음
  torch2.py    3 Conv+BN · Adam · 증강 · EarlyStop p=5
  torch3.py    3 Conv+BN · AdamW+ReduceLR · EarlyStop p=7
  hyperparameters.txt   6개 파일 조건 비교표 + 프레임워크 간 불일치 정리
  ※ keras6은 파일이 없다. keras3에서 옵티마이저만 SGD+momentum 0.9(wd=1e-4)로
     바꿔 30 epoch 돌린 것이라 별도 스크립트를 만들지 않았다.

food11_정의형.pptx          발표 자료 (18장) — ppt_build 빌드 결과물의 복사본

curves/               학습 곡선 PNG 10장 (.gitignore 대상 — 커밋되지 않는다)
  orig/               라벨 수정 전 원본 4장

ppt_build/            ← PPT·아티팩트를 수정하려면 여기부터
  build.js                  PPT 생성 스크립트 (이걸 고쳐서 재빌드)
  strip_link_underline.py   빌드 후처리
  artifact_source.html      아티팩트 HTML 원본
  README.md                 빌드 방법과 주의사항

batchnorm_earlystopping.txt   BatchNorm↔EarlyStopping 충돌 정리
learning_rate.txt             학습률과 1e-2 표기, 프레임워크 기본값 차이

keras/, pytorch/      초기 MNIST 실습 (참고용, 현재 실험과 무관)
colab_food11/         Food-11 초기 버전 (colab_final로 대체됨)
```

---

## 4. 실험 결과 요약

### 구조별 최고 (5 epoch 기준)
| 구조 | 최고 | 조건 |
|---|---|---|
| ANN | 21.3% | Keras · SGD |
| DNN | 26.9% | PyTorch · Adam |
| CNN | 44.1% | PyTorch · Adam |

### CNN 개선 경로
| 단계 | Keras | PyTorch |
|---|---|---|
| 기본 (5 epoch) | 43.6% | 44.1% |
| epoch 15 | 45.4% | 44.0%(SGD+mom) / 44.4%(Adam) |
| + 증강 + EarlyStop | 50.9% | 50.9% |
| + 3Conv·BatchNorm·He | 56.1% | 54.5% |
| + AdamW + ReduceLR | 52.1% | **59.2%** |

### 옵티마이저 A/B — 2×2 완성 (2 Conv · 15 epoch · 증강 없음 · lr=1e-3)
| 조건 | Train | Val | Test | Test loss |
|---|---|---|---|---|
| Keras · Adam | 93.6% | 42.7% | 46.4% | 3.08 |
| Keras · SGD+mom | 68.7% | 41.2% | 43.1% | 1.80 |
| PyTorch · Adam | 99.4% | 39.4% | 44.4% | 4.81 |
| PyTorch · SGD+mom | 57.0% | 39.9% | 43.0% | 1.66 |

- Test 폭 **3.4%p** (43.0~46.4) — 측정 편차 6.1%p 안, 사실상 동률
- Train 폭 **42.4%p** (57.0~99.4)
- Test loss **2.9배** (1.66~4.81)

**Adam이 사준 것은 도달점이 아니라 속도였다.** 정확도로는 승부가 안 나는데
loss는 두 프레임워크 모두 SGD+momentum이 확실히 낮다 — 편차로 설명 안 되는 크기.

### keras6 (최종 튜닝 구성에서 옵티마이저만 SGD+momentum)
30 epoch 완주, Train 54.0% · Val 46.5% · **Test 47.4%** · loss 1.64.
keras3(AdamW 평균 54.4%)보다 낮지만 부수 설정이 완전히 같지는 않아
깨끗한 A/B는 아니다. 과적합은 확실히 덜하다(Train−Test 격차 6.6%p).

### torch5 — 30번째 조합 (3 Conv+BN · SGD+mom · 증강 · ES p=5)
13 epoch에서 정지. Train 89.7% · Val 55.2% · **Test 56.1%** · loss 1.35.

같은 조건 Adam(torch2)은 54.5% · 52.6%(평균 53.6%)라 **단일 SGD 실행이 Adam 두 실행을
모두 넘었다.** 다만 1회뿐이고 최고 Adam 실행과의 차이 1.6%p는 편차(4.6%p) 안이라
"SGD가 이겼다"가 아니라 **"구조가 커지니 차이가 사라졌다"**까지만 말해야 한다.

2 Conv 때와 방향이 반대인 것도 기록해둔다 — 거기선 Adam이 train 99.4%까지 외웠는데
여기선 SGD 쪽 train이 89.7%로 Adam(73.4%)보다 높다. 13번 슬라이드 하단 각주에 넣었다.

### 재현 실행 (같은 조건 2회차)
| 스크립트 | 1차 → 2차 | 편차 |
|---|---|---|
| keras1 | 45.4 → 46.4 | 1.0%p |
| keras2 | 56.1 → 52.5 | 3.6%p |
| keras3 | 52.1 → 56.7 | **4.6%p** |
| torch2 | 54.5 → 52.6 | 1.9%p |
| torch3 | 59.2 → **61.9** | 2.7%p |
| torch4 | 44.0 → 43.0 | 1.0%p |

*(표의 편차는 test 정확도 기준. 검증 정확도는 torch2에서 6.1%p까지 움직였다.)*

**Test 정확도 편차 최대 4.6%p**(keras3). 이 수치가 이 프로젝트에서 가장 중요한 숫자이고,
발표에서 "차이가 있다"고 말할 수 있는 기준선이다.

⚠️ 예전에 쓰던 **6.1%p는 Val 편차**(torch2)다. 발표에서 비교하는 숫자는 전부 test 정확도이므로
기준선으로 인용할 값은 **4.6%p**. PPT·아티팩트 모두 test 기준으로 통일해 뒀다.

---

## 5. 최종 결론 3가지 (발표용)

1. **최적 옵티마이저는 모델에 따라 뒤집힌다**
   ANN에서 SGD 21.3% vs Adam 12.9%, CNN에서 Adam 44.1% vs SGD 20.5%.
   momentum 0.9만 더해도 +12%p. "일단 Adam"은 성립하지 않았다.

2. **정규화는 더하기가 아니라 총량의 문제**
   2회씩 평균: PyTorch Adam 53.6% → AdamW **60.6%** (+7.0%p, 범위 겹침 없음)
   / Keras Adam 54.3% → AdamW 54.4% (차이 없음).
   PyTorch에는 Dropout이 없어 weight decay가 빈 자리를 채웠고, Keras에는 이미 있었다.

3. **차이가 났다면 조건이 달랐던 것이다**
   조건을 맞춘 구간에서 두 프레임워크가 50.9%로 일치. 19.6%p까지 벌어졌던 구간은
   BatchNorm/ReLU 순서 실수였고 바로잡자 1.6%p로 좁혀졌다.

> **주의**: 결론 ②는 원래 "Keras에서는 AdamW가 4%p 해로웠다"까지 포함했으나,
> 재현 실행에서 그 부분이 **실행 편차로 밝혀져 삭제**했다. 지금 형태가 확정본이다.

---

## 6. 발견한 함정 (자세한 내용은 각 txt 파일)

### BatchNorm ↔ EarlyStopping 충돌
BatchNorm은 eval 모드에서 누적 통계(running stats)를 쓰는데, 초반 몇 epoch은
이 값이 안 여물어서 val 지표가 실제보다 나쁘게/불안정하게 나온다.
patience가 짧으면 여기서 성급하게 멈춘다. PyTorch 3Conv 첫 시도가
patience=3으로 8 epoch만에 멈춰 36.5%가 나왔고, patience=5로 늘리니 54.5%.
→ `batchnorm_earlystopping.txt`

### val_loss로 최적점을 고르면 손해볼 수 있다
torch2 재현에서 epoch 5(val_loss 1.494, val_acc 51.2%)가 선택됐는데
epoch 8은 val_loss 1.500으로 0.006 밀렸지만 val_acc는 54.7%였다.
**loss 0.006 차이로 정확도 3.5%p를 잃었다.**

### 프레임워크 기본값이 서로 다른 것들
| | Keras | PyTorch |
|---|---|---|
| 가중치 초기화 | Glorot (ReLU엔 `he_normal` 명시 필요) | Kaiming(He) — 기본값이 이미 적합 |
| SGD 기본 학습률 | 0.01 | 없음 (필수 지정) |
| BatchNorm momentum | 0.99 = 배치당 1% 갱신 | 0.1 = 배치당 10% 갱신 (**의미가 반대**) |
| 분류 손실 | 모델에 softmax + `from_logits=False` | 모델은 logit, `CrossEntropyLoss`가 처리 |

### Colab에서 Drive 직접 읽으면 학습이 수십 배 느려진다
반드시 로컬로 복사 후 사용:
```
!cp -r /content/drive/MyDrive/food11 /content/food11
```
`DATA_DIR = "/content/food11"` 로 지정. 런타임이 끊기면 다시 복사해야 함.

---

## 7. 절대 "고치지" 말 것 — 의도적으로 남겨둔 불일치

새 세션이 코드를 보면 고치고 싶어질 만한 것들인데, **고치면 기록된 실험 결과와
어긋나므로 그대로 둬야 한다.** 발표에서는 "실험의 한계"로 밝히는 것이 맞다.

| 항목 | Keras | PyTorch |
|---|---|---|
| Dropout | 0.5 있음 | **없음** |
| 분류 헤드 | Flatten→Dropout→Dense(11) | Flatten→**Linear(128)→ReLU**→Linear(11) |
| 증강 종류 | Flip + Rotation + **Zoom** | Flip + Rotation |
| 회전 강도 | `0.1` = **±36°** | `10` = **±10°** |
| EarlyStop patience | keras2=3 | torch2=5 |

특히 **Dropout 불일치는 결론 ②의 근거**다. 이걸 "통일"하면 결론이 사라진다.

또한 **학습률 1e-3 고정**은 Adam엔 기본값이지만 SGD엔 평소의 1/10이라
SGD에 불리했을 수 있다. 다만 momentum 0.9가 정상상태 유효 보폭을 약 10배로 키워
lr=1e-2를 근사하고, 그 조건에서 SGD는 43.0~43.1%로 Adam과 동률이었다 — 발표에서는
그냥 인정하지 말고 이 반박 근거까지 같이 말할 것.

### 한계 슬라이드는 4개로 재정리했다 (2026-09-09)
결론별로 "무엇을 흔드는가" 기준으로 골랐다.

| # | 한계 | 흔드는 결론 |
|---|---|---|
| 1 | 두 CNN이 같은 모델이 아니었다 — **파라미터 653K 대 7.39M (11.3배)** | ② ③ |
| 2 | 한 단계에서 변수를 여러 개 바꿈 (④⑤단계 각 3개) | ② |
| 3 | 61.9%는 35번 측정 중 최댓값 (2회 평균은 60.6%) | 최고 기록 |
| 4 | SGD에 불리했을 수 있는 lr (단, momentum이 상쇄) | ① |

**뺀 것**: 단일 실행(14번이 이미 답), 배치 크기 미탐색(어떤 결론도 안 흔듦).

**"test 정보가 새어 들어갔다"는 표현은 폐기했다.** 코드를 확인하니 분할 위생은 7개 스크립트
전부 깨끗하다 — 학습은 `training`, EarlyStopping·ReduceLR은 `validation`(`monitor="val_loss"`),
`evaluation`은 실행 끝에 한 번뿐. PyTorch 쪽 함수 이름이 `test()`라 헷갈리지만
학습 루프에 들어가는 건 `val_dataloader`다. 실제 문제는 누수가 아니라
**35번 측정의 최댓값을 헤드라인으로 쓴 선택 편향**이고, 지금 슬라이드는 그렇게 적혀 있다.

---

## 8. 다음에 할 일

1. **torch5 2회차** — 이것만 있으면 "구조가 커지면 옵티마이저 차이가 사라진다"를
   범위 비교로 확정할 수 있다. 지금은 1회뿐이라 편차 범위 안이다
2. Colab에서 다시 그릴 일이 있으면 `OPTIMIZER_NAME = "SGD + momentum 0.9"` 로 고쳐서 실행할 것 —
   안 고치면 같은 라벨 오류가 재발한다
3. torch1을 Adam/SGD 각각 2회차로 돌리면 재현 데이터가 더 쌓인다
4. 결과 나올 때마다 아티팩트에 행 추가 → PPT의 조합 수(현재 30)도 같이 갱신
5. PPT는 로컬에서 열어 넘침·겹침만 눈으로 확인 (이 PC엔 LibreOffice가 없어 자동 검사 불가)

### PPT를 고칠 때 지켜야 할 것
`build.js`를 고쳐 재빌드하고 `food11_정의형.pptx`로 복사하는 것이 정해진 경로다.
**pptx를 PowerPoint에서 직접 고치면 다음 재빌드 때 사라진다.** 부득이 직접 고쳤다면
두 파일을 문단 단위로 diff 해서 `build.js`에 먼저 이식할 것 — 실제로 두 번 그렇게 복구했다.

### 그래프 코드 사용법
각 스크립트 하단에 학습 곡선 저장 코드가 붙어 있다. 옵티마이저를 바꿔 돌릴 때는
**라벨도 반드시 같이 수정**할 것 (안 그러면 그래프에 잘못된 이름이 찍힘):
```python
OPTIMIZER_NAME = "SGD + momentum 0.9"
OUTFILE = "curve_keras4.png"
```

---

## 9. 환경

- Colab (GPU T4). 무료 할당량 소진되면 몇 시간 대기 필요
- 로컬에는 conda 환경 `nnetwork` (Python 3.12 + TensorFlow + PyTorch)
  — 다만 실제 실험은 전부 Colab에서 진행했다
- 로컬 시스템 Python은 3.14라 TensorFlow 미지원
