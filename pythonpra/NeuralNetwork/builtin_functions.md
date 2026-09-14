# 쓴 내장 함수 정리 — Keras / PyTorch

Food-11 실험에서 실제로 호출한 함수만 모았다. 각 항목은 **시그니처 → 기본값 →
우리가 준 값 → 주의점** 순서다. "기본값"은 인자를 안 넘겼을 때 적용되는 값이고,
이 프로젝트에서 두 프레임워크가 어긋난 지점은 대부분 여기서 나왔다.

작성 2026-09-14. 대상 코드: `colab_final/keras3.py`, `colab_final/torch3.py`

---

## 1. 데이터 로딩

### Keras — `keras.utils.image_dataset_from_directory`

```python
train_ds = keras.utils.image_dataset_from_directory(
    f"{DATA_DIR}/training", image_size=(128,128), batch_size=32)
```

| 인자 | 기본값 | 우리 값 | 비고 |
|---|---|---|---|
| `labels` | `"inferred"` | 기본 | 폴더 이름이 곧 라벨 |
| `label_mode` | `"int"` | 기본 | 정수 라벨 → `sparse_categorical_crossentropy`와 짝 |
| `color_mode` | `"rgb"` | 기본 | 3채널 |
| `image_size` | `(256,256)` | **`(128,128)`** | 읽으면서 리사이즈 |
| `batch_size` | `32` | `32` | |
| `shuffle` | **`True`** | 기본 | **train·val·test 전부 섞임** |
| `seed` | `None` | **안 줌** | ← 재현 불가의 원인 |
| `interpolation` | `"bilinear"` | 기본 | |

한 함수가 **로딩 · 리사이즈 · 라벨링 · 배치 · 셔플**을 전부 처리한다.

### PyTorch — `datasets.ImageFolder` + `DataLoader`

```python
data = datasets.ImageFolder(root=..., transform=train_transform)
loader = DataLoader(data, batch_size=32, shuffle=True)
```

읽는 것(`Dataset`)과 묶는 것(`DataLoader`)이 분리돼 있다. 리사이즈는
`Dataset`이 아니라 `transform`이 한다.

| `DataLoader` 인자 | 기본값 | 우리 값 | 비고 |
|---|---|---|---|
| `batch_size` | `1` | `32` | |
| `shuffle` | **`False`** | train만 `True` | val·test는 **순차** |
| `num_workers` | `0` | 기본 | 메인 프로세스에서 로딩 — **느림** |
| `pin_memory` | `False` | 기본 | GPU 전송 최적화 미사용 |
| `drop_last` | `False` | 기본 | 마지막 배치가 32보다 작을 수 있음 |

> **⚠ 기본값 불일치 ①** — 셔플. Keras는 val·test까지 섞고 PyTorch는 안 섞는다.
> 전체를 한 바퀴 도는 평가라 정확도·평균 loss는 안 바뀌지만, 마지막 부분 배치의
> 구성이 달라져 배치 단위로 평균 낸 loss가 미세하게 흔들릴 수 있다.

---

## 2. 전처리와 증강

| 하는 일 | Keras | PyTorch |
|---|---|---|
| 리사이즈 | `image_dataset_from_directory(image_size=)` | `transforms.Resize((128,128))` |
| 0~1 변환 | `layers.Rescaling(1./255)` | `transforms.ToTensor()` (자동) |
| 좌우 반전 | `layers.RandomFlip("horizontal")` | `transforms.RandomHorizontalFlip()` |
| 회전 | `layers.RandomRotation(0.1)` | `transforms.RandomRotation(10)` |
| 확대·축소 | `layers.RandomZoom(0.1)` | **없음** |
| 붙는 위치 | **모델 층** | **데이터 변환** |

`ToTensor()`는 0~1 변환과 함께 `HWC → CHW` 축 변경까지 한다. Keras는 `Rescaling`만
하면 되고 축은 그대로 `HWC`.

### 회전 — 단위와 채움이 둘 다 다르다

| | Keras `RandomRotation(0.1)` | PyTorch `RandomRotation(10)` |
|---|---|---|
| 단위 | **2π의 비율** → ±36° | **도(degree)** → ±10° |
| 빈 구석 채움 | `fill_mode="reflect"` (거울 반사) | `fill=0` (검정) |
| 보간 | `"bilinear"` | `NEAREST` |

> **⚠ 기본값 불일치 ②** — 회전 강도가 **3.6배** 차이 났고, 회전 후 생기는 빈 구석을
> Keras는 이미지를 반사해 채우고 PyTorch는 검게 남긴다. 증강된 그림 자체가 달랐다.

