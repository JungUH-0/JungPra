# Food-11 하이퍼파라미터 실험

Food-11(음식 사진 11개 클래스, 16,643장)로 **하이퍼파라미터를 바꿨을 때 성능이 어떻게 달라지는지**
측정하는 실험. 학부 발표용.

Keras와 PyTorch 양쪽에서 같은 실험을 한다. 다만 **두 프레임워크 비교가 목적은 아니다** —
튜닝 효과는 프레임워크 안에서 재고, 양쪽 결과가 같은 방향이면 근거가 강해지는 구조다.

- 데이터셋: https://www.kaggle.com/datasets/trolukovich/food11-image-dataset
- 결과 전체(아티팩트): https://claude.ai/code/artifact/152cfb3a-8394-46b6-9587-843a299ab858

> 학습은 전부 **Colab**에서 했다. 이 폴더에는 Colab에 붙여넣는 스크립트와 기록 문서만 있고,
> 데이터셋·학습 곡선 PNG·pptx는 git에 올라가지 않는다 (`.gitignore`).

---

## 진행 단계

| 단계 | 상태 | 요약 |
|---|---|---|
| v1 | 완료 | 30개 조합 · 36회 학습 · 최고 61.9% · 발표 PPT 18장 |
| v2 | **0·1단계·시드 반복 완료, 기준선은 He로 확정.** 2단계(학습률) 시드 0 훑기 완료, 3시드 확인 노트북 작성·실행 전 (2026-10-29 기준) | v1의 설계 문제점을 막고 다시 실험 |

---

## v2로 다시 시작하는 이유

**v1 결과로는 "이 하이퍼파라미터를 바꿨더니 이런 효과가 났다"고 말할 수 없었다.**
정확도가 낮아서가 아니다. 숫자가 달라졌을 때 그 원인을 하나로 가려낼 수 없게 설계돼 있었다.

문제점은 입력 순서에서 시작됐다. 이미지가 들어가는 순서가 실행마다 달랐는데, 그게 결과에 영향을
주지 않았다고 말할 근거가 없었다. 이는 "그럼 다른 조건들은 정말 통제됐나"로 이어졌고, 결국
**설계 전체**의 문제점으로 번졌다. 코드와 기록을 다시 확인해 보니 실제로 그랬다.

v1을 부분적으로 고쳐 다시 돌리는 것으로는 해결되지 않는다. 문제가 개별 실행이 아니라
**조건을 쌓아 온 방식** 자체에 있기 때문이다. 그래서 가장 기초 모델(2 Conv, 분류 헤드만 통일)에서
출발해 한 번에 하나씩 다시 쌓는다. v1 코드(`colab_final/`)는 기록된 결과와 맞물려 있으므로
그대로 두고, v2는 `colab_v2/`에서 새로 한다.

### v1에서 무너진 지점

| # | 문제 | 확인된 사실 | v2에서 막는 방법 |
|---|---|---|---|
| 1 | 우연을 통제하지 않았다 | 시드 미고정, 대부분 1회 실행. 같은 설정을 다시 돌리면 test가 최대 **4.6%p** 달라졌다 — 이보다 작은 차이는 효과인지 우연인지 알 수 없다 | 시드 고정 + 시드 0·1·2 반복으로 흔들림 폭부터 잰다 |
| 2 | 한 번에 여러 개를 바꿨다 | "3 Conv + BatchNorm + He", "AdamW + ReduceLR + patience"처럼 한 단계에서 3개씩 같이 바꿈 → 어느 것의 효과인지 분리 불가 | 기준선에서 한 번에 하나만 바꾼다 |
| 3 | 두 프레임워크가 같은 모델이 아니었다 | 파라미터 653,003 대 7,393,739 (**11.3배**) — PyTorch에만 은닉층, Keras에만 Dropout | 같은 구조로 맞추고 파라미터 수부터 확인 (`basic_unified.py`: 둘 다 653,003) |
| 4 | 학습률을 통제 변수로 썼다 | 전 구간 1e-3 고정 — Adam에겐 기본값이지만 SGD에겐 평소의 1/10 | 옵티마이저마다 맞는 학습률을 직접 찾는다 (`colab_v2/README.md` Phase 1) |
| 5 | 최고 기록에 선택 편향 | 61.9%는 v1 전체 측정 중 최댓값. 같은 조건 2회 평균은 60.6% | 고르는 건 val, test는 보고용 |
| 6 | 두 프레임워크 사이 설정·기본값이 어긋났다 | 증강 회전 ±36° 대 ±10° (단위 차이), EarlyStop patience 3 대 5. PyTorch 기본 초기화를 He라고 잘못 설명했다 (실제로는 2.45배 작다) | 직접 정하는 값은 양쪽을 같게. 기본값 차이는 목록으로 관리하다가 두 프레임워크 결과가 다를 때 하나씩 맞춘다 |

### 문제점과 대응

