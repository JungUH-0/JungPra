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

## 2. 현재 상태 (2026-09-06 기준)

- 실험 조합 **27개** 완료
- 그중 **5개 조건은 재현 실행(2회차)까지** 완료
- 최고 기록 **61.9%** (PyTorch · 3Conv+BN · AdamW + ReduceLR)
- 발표 자료 PPT 16장 완성, 학습 곡선 그래프 자리 4칸 마련됨
- **남은 것**: keras4(SGD+momentum) 실행 → 결론 ①의 곡선 근거

---

## 3. 파일 목록

```
colab_final/          ← 실제로 돌리는 코드 (Colab 붙여넣기용)
  keras1.py    2 Conv · Adam · 15 epoch · 증강 없음
  keras2.py    3 Conv+BN+He · Adam · 증강 · EarlyStop p=3
  keras3.py    3 Conv+BN+He · AdamW+ReduceLR · EarlyStop p=7
  keras4.py    keras1과 옵티마이저만 다름 (SGD+momentum) ← 아직 미실행
  torch1.py    2 Conv · SGD+momentum · 15 epoch · 증강 없음
  torch2.py    3 Conv+BN · Adam · 증강 · EarlyStop p=5
  torch3.py    3 Conv+BN · AdamW+ReduceLR · EarlyStop p=7
  hyperparameters.txt   6개 파일 조건 비교표 + 프레임워크 간 불일치 정리

food11_presentation.pptx   발표 자료 (16장)

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

### 재현 실행 (같은 조건 2회차)
| 스크립트 | 1차 → 2차 | 편차 |
|---|---|---|
| keras1 | 45.4 → 46.4 | 1.8%p |
| keras2 | 56.1 → 52.5 | 3.6%p |
| keras3 | 52.1 → 56.7 | 4.6%p |
| torch2 | 54.5 → 52.6 | 6.1%p |
| torch3 | 59.2 → **61.9** | 2.7%p |

**실행 간 편차 최대 6.1%p.** 이 수치가 이 프로젝트에서 가장 중요한 숫자다.
5%p 안팎의 차이는 단독 실행 하나로 주장할 수 없다는 기준선.

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
SGD에 불리했을 수 있다. 이건 한계로 인정하고 후속 과제로 남겼다.

---

## 8. 다음에 할 일

1. **keras4.py 실행** (SGD+momentum) — keras1과 옵티마이저만 달라서
   두 곡선을 나란히 놓으면 결론 ①의 시각적 근거가 된다
2. torch1을 Adam/SGD 각각 2회차로 돌리면 재현 데이터가 더 쌓인다
3. PPT 8·9번 슬라이드의 점선 상자에 `curve_*.png` 4장 삽입
4. 결과 나올 때마다 아티팩트의 "재현 실행" 섹션에 행 추가

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