### 증강이 켜지고 꺼지는 방식

- **Keras** — 모델 층이라 `model.fit()`에서 자동으로 켜지고 `evaluate()`에서 꺼진다
- **PyTorch** — `train_transform` / `eval_transform`을 **따로 만들어** 각 Dataset에 붙여야 한다

---

## 3. 층

### Conv

```python
layers.Conv2D(32, kernel_size=3, activation="relu", kernel_initializer="he_normal")
nn.Conv2d(3, 32, kernel_size=3)
```

| 인자 | Keras 기본 | PyTorch 기본 | 우리 값 |
|---|---|---|---|
| 패딩 | `"valid"` (없음) | `0` (없음) | 둘 다 기본 → **128 → 126** |
| stride | `1` | `1` | 기본 |
| 활성함수 | `None` (인자로 받음) | 별도 층 `nn.ReLU()` | ReLU |
| 가중치 초기화 | **`glorot_uniform`** | **`kaiming_uniform_(a=√5)`** | Keras만 `he_normal` 명시 |
| bias 초기화 | `zeros` | `uniform(±1/√fan_in)` | 기본 |

> **⚠ 기본값 불일치 ③** — 초기화. Keras 기본 Glorot은 ReLU에 안 맞아 `he_normal`을
> 명시했고, PyTorch는 기본이 이미 Kaiming 계열이라 안 건드렸다. **같은 상태를
> 만들려고 한쪽만 손댄 것.**

파라미터 = `(커널 × 커널 × 입력채널) × 필터수 + 필터수`

### Pooling

```python
layers.MaxPooling2D(pool_size=2)
nn.MaxPool2d(2, 2)
```

| | Keras | PyTorch |
|---|---|---|
| stride 기본 | `None` → `pool_size`와 같음 | `None` → `kernel_size`와 같음 |
| 나머지 처리 | `padding="valid"` → 버림 | `ceil_mode=False` → 버림 |

둘 다 동작이 같다. `61 ÷ 2 = 30.5 → 30`으로 버림.

### BatchNorm

```python
layers.BatchNormalization()
nn.BatchNorm2d(32)
```

| 인자 | Keras 기본 | PyTorch 기본 | 의미 |
|---|---|---|---|
| `momentum` | **`0.99`** | **`0.1`** | 러닝 통계 갱신 속도 |
| `epsilon` / `eps` | **`1e-3`** | **`1e-5`** | 0 나눗셈 방지 |
| 학습 파라미터 | γ, β | γ, β | 채널당 2개 |
| 통계 버퍼 | moving_mean, moving_var | running_mean, running_var | 채널당 2개 |

> **⚠ 기본값 불일치 ④** — `momentum`의 **의미가 반대**다. Keras 0.99 = 배치마다 1%
> 갱신(느림), PyTorch 0.1 = 10% 갱신(빠름). 같은 이름인데 큰 값이 느린 쪽이다.
>
> **⚠ 기본값 불일치 ⑤** — `epsilon`이 **100배** 차이. 분산이 작은 채널에서
> 정규화 결과가 미세하게 달라진다.

**학습/평가 모드가 다르게 계산한다:**
```
train()  →  지금 배치 32장의 평균·분산
eval()   →  학습 중 누적한 러닝 통계
```
초반 몇 epoch은 러닝 통계가 안 여물어 val 지표가 실제보다 나쁘게 나온다.
patience가 짧으면 여기서 성급하게 멈춘다 — torch2가 `patience=3`에서 36.5%,
`patience=5`에서 54.5%가 나온 원인. → `batchnorm_earlystopping.txt`

### Dropout · Dense

| | Keras | PyTorch |
|---|---|---|
| Dropout | `layers.Dropout(0.5)` | `nn.Dropout(p=0.5)` |
| Dense | `layers.Dense(11, activation="softmax")` | `nn.Linear(128, 11)` |
| Dense 초기화 | `glorot_uniform` | `kaiming_uniform_(a=√5)` |

Dropout은 둘 다 **inverted dropout** — 학습 때 살아남은 값에 `1/(1-p)`를 곱해
평균을 유지하고, 평가 때는 아무것도 안 한다.

---

## 4. 손실함수

```python
loss="sparse_categorical_crossentropy"    # Keras — 모델이 softmax까지
loss_fn = nn.CrossEntropyLoss()           # PyTorch — 모델은 logit
```