| 문제점 | 성격 | 대응 |
|---|---|---|
| 이미지 입력 순서가 실행마다 달랐다 → 다른 조건도 통제됐다고 할 수 없다 | 설계 | 위 1·2 |
| 학습률 0.001 통일의 근거가 약하다 (SGD는 기본값이 다른데 momentum으로 메웠다) | 설계 | 위 4 |
| "프레임워크 차이가 적다"는 결론의 전제조건이 성립하지 않았다 | 설계 | 위 3·6. v2는 이 결론을 내지 않는다 — 목적은 튜닝 효과 |
| 쓴 함수의 내부 동작(EarlyStopping, 스케줄러)을 설명하지 못했다 | 이해 | `builtin_functions.md` 6번 |
| 128×128인데 첫 층 출력이 126×126인 이유를 설명하지 못했다 | 이해 | `builtin_functions.md` 3번 (패딩 없음) |
| Conv2D를 쓴 이유, DNN을 2층만 쌓은 이유를 설명하지 못했다 | 이해 | 아직 문서로 정리 안 됨 |

위의 세 개가 다시 실험하는 이유이고, 아래 세 개는 실험이 아니라 설명을 보강할 부분이다.
v2 설계의 세부(원칙·Phase·기록 항목)는 `colab_v2/README.md`.

---

## 어디부터 읽을까

| 하려는 일 | 읽을 문서 |
|---|---|
| 전체 맥락·결정 이유·다음 할 일 | `HANDOFF.md` |
| 튜닝 전 전제조건과 진행 상태 | `HANDOFF.md` 10번 |
| v2 실험 설계 (Phase 1~4) | `colab_v2/README.md` |
| v1 스크립트별 설정 비교 | `colab_final/hyperparameters.txt` |
| 발표 자료·아티팩트 수정 | `ppt_build/README.md` |
| 쓴 함수의 기본값·주의점 | `builtin_functions.md` |

---

## 폴더 구조

```
NeuralNetwork/
  HANDOFF.md                   인수인계 문서 — 새로 이어받을 때 이것부터
  builtin_functions.md         Keras·PyTorch 내장 함수 기본값 정리
  batchnorm_earlystopping.txt  BatchNorm ↔ EarlyStopping 충돌 정리
  learning_rate.txt            학습률 표기와 프레임워크 기본값 차이
  requirements.txt

  colab_v2/          ← v2 (지금 단계)
    basic_unified.py   기준선 — 분류 헤드만 통일한 2 Conv. 가장 먼저 돌릴 코드
    basic_unified.ipynb  위 코드의 Colab 노트북 사본 (원본은 .py)
    step1_he_init.ipynb  1단계 — He 초기화 하나만 변경, 설명 포함 (0단계 결과와 비교)
    seed_repeat.ipynb    시드 반복 — 0·1단계 × 두 프레임워크 × 시드 0·1·2 (12번)
    step2_learning_rate.ipynb  2단계 — 옵티마이저 3개 × 학습률 4개(1e-4~1e-1), 시드 0, 두 프레임워크 24번
    step2_lr_seeds.ipynb       2단계 마무리 — 후보 4개 × 시드 1·2 (시드 0은 위 결과 재사용), 학습률 결론과 옵티마이저 비교 16번
    common.py          설정·시드·데이터·모델·학습·기록 하네스
    phases.py          Phase 1~4 조건 목록과 실행 루프
    README.md          v2 설계 문서

  colab_final/       ← v1 실험 코드 (결과와 맞물려 있어 수정 금지)
    keras1~4.py, torch1~3.py
    hyperparameters.txt

  ppt_build/         발표 PPT·아티팩트 소스 (build.js가 원본)
  curves/            v1 학습 곡선 PNG (git 제외) · orig/ = 라벨 수정 전 원본
  food11_정의형.pptx  발표 자료 — ppt_build 빌드 결과물의 복사본 (git 제외)
  ppt_build.zip      09-06 시점 ppt_build 백업 (git 제외)

  colab_food11/      Food-11 초기 버전 (colab_final로 대체됨)
  keras/, pytorch/   초기 MNIST 실습 (참고용, 현재 실험과 무관)
  data/              MNIST 자동 다운로드 (git 제외)
```

---

## 실행 방법 (Colab)

1. Kaggle에서 데이터셋을 받아 Google Drive `MyDrive/food11`에 올린다
2. Colab에서 Drive를 마운트하고 **로컬로 복사**한다 — Drive에서 직접 읽으면 학습이 수십 배 느려진다

   ```python
   !cp -r /content/drive/MyDrive/food11 /content/food11
   ```

   런타임이 끊기면 다시 복사해야 한다.

3. 스크립트를 셀에 붙여넣고 실행한다

   - **v2 기준선**: `colab_v2/basic_unified.py` — Keras 셀과 PyTorch 셀이 나뉘어 있다.
     두 셀 모두 파라미터 653,003이 나와야 한다
   - **v2 Phase 실행**: `common.py` → `phases.py` 순서로 붙여넣고 `smoke_test()`부터.
     결과는 Drive의 `food11_v2_results.csv`에 한 줄씩 쌓인다
   - **v1 재현**: `colab_final/` 스크립트를 하나씩. `DATA_DIR = "/content/food11"`

---

## 환경

- Colab (GPU T4) — 실제 실험은 전부 여기서. 무료 할당량이 떨어지면 몇 시간 기다려야 한다
- 로컬 conda 환경 `nnetwork` (Python 3.12 + TensorFlow + PyTorch) — MNIST 실습용