| | Keras | PyTorch |
|---|---|---|
| 입력 | **확률** (모델에 softmax 있음) | **logit** (내부에서 log_softmax) |
| `from_logits` | `False` 기본 | 해당 없음 |
| 라벨 형태 | 정수 (`sparse_`) | 정수 |
| `label_smoothing` | 인자 있음, 기본 `0.0` | 인자 있음, 기본 `0.0` |
| `weight` (클래스 가중치) | `class_weight`로 `fit()`에 전달 | 생성자 인자 `weight=` |

수학적으로 같지만 PyTorch 쪽이 **수치적으로 더 안정적**이다 — softmax 후 log를
따로 하지 않고 log_softmax로 한 번에 계산하기 때문.

---

## 5. 옵티마이저

| | Keras 기본 | PyTorch 기본 | 우리 값 |
|---|---|---|---|
| **SGD** `learning_rate` | `0.01` | 필수 지정 | `1e-3` |
| SGD `momentum` | `0.0` | `0` | `0.9` |
| SGD `nesterov` | `False` | `False` | 기본 |
| **Adam** `learning_rate` | `0.001` | `1e-3` | `1e-3` |
| Adam `beta_1, beta_2` | `0.9, 0.999` | `0.9, 0.999` | 기본 |
| Adam `epsilon` / `eps` | **`1e-7`** | **`1e-8`** | 기본 |
| **AdamW** `weight_decay` | **`0.004`** | **`0.01`** | 둘 다 `1e-4` 명시 |

> **⚠ 기본값 불일치 ⑥** — Adam의 `epsilon`이 10배 차이.
>
> **⚠ 기본값 불일치 ⑦** — AdamW의 `weight_decay` 기본값이 다르다(0.004 vs 0.01).
> 우리는 양쪽 다 `1e-4`를 명시해서 이건 문제되지 않았다.

**SGD+momentum의 누적 방식이 미묘하게 다르다:**
```
Keras     v ← m·v − lr·g   →   w ← w + v        (lr이 v 안에 들어감)
PyTorch   b ← m·b + g      →   w ← w − lr·b     (lr이 밖에 있음)
```
학습률이 고정이면 완전히 같다. 하지만 **스케줄러로 lr을 바꾸면** Keras는 이미
쌓인 velocity에 옛 lr이 박혀 있고 PyTorch는 안 그렇다. 우리는 SGD에 스케줄러를
안 붙여서 문제되지 않았다.

---

## 6. 콜백과 스케줄러

### EarlyStopping

```python
# Keras — 내장
keras.callbacks.EarlyStopping(monitor="val_loss", patience=7, restore_best_weights=True)

# PyTorch — 내장 없음, 직접 구현
best_val_loss, best_state, counter = float("inf"), None, 0
if val_loss < best_val_loss:
    best_val_loss, best_state, counter = val_loss, copy.deepcopy(model.state_dict()), 0
else:
    counter += 1
    if counter >= patience: break
model.load_state_dict(best_state)
```

| Keras 인자 | 기본값 | 우리 값 | 손구현 대응 |
|---|---|---|---|
| `monitor` | `"val_loss"` | `"val_loss"` | `val_loss` 비교 |
| `min_delta` | `0` | 기본 | `<` 엄격 비교 = 동일 |
| `patience` | `0` | `7` | `patience = 7` |
| `restore_best_weights` | **`False`** | **`True`** | `load_state_dict(best_state)` |
| `start_from_epoch` | `0` | 기본 | 없음 |
| `baseline` | `None` | 기본 | 없음 |

**PyTorch에는 EarlyStopping 내장 클래스가 없다.** 위 손구현은 Keras와 동작이
동등하다 — 최고 기록 추적, 카운터, 가중치 복원까지 대응된다.

> `restore_best_weights`의 기본값이 `False`라는 점에 주의. 명시하지 않으면
> **마지막 epoch의 가중치**로 평가하게 된다.

### ReduceLROnPlateau

```python
keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6)
torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)
```

| 인자 | Keras 기본 | PyTorch 기본 | 우리 값 |
|---|---|---|---|
| `factor` | `0.1` | `0.1` | 둘 다 `0.5` |
| `patience` | `10` | `10` | 둘 다 `2` |
| 개선 판정 | `min_delta=1e-4` **절대값** | `threshold=1e-4` **상대값** | 기본 |
| `min_lr` | `0` | `0` | Keras만 `1e-6` |
| `cooldown` | `0` | `0` | 기본 |
| `verbose` | `0` | (신버전 deprecated) | 기본 |

> **⚠ 기본값 불일치 ⑧** — 개선 판정 방식. Keras는 `best − 1e-4`보다 나아야
> 개선으로 보고, PyTorch는 `best × (1 − 1e-4)`보다 나아야 한다. val_loss가 1.5
> 근처면 PyTorch 기준이 `1.5e-4`로 **약간 더 엄격**하다.
>
> **⚠ 기본값 불일치 ⑨** — `min_lr`. Keras에만 `1e-6`을 줬고 PyTorch는 기본값 0.
>
> **발동 시점이 한 epoch 어긋날 수 있다** — 두 구현의 patience 카운팅 규칙이
> 미묘하게 달라, 같은 `patience=2`로도 감소 시점이 다를 수 있다. 실제 로그로
> 확인해야 한다(아래 참고).

**EarlyStopping과 충돌한다.** 둘 다 같은 `val_loss`를 보므로 patience가 비슷하면
학습률을 낮춘 바로 그 epoch에 종료되어 감소 효과를 못 쓴다.
keras3에서 ES `p=3` → 49.9%, ES `p=7` → 52.1%. **ES patience > ReduceLR patience.**

### 📌 학습률 로그 — PyTorch는 이미 남기고 있다

```python
# torch3.py — 매 epoch 출력하고 hist에 쌓는다
print(f"lr: {optimizer.param_groups[0]['lr']:.2e}")
hist["lr"].append(optimizer.param_groups[0]["lr"])
print(f"[학습률 변화] {hist['lr']}")     # 실행 마지막 줄
```

**torch3 실행 출력의 마지막 `[학습률 변화]` 줄에 ReduceLR 발동 여부가 그대로
찍혀 있다.** 발표에서 "확인하지 않았다"고 한 것은 Keras 쪽에만 해당한다.
Colab 출력이 남아 있으면 한계 하나를 바로 지울 수 있다.

Keras 쪽에서 같은 것을 보려면:
```python
reduce_lr = keras.callbacks.ReduceLROnPlateau(..., verbose=1)   # 발동 시 출력
print(history.history.get("learning_rate"))                      # 또는 히스토리
```

---

## 7. 학습과 평가

| | Keras | PyTorch |
|---|---|---|
| 학습 | `model.fit(train_ds, validation_data=, epochs=, callbacks=)` | 루프 직접 (약 75줄) |
| 평가 | `model.evaluate(test_ds)` | `test()` 직접 |
| 모드 전환 | 자동 | `model.train()` / `model.eval()` |
| 기울기 | 자동 | `loss.backward()` → `step()` → `zero_grad()` |
| 평가 시 기울기 | 자동 차단 | `with torch.no_grad():` |
| GPU | 자동 | `.to(device)` 명시 |
| epoch마다 셔플 | 자동 | `DataLoader(shuffle=True)`가 처리 |

**`optimizer.zero_grad()`를 빼먹으면** 기울기가 배치마다 누적되어 학습이 망가진다.
Keras는 이 세 줄이 `fit()` 안에 숨어 있다.

---

## 기본값이 달랐던 것 — 전체 목록

| # | 항목 | Keras | PyTorch | 영향 |
|---|---|---|---|---|
| ① | val·test 셔플 | 섞음 | 안 섞음 | 없음 |
| ② | 회전 단위 | 2π 비율 → ±36° | 도 → ±10° | **큼** |
| ②' | 회전 빈칸 채움 | 반사 | 검정 | 중간 |
| ③ | Conv 초기화 | Glorot | Kaiming | 명시로 해소 |
| ④ | BatchNorm momentum | 0.99 (1%) | 0.1 (10%) | 중간 |
| ⑤ | BatchNorm epsilon | 1e-3 | 1e-5 | 작음 |
| ⑥ | Adam epsilon | 1e-7 | 1e-8 | 작음 |
| ⑦ | AdamW weight_decay | 0.004 | 0.01 | 명시로 해소 |
| ⑧ | ReduceLR 개선 판정 | 절대값 | 상대값 | 작음 |
| ⑨ | ReduceLR min_lr | 0 (우리 1e-6) | 0 | 작음 |

**②가 가장 크다.** 증강 강도가 3.6배 달랐다는 것은 두 모델이 본 데이터 자체가
달랐다는 뜻이고, 이것만으로도 "같은 조건"이라는 전제가 흔들린다.
분류 헤드 파라미터 11.3배 차이와 함께 발표 한계 ①에 들어간 항목.
