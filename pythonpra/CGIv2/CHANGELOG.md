# CGIv2 변경 기록

AnyDoor 저장소는 수정하지 않는다. 여기 적힌 것은 전부 CGIv2 쪽 코드다.

---

# 기술·도구 등록부

단계마다 **어떤 기술을 어떤 도구로 구현했는지**와 **그 도구를 갈아끼울 수
있는지**를 적는다. 나중에 도구를 바꾸거나 가중치를 갱신할 때 어디까지
건드려도 되는지 여기서 판단한다.

## 교체 등급

| 등급 | 뜻 | 바꿨을 때 |
|:---:|---|---|
| 🟢 | **자유** | 입출력 규격만 맞추면 됨. 가중치와 무관 |
| 🟡 | **규약 결합** | 실행은 되는데 **에러 없이 품질만 떨어진다.** 가중치가 학습한 입력 형태를 어기는 것 |
| 🔴 | **킬스위치** | 가중치가 무의미해진다. 재학습 없이는 불가 |

🟡가 가장 위험하다 — 에러가 안 나서 "왜 결과가 이상하지"로만 나타난다.

## 전처리

| 기능 | 기술 | 도구 | 등급 | 결합 대상 · 교체 후보 |
|---|---|---|:---:|---|
| 객체 마스크 생성 | 이진 세그멘테이션 | **BiRefNet_HR-matting**<br>`transformers.AutoModelForImageSegmentation` | 🟢 | 없음. SAM 2 · U²-Net · DeepLabV3 · rembg 무엇이든 가능.<br>**연속 알파는 의미 없다** — `process_pairs`가 전부 `>128`로 이진화한다 |
| 가는 부분 복원 | 형태학적 닫힘 | `cv2.morphologyEx(MORPH_CLOSE)` | 🟢 | 없음 |
| 면적비 정규화 | bbox 기준 크롭 / 여백 | OpenCV + numpy | 🟢 | 로직은 자유. **다만 목표 상수(1% / 64%)는 AnyDoor 관문 값**이라 바꾸면 탈락한다 |
| 배치 마스크 | 정규화 좌표 → 사각 / 실루엣 | numpy + `cv2.resize` | 🟢 | 없음. Gradio 브러시 UI로 대체 가능 |
| 참조 정규화 | 224 정사각 · 흰 배경 · 1.2배 | AnyDoor `data_utils` | 🟡 | **DINOv2 입력 규약.** 해상도·패딩색·확대비를 바꾸면 특징 분포가 이탈 |
| 디테일 조건 | Sobel/Scharr 에지 × 원본색 | AnyDoor `data_utils.sobel` | 🟡 | **ControlNet이 이 형태를 학습했다.** Canny나 depth로 바꾸면 못 알아듣는다.<br>단 `thresh=50` / `erode ×2` 상수는 객체별 조정 가능 |
| 타깃 크롭 | bbox 1.3~3.0배 → 512 | AnyDoor `data_utils` | 🟡 | 객체 크기 사전분포. 512는 특히 고정 |

## 가중치 라인

| 기능 | 기술 | 도구 | 등급 | 비고 |
|---|---|---|:---:|---|
| ID 조건 | 자기지도 ViT | **DINOv2 ViT-g/14** + `Linear(1536→1024)` | 🔴 | **조건 경로가 하나뿐이라 대체가 없다.** 바꾸면 projector·U-Net 크로스어텐션·ControlNet이 전부 죽고 VAE 84M만 남는다 (3.4%) |
| 공간 조건 | ControlNet 잔차 13개 | `cldm.ControlNet` (힌트 4채널) | 🔴 | 구조·채널 수 고정 |
| 생성 백본 | Latent Diffusion | SD 2.1 U-Net (`ControlledUnetModel`) | 🔴 | `context_dim 1024` 고정 |
| latent 코덱 | VAE 8배 | `AutoencoderKL` | 🔴 | `scale_factor 0.18215` |
| 노이즈 스케줄 | scaled_linear, eps 예측 | `configs/anydoor.yaml` | 🔴 | β 곡선을 바꾸면 ε 예측이 전부 어긋난다 |
| **샘플러** | DDIM eta=0 | `cldm/ddim_hacked.py` | 🟢 | **자유다.** 같은 스케줄을 다르게 훑을 뿐.<br>후보: DPM-Solver++ (저장소에 1,153줄이 이미 있음) · UniPC · Euler A |
| **실행 프레임워크** | — | PyTorch 2.0 + PL 1.5<br>(`cldm` / `ldm`) | 🟢 | 조건부 자유. **U-Net이 순수 SD 2.1이라 diffusers로 이식 가능하다.**<br>이식하면 PL 의존성 제거 + 최신 샘플러 + `enable_model_cpu_offload()` |
| 조건 토큰 **개수** | 257 (cls 1 + patch 256) | — | 🟢 | 어텐션은 가변 길이. **차원 1024만 고정**이고 개수는 바꿔도 실행된다 |
| 추론 파라미터 | `cfg` · `steps` · `control_strength` | — | 🟢 | 학습과 무관 |

> **차원은 고정, 개수는 자유. 스케줄은 고정, 샘플러는 자유.**

## 후처리

| 기능 | 기술 | 도구 | 등급 | 교체 후보 · 주의 |
|---|---|---|:---:|---|
| 역변환 | 패딩 제거 + 좌표 복원 | numpy + OpenCV | 🟡 | `process_pairs`와 짝이다. 전처리를 바꾸면 같이 바꿔야 한다 |
| 되붙이기 범위 | 알파 합성 — 크롭 / 박스 / 인물 | `paste.py` (numpy) | 🟢 | `crop` = `run_inference.py`, `box` = `run_gradio_demo.py:140-143`. 배치 합성은 **`person`** (2026-09-23) |
| 인물 분할 (생성물) | 매팅 분할 + 덩어리 선택 | **BiRefNet_HR-matting** `alpha()` (마스크 생성과 공유) | 🟢 | `alpha()` 또는 `binary()`만 있으면 된다. SAM 2 박스 프롬프트 · DeepLabV3 person · Mask2Former person |
| 경계 전경색 추정 | Blur-Fusion (Forte & Pitié 2021) | `cv2.blur` | 🟢 | pymatting `estimate_foreground_ml` · closed-form 전경 추정 |
| 경계 블렌딩 | 선형 알파 페더링 | numpy | 🟢 | 포아송(`cv2.seamlessClone`) 가능하나 **색을 주변에 맞추느라 로고 색까지 이동**시킨다 |
| 색 정합 | LAB 평균/표준편차 매칭 | `cv2.cvtColor` | 🟢 | 히스토그램 매칭 · Reinhard 등. **AnyDoor가 이미 조명을 맞추려 시도하므로 이중 보정 주의** |
| 광원 추정 | 밝기 gradient | `cv2.Sobel` | 🟢 | 학습형 추정기로 교체 가능. ⚠️ W01에서 위쪽을 가리킴 — `offset` 전용 |
| 그림자 (`offset`) | 실루엣 평행이동 + 가우시안 | `cv2.warpAffine` | 🟢 | ⚠️ 서 있는 사람에 부적합 (2026-09-26) |
| 접지 그림자 (`contact`) | 가우시안 타원 2겹 (AO 근사) | `shadow.py` | 🟢 | **3단계 기본** (2026-09-26) |
| 투영 그림자 (`cast`) | 평면 투영 아핀 + β 곱 | `shadow.py` · `cv2.warpAffine` | 🟢 | 해 필요. 학습형 그림자 생성기로 교체 가능 |
| 해 추정 | 기존 사람 그림자 광선 탐색 | `shadow.estimate_sun` | 🟢 | 20개 중 0개 검출 — UI 입력 권장 |
| 정체성 지표 | ViT 임베딩 코사인 | **DINOv2** (엔진에서 재사용) | 🟢 | CLIP · DreamSim 등. **단 DINOv2는 이미 로드돼 있어 공짜다**<br>⚠️ 반드시 `cutout()`으로 배경을 지우고 재야 한다 |
| 이음매 지표 | LAB 밴드 거리 | OpenCV | 🟢 | |
| 텍스트 지표 | OCR + 편집거리 | `easyocr` (선택) | 🟢 | PaddleOCR · Tesseract |

## 인터페이스 계약

도구를 갈아끼울 때 지켜야 할 입출력이다. 이것만 맞으면 나머지는 자유다.

```
mask.*            RGB uint8 (H,W,3)        -> 0/1 uint8 (H,W)
prep.normalize_*  (RGB, 0/1 mask)          -> (RGB, 0/1 mask, 사유 문자열)
prep.place_box    배경 shape + 위치 파라미터 -> 0/1 uint8 (H,W)
PairBuilder.build (ref, ref_m, tar, tar_m) -> dict(ref/jpg/hint/extra_sizes/tar_box)
AnyDoorEngine     위 dict                  -> 512x512x3 float 0~255
crop_back         (pred, 배경, sizes, box) -> 원본 크기 uint8
paste.person_alpha (합성, 배치 마스크, crop_box, masker) -> (알파 0~1 (H,W) | None, 정보 dict)
paste.box_alpha   (배치 마스크, crop_box)   -> 알파 0~1 (H,W) | None
paste.compose     (합성, 배경, 알파, fg=None) -> RGB uint8
masker (person 용) alpha(RGB) -> 0~1 float (H,W)   또는   binary(RGB) -> 0/1 uint8
postproc.*        (RGB, 0/1 region)        -> RGB uint8 (같은 크기)
evaluate.*        (ref, ref_m, gen, gen_m) -> {지표: float}
```

## 가중치를 갱신하면 무엇이 풀리나

재학습 범위에 따라 🟡·🔴가 해제된다.

| 재학습 범위 | 풀리는 것 | 비용 |
|---|---|---|
| **아무것도 안 함** | 🟢만 | — |
| ControlNet 364M | 디테일 조건을 **Sobel 외의 것으로** 교체 가능<br>(Canny · depth · 법선 · 4채널 구성 변경) | 쌍 데이터 필요. 소량이면 오히려 나빠진다 |
| ControlNet + projector | **참조 정규화 규약**(224 · 확대비 · 패딩색) 변경 가능 | 위와 같음 |
| U-Net `output_blocks` 추가 | 타깃 해상도·크롭 규약에 여유 | 55만 표본급 데이터 필요 |
| 전체 | 🔴 전부 — 인코더 교체 포함 | **사실상 새 모델을 만드는 것** |

**주의**: 위 표는 "가능해진다"이지 "좋아진다"가 아니다. 원본은 55만 표본으로
학습됐고 그 분포 안에 사람·시계·가방·자동차가 이미 들어 있다. 수백 장 규모의
재학습은 catastrophic forgetting 쪽이 더 유력하다.

---

## 2026-09-21

### 만든 것

CGIv2 초기 구축. AnyDoor의 가중치 라인은 그대로 쓰고 전처리·후처리만 새로 짰다.

| 모듈 | 줄 | 역할 |
|---|---:|---|
| `cgiv2/anydoor.py` | 176 | 가중치 라인 래퍼 + DINOv2 토큰 캐싱 |
| `cgiv2/pairs.py` | 284 | `process_pairs` 통합본 + `crop_back` |
| `cgiv2/prep.py` | 165 | 객체 정규화 + 배치 마스크 |
| `cgiv2/postproc.py` | 168 | 페더링 · 색 정합 · 그림자 |
| `cgiv2/evaluate.py` | 159 | DINOv2 코사인 · 이음매 · OCR |
| `cgiv2/mask.py` | 119 | BiRefNet 마스크 생성 |
| `cgiv2/pipeline.py` | 137 | 연결 |
| `scripts/` | 423 | `check_dataset` · `run_single` · `run_batch` |

### 원본에서 고친 것 셋

모두 가중치와 무관한 버그다.

**① 패딩 센티넬** — `run_inference.py:255`

```python
collage_mask = pad_to_square(collage_mask, pad_value=-1, ...).astype(np.uint8)
#                                                     ↑ uint8 에서 255 로 감김
collage_mask = (cv2.resize(...) > 0.5).astype(np.float32)   # 255 > 0.5 → 1.0
```

패딩 영역이 **"여기 생성해라"(1.0)** 가 된다. 학습 경로(`base.py`)는 이걸 알고
센티넬 `2`를 쓴 뒤 `-1`로 되돌린다. 통합본은 양쪽 다 `2`를 쓴다.

죽은 경로가 아니다. `box2squre`가 `max(0,x1)` / `min(W,x2)`로 경계를 클램프
하므로 **객체가 프레임 가장자리에 있으면 패딩이 실제로 생긴다.**

**② 타깃 크롭 랜덤성** — `data_utils.py:107`

```python
ratio = np.random.randint(ratio[0]*10, ratio[1]*10) / 10
```

추론에서도 `[1.5, 3]`이라 **매 실행마다 크롭이 달라진다.** diffusion seed를
고정해도 크롭이 흔들리므로 격자 탐색 결과를 신뢰할 수 없다.
→ `PairBuilder.build(train=False)`는 `tar_crop_ratio=2.0` 고정.
학습(`train=True`)은 증강이므로 원본 랜덤을 유지.

**③ `crop_back` 1픽셀 밀림** — `run_inference.py:215`

```python
pred = np.clip(x_samples[0], 0, 255)[1:, :, :]   # 맨 윗줄을 버린 뒤 resize
```

→ 자르지 않는다. 더해서 `feather` 인자로 경계 알파 페더링을 선택할 수 있게 했다
(`feather=0`이면 원본과 같은 하드 대입).

### 설계상 정한 것

| | 결정 | 이유 |
|---|---|---|
| 후처리 기본값 | **전부 꺼짐** | AnyDoor는 "확산이 조명·그림자를 암묵 처리"를 전제로 후처리를 안 뒀다. 측정 전에 켜면 이중 보정 |
| 정체성 복원 | **구현 안 함** | AnyDoor는 자세를 바꾸므로 참조–결과 픽셀 대응이 없다. 고주파를 되붙일 좌표가 존재하지 않는다 |
| 연결성 자동 보정 | 안 함 | `bridge_thin_parts`는 제공하되 자동 적용 안 함. 관문 통과시키려고 가방 끈을 뭉개면 본말전도 |
| `process_pairs` 숫자 | 원본 그대로 | 224 / 512 / 1.3~3.0배는 55만 표본에서 학습된 규약 |

---

## 2026-09-21 · 첫 실행에서 드러난 것

### 마스크 생성 — 통과

`scripts/make_masks.py` 신설. BiRefNet_HR-matting(2048) 사용.

| 객체 | 크기 | 면적 | 연결성 |
|---|---|---:|---:|
| F01_man-olive-sweater-cream | 3733×5600 | 16.3% | 1.00 |
| F07_woman-tee-jeans-grey | 4160×6240 | 12.8% | 1.00 |
| F11_woman-blazer-jeans-white | 4016×6016 | 14.5% | 1.00 |

셋 다 `process_pairs` 관문 통과.

### 비교 실행 — `scripts/compare_runs.py` 신설

AnyDoor 원본 경로와 CGIv2 경로를 **같은 가중치·seed·배치 마스크**로 돌린다.
모델은 한 번만 올리고, 원본 함수는 흉내내지 않고 `ast`로 `run_inference.py`에서
`process_pairs` / `crop_back` 정의만 꺼내 실행한다 (import하면 모델을 또 올린다).
`pred[1:,:,:]` 1픽셀 밀림까지 재현한다.

### 🐛 정체성 지표가 틀렸다 — 수정함

**증상**: `identity=0.051`, `seam=0.9`. 아무것도 생성되지 않은 것처럼 보였다.

**실제**: 이미지를 열어보니 **생성은 정상**이었다. 사람이 제대로 들어가 있다.

**원인**: `IdentityScorer.score`가 양쪽을 그냥 잘라서 DINOv2에 넣었다.
DINOv2의 CLS 토큰은 **장면 기술자**다. 참조는 "크림색 스튜디오의 인물",
생성물은 "콜로세움 앞 인물" — 장면이 전혀 다르니 코사인이 0 근처로 나온다.
**정체성이 아니라 배경을 재고 있었다.**

**수정**:

```python
def cutout(image, mask, pad_value=255):
    """배경을 흰색으로 지우고 bbox 크롭 + 정사각 패딩"""
```

`process_pairs`가 참조를 다루는 방식과 똑같이 맞췄다 — 조건 인코더가 실제로
보는 표현에서 재는 것이 맞다. `score()`가 양쪽에 `cutout`을 적용한다.

`segment` 인자를 추가했다. 생성물의 실제 실루엣을 뽑는 함수를 넘기면
배치 사각형 안의 배경이 섞이는 문제까지 없어진다.

`calibrate()`를 추가했다. **값 자체는 의미가 없고 기준선과의 거리로만 읽어야
한다.** 같은 객체(증강쌍)가 상한, 다른 객체가 바닥이다.

### 배운 것 — 구조적 한계

F01의 실제 숫자를 따라가면:

```
원본         3733 × 5600, 마스크 면적 16.3%
인물 bbox    약 1380 × 4130
1.2배 확대   약 1650 × 4950
정사각 패딩  4950 × 4950    ← 좌우가 흰 여백
224 로 축소  인물 높이 ≈ 187px
얼굴         187 / 7.5 ≈ 25px
```

**DINOv2가 보는 얼굴이 25픽셀이다.** `cfg`나 `control_strength`로 고칠 수 없다.
없는 정보는 생기지 않는다.

전신 합성에서 보존되는 것은 **옷·체형·자세**이지 얼굴이 아니다.
1안에서 "그 사람"이 보여야 한다면 상반신 크롭으로 가야 한다.

### IP-Adapter는 답이 아니다

검토했으나 기각. 두 가지 이유다.

1. **베이스 모델에 묶여 있다.** `to_k_ip`/`to_v_ip`를 추가로 달아 학습한
   가중치이고, 공개본은 SD 1.5와 SDXL용뿐이다. 게다가 AnyDoor의 U-Net은
   기본 SD 2.1에서 파인튜닝돼 떠난 상태라 어차피 어긋난다.
2. **붙여도 하향이다.** IP-Adapter Plus는 16토큰(Resampler 압축),
   AnyDoor는 257토큰(압축 없음). CGI에서 로고·얼굴이 뭉개지던 원인이
   16토큰 병목이었고 그걸 고치려고 옮겨왔다.

---

### 지표가 배경을 재고 있었다는 추가 증거

같은 인물 F01이 배경에 따라 이렇게 나왔다.

| 배경 | 성격 | 옛 지표 |
|---|---|---:|
| 콜로세움 | 석조, 어두운 회갈색 | 0.051 |
| 경복궁 | 단청, 채도 높음 | 0.259 |
| 산토리니 | **흰 벽** | **0.483** |

F01의 참조 배경이 크림색 스튜디오다. **참조 배경과 닮은 장면일수록 점수가
높다** — 정체성과 무관하게. 진단이 맞았다는 것을 보여주는 순서다.

### `scripts/rescore.py` 신설

이미지는 정상이므로 재생성하지 않는다. 저장된 PNG만 다시 읽어 채점한다.

| | 옛 채점 | 재채점 |
|---|---|---|
| 배경 | 그대로 둠 → 장면을 잼 | `cutout()`으로 흰 배경 정사각 |
| 생성물 영역 | 배치 사각형 (배경 섞임) | **BiRefNet으로 재분할** |
| 해석 | 절대값 | `calibrate()` 기준선 내 위치(%) |

CGI venv에서 돌린다 (BiRefNet에 transformers + timm이 필요).

---

## 2026-09-21 · 도구 교체 기반 추가

파라미터는 건드리지 않고 **🟢 등급 도구만 갈아끼울 수 있게** 했다.

### 추가한 마스크 도구 — 계약: `RGB uint8 (H,W,3) → 0/1 uint8 (H,W)`

| 도구 | 클래스 | 값 |
|---|---|---|
| BiRefNet HR-matting *(기존)* | `BiRefNetMasker` | `model="ZhengPeng7/BiRefNet_HR-matting"`, `size=2048`, `half=True`, `thresh=0.5`, `keep_largest=False` |
| BiRefNet 표준 *(신규)* | `BiRefNetMasker` | `model="ZhengPeng7/BiRefNet"`, `size=1024` (모델명에 `_HR` 없으면 자동) |
| DeepLabV3 *(신규)* | `DeepLabV3Masker` | `deeplabv3_resnet101(weights=DEFAULT)`, `PERSON=15`, `size=720` |
| SAM 2 *(신규)* | `SAM2Masker` | `model="facebook/sam2.1-hiera-large"`, 기본 점 3개 = `(cx, H×0.35)`, `(cx, H×0.55)`, `(cx, H×0.75)`, `multimask_output=True` → 최고 score 선택 |

공통 정규화: `mean=[0.485,0.456,0.406]`, `std=[0.229,0.224,0.225]`

`get_masker(tool)` 팩토리 추가. 허용 이름:
`birefnet` / `birefnet_hr` / `hr` · `birefnet_1024` / `birefnet_std` / `std` ·
`deeplabv3` / `deeplab` · `sam2` / `sam`

**도구별 성격 차이** (이게 선택의 근거다)

```
BiRefNet    "가장 눈에 띄는 것"  경계 정밀, 클래스 모름 → 소품도 같이 잡힘
DeepLabV3   "사람"              경계 거침, 클래스 앎  → 소품 안 잡힘
SAM 2       "우리가 가리킨 것"   점 프롬프트 필요
```

### 추가한 후처리 도구

| 기능 | 기존 | 신규 | 신규 값 |
|---|---|---|---|
| 블렌딩 | 선형 알파 페더링 | `blend_poisson` | `cv2.seamlessClone`, `NORMAL_CLONE` 또는 `MIXED_CLONE`, 중심 = region bbox 중점 |
| 색 정합 | `match_color_lab` (LAB 평균/표준편차) | `match_color_hist` | CDF 매칭, 256 bin, `np.interp` 기반 LUT, `strength` 기본 `0.5` |

`blend_poisson`은 영역이 이미지 경계에 닿으면 `cv2.error`가 나므로 `try/except`로
받아 원본을 돌려준다.

**포아송 주의** — 경사도를 보존하며 색을 주변에 맞추므로 **물체 전체 색이 끌려간다.**
로고·라벨이 중요한 2안에서는 위험하다.

### `Result`에 중간 산출물 보존 — GPU 없이 후처리 재실행

```python
Result.raw          512×512×3 모델 출력
Result.extra_sizes  crop_back 용 H1,W1,H2,W2
Result.crop_box     crop_back 용 y1,y2,x1,x2
Result.repost(bg, st)   → 후처리만 다시 적용
```

`Compositor.__call__(..., keep_raw=True)`로 켠다. 기본은 `False`(메모리 절약).

**이유**: 확산은 한 번만 돌리고 블렌딩·색 정합은 몇 번이든 다시 할 수 있다.
현재 쌍당 6.6분인데, 후처리 도구 6종 비교를 재생성으로 하면 40분이 걸린다.
`repost`면 **초 단위**다.

후처리 경로를 `_finish()` 한 함수로 모았다. 도구 선택이 전부 여기 있다.

### `Settings` 전체 기본값 — 2026-09-21 시점 (최신 전체 목록은 '인물만 되붙이기' 절)

```python
steps            = 50        # run_inference.py 기본값
cfg              = 5.0       # run_inference.py 기본값
control_strength = 1.0
seed             = 1234
shape_control    = False
tar_crop_ratio   = 2.0       # 원본은 [1.5,3.0] 랜덤 — 고정으로 바꿈
normalize_object = True
feather          = 0
color_match      = 0.0
color_tool       = 'lab'     # lab | hist          ← 신규
shadow           = False
mask_tool        = 'birefnet_hr'                    ← 신규 (기록용)
blend_tool       = 'feather' # feather | poisson | poisson_mixed | none  ← 신규
```

`tag()`가 도구 선택까지 파일명에 반영하도록 고쳤다.

### `scripts/swap_tools.py` 신설

파라미터를 고정한 채 🟢 등급 도구만 갈아끼우는 실험 러너.

**설계 근거 — 비용이 두 자릿수 차이 난다**

```
마스크 도구 교체   전처리가 바뀌므로 확산 재실행 필요   쌍당 수 분
후처리 도구 교체   raw 512 재활용                      쌍당 수 초

순진하게  마스크 3종 × 후처리 7종 × 4쌍 = 84회 생성  → 약 9시간
이 방식   마스크 3종 × 4쌍           = 12회 생성  → 약 50분
```

마스크 도구마다 한 번만 생성하고 후처리 변형은 전부 `Result.repost()`로 만든다.

**후처리 변형 `POST_VARIANTS` 전체 값**

| 이름 | `blend_tool` | `feather` | `color_match` | `color_tool` |
|---|---|---:|---:|---|
| `none` | `none` | 0 | 0.0 | — |
| `feather6` | `feather` | **6** | 0.0 | — |
| `feather16` | `feather` | **16** | 0.0 | — |
| `poisson` | `poisson` | 0 | 0.0 | — |
| `poisson_mixed` | `poisson_mixed` | 0 | 0.0 | — |
| `lab0.3` | `feather` | 6 | **0.3** | `lab` |
| `hist0.3` | `feather` | 6 | **0.3** | `hist` |

**고정 파라미터 (인자로 명시하지 않으면 안 바뀐다)**

```
--steps 50  --cfg 5.0  --strength 1.0  --seed 1234
--bg-width 1600  --obj-width 1200
--cy 0.62  --cx 0.5  --height 0.5
내부 고정: tar_crop_ratio 2.0, normalize_object True
```

**마스크 자체도 잰다** — 결과뿐 아니라 도구가 만든 마스크의 생성시간·면적·
연결성을 함께 기록한다. **연결성이 관문 0.90을 넘는지**가 특히 중요하다.
DeepLabV3는 경계가 거칠어 떨어질 수 있고, 그러면 가방 같은 객체에 못 쓴다.

마스크 PNG도 `outputs/swap/mask_<도구>/`에 남긴다.

---

# 상수 등록부

값 하나까지 여기 적는다. 실험 결과를 나중에 재현하려면 이게 있어야 한다.

## AnyDoor 규약 — 🟡 바꾸면 품질이 조용히 떨어진다

| 상수 | 값 | 위치 |
|---|---|---|
| 참조 해상도 | **224** | `pairs.build` |
| 참조 확대비 (추론) | **1.2** 고정 | 원본도 `randint(12,13)/10` = 1.2 |
| 참조 확대비 (학습) | **1.1 ~ 1.4** 랜덤 | `randint(11,15)/10` |
| 참조 패딩색 | **255** (흰색) | |
| 타깃 해상도 | **512** | |
| 타깃 bbox 확대 | **[1.1, 1.2]** | `expand_bbox` |
| 타깃 크롭 확대 (추론) | **2.0** 고정 | 원본 `[1.5, 3.0]` 랜덤 → 변경 |
| 타깃 크롭 확대 (학습) | **[1.3, 3.0]** 랜덤 | 원본 유지 |
| 패딩 센티넬 | **2** → 나중에 **-1** | 원본 추론은 `-1` 직행 (버그) |
| 마스크 교란 확률 (학습) | **0.7** | |
| latent shape | **(4, 64, 64)** | |
| `control_scales` | `[strength] × **13**` | |
| 무조건 조건 | `torch.zeros((1,3,**224**,224))` | 검은 이미지 |

## 관문 — AnyDoor 값 그대로

| 관문 | 값 |
|---|---|
| 연결성 | `mask_score > **0.90**` |
| 면적 | **0.01 < r < 0.64** (= 0.1² ~ 0.8²) |
| 최소 변 | bbox 각 변 ≥ **0.10** |
| 타깃 최대 변 | ≤ **0.8** (`max_ratio`) |

## 전처리 — 🟢 우리 값

| 함수 | 상수 | 값 |
|---|---|---|
| `normalize_object` | `lo` / `hi` | **0.02** / **0.55** (관문 0.01/0.64보다 안쪽) |
| | `crop_target` | **0.20** |
| | `pad_target` | **0.45** |
| `crop_to_area` | `min_margin` | **0.15** |
| `pad_to_area` | `pad_value` | **255** |
| `place_box` | `height_ratio` 클립 | **0.05 ~ 0.78** (관문 0.8 상한 회피) |
| `bridge_thin_parts` | `radius` | **3** (기본, 자동 적용 안 함) |

## 후처리 — 🟢 우리 값

| 함수 | 상수 | 값 |
|---|---|---|
| `crop_back` | `feather` | **0** (기본 = 원본과 같은 하드 대입) |
| `surround_ring` | `inner` / `outer` | **6** / **40** |
| `seam_score` | `band` | **5** |
| `_region_stats` | 최소 픽셀 | **50** |
| `match_color_lab` | `strength` | **0.5** |
| `match_color_hist` | `strength` / bin | **0.5** / **256** |
| `estimate_light_direction` | ring | inner **4**, outer **60** |
| | Sobel `ksize` | **5** |
| `add_contact_shadow` | `direction` | **(0.3, 1.0)** |
| | `length` / `blur` / `opacity` | **0.25** / **31** / **0.35** |
| `paste.person_alpha` | `margin` / `min_aspect` | **0.08** / **0.6** (2026-09-23) |
| | `thresh` / `min_inside` / `grow` | **0.5** / **0.5** / **0.01** |
| | 연결성 · 팽창 커널 | **8** · `MORPH_ELLIPSE` |
| `paste.box_alpha` | `BOX_EXPAND` | **1.2** |
| `paste.estimate_foreground` | `FG_RADII` / eps | **(90, 6)** / **1e-5** |
| | 계산 범위 여백 | **max(FG_RADII) = 90px** |
| `shadow.contact_shadow` | `FEET_BAND` / `CONTACT_WIDTH` / `CONTACT_HEIGHT` / `CONTACT_CORE` | **0.04** / **1.25** / **0.03** / **0.3** (2026-09-26) |
| | `strength` · 넓은 타원 계수 | **0.5** · **0.6** |
| `shadow.cast_shadow` | `soft` / `fade` / `CAST_MIN_DY` | **(0.002, 0.008)** / **0.2** / **0.08** |
| | `strength` (β 없을 때) | **0.45** |
| `shadow.estimate_sun` | `min_h` / `step_deg` / `dark_min` | **40** / **5** / **0.3** |
| | `min_evidence` / `min_concentration` | **2** / **0.9** |
| | 고리 · 광선 · 길이 탐색 | 키 × **0.35~0.9** · **0.05~0.5** · **0.05~1.5** |

## 평가 — 🟢 우리 값

| 함수 | 상수 | 값 |
|---|---|---|
| `cutout` | `pad_value` | **255** |
| `_crop_to_mask` | `pad` | **0.1** (segment 경로는 **0.05**) |
| `embed` | 입력 | **224 × 224** |
| `calibrate` | `max_pairs` | **60** |

## 실행 값 — 재현용

### `make_masks.py` (2026-09-21 실행)

```
--src    D:/JungPra/pythonpra/CGI/objects
--names  F01 F07 F11
--model  ZhengPeng7/BiRefNet_HR-matting   (size 2048)
--bridge 0
--save-alpha
```

결과: F01 면적 16.3% 연결성 1.00 / F07 12.8% 1.00 / F11 14.5% 1.00

### `compare_runs.py` (2026-09-21 실행, 진행 중)

```
--objects      F01 F07 F11
--backgrounds  K02 W03 W05
--steps 50  --cfg 5.0  --strength 1.0  --seed 1234
--feather 6
--bg-width 1600  --obj-width 1200
--cy 0.62  --cx 0.5  --height 0.5
내부 고정: tar_crop_ratio 2.0, normalize_object True,
          shape_control False, color_match 0.0, shadow False
비교 썸네일 높이 540
```

**주의** — 이 실행의 `identity` 값은 옛 지표(배경 포함)라 해석하면 안 된다.
`rescore.py`로 다시 채점해야 한다.

---

## 2026-09-22 · 얼굴 정체성 지표 추가 — 측정 결과가 계획을 바꾼다

### 왜 필요했나

DINOv2 코사인은 **인물 컷아웃 전체**를 잰다. 옷 색·체형·자세·실루엣이 면적의
대부분이고 얼굴은 몇 %다. 그래서 얼굴이 뭉개져도 0.88이 나왔다.
**"내 사진을 넣는다"가 목적인데 지표가 그것을 안 재고 있었다.**

### 추가한 것

| | 값 |
|---|---|
| 검출 | YuNet `face_detection_yunet_2023mar.onnx` (228 KB) |
| 인식 | SFace `face_recognition_sface_2021dec.onnx` (37 MB) |
| 출처 | OpenCV Zoo (`media.githubusercontent.com/media/opencv/opencv_zoo/main/models/...`) |
| 위치 | `work/models/` |
| API | `cv2.FaceDetectorYN_create` · `cv2.FaceRecognizerSF_create` — **OpenCV 내장, 추가 패키지 없음** |
| 임계값 | `FaceScorer.SAME_PERSON = **0.363**` (OpenCV 권장) |
| 검출 파라미터 | `score_threshold=0.6`, `nms=0.3`, `topk=500`, 입력 `(320,320)` 초기값 |
| 작은 얼굴 대응 | 1차 실패 시 **상단 60%를 2배 확대**해 재검출, 좌표는 `/2`로 복원 |

`cgiv2/evaluate.py :: FaceScorer` · `scripts/face_score.py` 신설.
GPU를 쓰지 않는다 — 저장된 PNG만 읽는다.

### 측정 결과 (9쌍 × 2경로)

```
기준선
  자기 자신 (좌우반전)    0.9370   ← 상한
  다른 사람               0.0234   ← 바닥  (n=3)
  OpenCV 같은 사람 판정선  0.363

원본    0.1051   → 다른 사람
CGIv2   0.1072   → 다른 사람
차이    +0.0021  (잡음)
```

**기준선 내 위치 약 9%.** 생판 남에서 본인까지의 거리 중 9%만 왔다.

### 두 지표가 정반대를 말한다

| 지표 | 재는 것 | CGIv2 값 | 기준선 내 |
|---|---|---:|---:|
| DINOv2 | 인물 전체 | 0.877 | **77.9%** |
| **SFace** | **얼굴만** | **0.107** | **9%** |

옷·체형은 보존되고 얼굴은 거의 보존되지 않는다. **AnyDoor가 object-level
모델이라는 것의 실측 증거다.**

### 쌍별

| 객체 | 원본 | CGIv2 |
|---|---:|---:|
| F01 남·올리브 스웨터 | 0.17 ~ 0.24 | **0.29 ~ 0.34** |
| F07 여·회색 티 | -0.09 ~ 0.04 | -0.08 ~ 0.00 |
| F11 여·블레이저 | 0.09 ~ 0.18 | -0.01 ~ 0.19 |

F07은 **음수** — 참조와 반대 방향이다. 앞서 본 반투명 결과와 일치한다.

### 정보가 사라진 지점

```
참조 원본 얼굴     156 px   (1200폭 객체 이미지)
224 참조 안 얼굴   약 17~25 px   ← 여기서 소실
생성물 얼굴        122 px   (1600폭 배경)
```

**출력 해상도는 문제가 아니다.** 122px면 얼굴을 그리기 충분하다. 모델이
17px짜리 정보로 122px 얼굴을 지어냈으니 다른 사람이 나온다.

### 계획에 미치는 영향

`readme.md:41`이 향후 별도 모델로 "virtual tryon, **face swap**" 등을 예고한다.
저자 본인이 얼굴은 이 모델 밖이라고 표시해 둔 것이다.

```
1안 (명소 × 사람)   팀 가정: 쉬움   실제: 얼굴 정체성 구조적 불가
2안 (사람 × 사물)   팀 가정: 어려움  실제: AnyDoor 본령 (object-level)
```

목적이 "내 사진을 넣는다"로 확정됐으므로 A(목표 재정의)는 선택지에서 빠진다.

---

## 2026-09-22 · 2번 검증 — 상반신 크롭이 얼굴을 회복시키는가

**검증 전용. 파이프라인을 수정하지 않는다.** CGIv2 기본 경로는 전신 참조를
그대로 쓴다. `scripts/test_upper_body.py` 신설, `prep.crop_to_face()` 추가.

### 설계 — GPU 를 아끼는 2단계

```
1단계 (GPU 없음)  얼굴 검출 -> 상반신 크롭 -> PairBuilder.build() 로 실제
                  224 참조(item['ref'])를 만들고 그 안 얼굴 높이를 잰다.
                  build() 는 순수 OpenCV 라 GPU 가 없다.
2단계 (GPU)       1단계가 개선을 보일 때만 실제 합성 + SFace 최종 확인.
```

### `prep.crop_to_face()` — 값

```python
def crop_to_face(image, mask, face_box, *,
                 head_room=0.7, torso_ratio=2.6, width_ratio=2.0):
```

| 인자 | 뜻 |
|---|---|
| `head_room` | 정수리 위 여백 = 얼굴 높이 × 이 비율 |
| `torso_ratio` | 크롭 높이 = 얼굴 높이 × 이 비율 (턱 아래로 어깨까지) |
| `width_ratio` | 크롭 폭 = 얼굴 높이 × 이 비율 (얼굴 중심 기준 좌우) |

### 1차 시도 — 관문 탈락

기본값(`0.7 / 2.6 / 2.0`)으로 돌리니 크롭이 너무 타이트해서 **면적 상한
(64%)을 넘겼다.**

| 객체 | 원본→224 | 상반신→224 | 면적 | 관문 |
|---|---:|---:|---:|---|
| F01 | 19px | 49px | — | 통과 |
| F07 | 21px | 49px | **66.55%** | **탈락** |
| F11 | 23px | 48px | **69.84%** | **탈락** |

자동차(면적 상한 문제)와 같은 실패 양상이다. 얼굴은 2.1~2.6배 커졌지만
2/3이 관문에서 막혔다.

### 2차 — 여백 확대로 해결

면적은 크롭 선형 배율의 제곱에 반비례한다. 68% → 목표 35% 근방이려면
배율을 `sqrt(68/35) ≈ 1.39`배 늘리면 된다.

```
head_room    0.7 → 1.0    (×1.39 근사, 반올림)
torso_ratio  2.6 → 3.6
width_ratio  2.0 → 2.8
```

| 객체 | 원본→224 | 상반신→224 | 배율 | 면적 | 관문 |
|---|---:|---:|---:|---:|---|
| F01 | 19px | 39px | ×2.05 | 48.7% | 통과 |
| F07 | 21px | 39px | ×1.86 | 52.5% | 통과 |
| F11 | 23px | 36px | ×1.57 | 51.9% | 통과 |

**3/3 통과. 얼굴이 1.6~2.1배 커졌다.** 여백을 늘린 만큼 배율은 1차 시도보다
낮아졌다 — 면적 관문과 얼굴 크기가 서로 당기는 관계라 이 값이 최선의 절충은
아닐 수 있다. `--head-room --torso-ratio --width-ratio` 로 계속 조정 가능.

### 배치 크기도 줄였다

```
전신 실행 (2026-09-22)   height_ratio = 0.45
상반신 검증              height_ratio = 0.22   (기본값, --height-ratio)
```

전신 크기 틀에 흉상을 욱여넣으면 결과가 왜곡돼 참조 해상도 효과만 순수하게
비교할 수 없다. `normalize_object=False` 로도 뒀다 — 이미 크롭으로 면적을
맞췄으므로 추가 정규화가 끼면 무엇이 효과였는지 섞인다.

### 🐛 venv 충돌 — 스크립트를 3개로 쪼갬

`test_upper_body.py` 하나로 얼굴 검출(YuNet)과 확산 생성을 같이 하려다
**AnyDoor venv 의 cv2 4.7.0 에서 YuNet 이 깨졌다.**

```
cv2.error: ... NaryEltwiseLayerImpl::findCommonShape
  input[0] = [1 64 112 75]
  input[1] = [1 64 112 74]
```

두 갈래 특징맵의 너비가 75 대 74로 하나 어긋난다 — 홀수 입력 폭에서 FPN
두 갈래의 패딩이 어긋나는 구버전 DNN 버그로 보인다. **CGI venv의 cv2
4.11.0에서는 같은 입력으로 정상 동작한다** (`face_score.py` 2026-09-22
실행이 그 증거). 반대로 확산 생성은 `pytorch_lightning`이 있는 AnyDoor
venv에서만 된다. 한 프로세스에 못 넣는다.

`compare_runs.py` / `rescore.py`를 나눴던 것과 같은 이유로 3단계로 쪼갰다.
`scripts/test_upper_body.py`는 폐기하고 즉시 종료하는 안내문으로 남겼다.

```
predict_upper_body.py   1단계  CGI venv     얼굴 검출 + 상반신 크롭 + 예측
generate_upper_body.py  2단계  AnyDoor venv 실제 합성 (얼굴 검출 없음)
score_upper_body.py     3단계  CGI venv     SFace 채점 + 전신 결과와 비교
```

`generate_upper_body.py`가 얼굴 검출을 전혀 안 하는 게 핵심이다 —
`predict_upper_body.py`가 만든 `_bust_img.png` / `_bust_mask.png` / `_tar.png`를
디스크에서 읽기만 하고, `Compositor`가 쓰는 건 AnyDoor 자체의 `mask_score`
등 cv2 기본 연산이라 4.7.0에서도 안전하다.

### 🐛 배경 오매칭 — 다른 사진으로 3장을 만들었다가 폐기

`W03` 하나로 검색되는 파일이 **둘** 있었다.

```
W03_rome-colosseum-pavement_7245244.jpg   4827 x 7232   ← 베이스라인이 쓴 파일
w03_colosseum.jpg                          984 x 1600   ← 다른, 훨씬 작은 사진
```

`predict_upper_body.py`가 `Path.glob(f"{a.background}*")`를 썼는데, **Windows는
파일명 대소문자를 구분하지 않아** `"W03*"`가 둘 다 걸렸다. 정렬도 안 해서
OS 열거 순서에 맡겨졌고, 이번엔 소문자 파일이 뽑혔다. `generate_upper_body.py`
도 같은 방식으로 또 매칭해서 **결과물이 베이스라인과 다른 배경으로 생성됐다.**
3장을 만들고 나서야 `bg_key`가 `w03_colosseum`으로 찍힌 걸 보고 발견했다 —
이전 실행의 `W03_rome-colosseum-pavem`과 달랐다.

`compare_runs.py`의 `pick()`은 이 문제가 없었다 — `sorted()` 뒤에
**대소문자 구분** `str.startswith()`를 쓴다. `"w03_colosseum".startswith("W03")`
는 파이썬에서 `False`다. 그래서 처음부터 대문자 파일만 걸렸다.

**수정**: `pick_one()`을 `compare_runs.py`와 같은 규칙(`sorted()` + 대소문자
구분 `startswith`)으로 다시 구현해 두 스크립트에 적용. 그리고
`generate_upper_body.py`는 이제 **다시 매칭하지 않는다** — `predict_meta.json`
에 `bg_file`(정확한 파일명)을 저장해 그대로 읽는다. 매칭은 1단계에서 한 번만
한다.

**정리**: 잘못된 배경으로 만든 PNG 3장과 그 `generate_meta.json` 삭제.
`_bust_img.png`/`_bust_mask.png`(사람 크롭)는 배경과 무관해 **재사용**했다.
`_tar.png`(배치 마스크)는 `place_box(bg.shape, ...)`로 배경 크기에 의존하므로
삭제 후 올바른 배경으로 1단계를 다시 돌려 재생성했다.

재확인한 예측값은 수정 전과 동일했다(사람 크롭은 배경과 무관하므로 당연하다) —
19→39, 21→39, 23→36px, 면적 48.7/52.5/51.9%, 3/3 통과.

### 실행 값

```
객체            F01, F07, F11
배경            W03_rome-colosseum-pavement_7245244.jpg (4827x7232)
                — 전신 실행(compare_runs.py)과 동일 파일, 직접 비교 가능
steps 50  cfg 5.0  strength 1.0  seed 1234  tar_crop_ratio 2.0
height_ratio 0.22   normalize_object False
head_room 1.0  torso_ratio 3.6  width_ratio 2.8
```

### 결과 — 가설은 절반만 맞았다

```
              전신(이전)   상반신    차이
F01              0.3385   0.2321   -0.1064   ← 오히려 나빠짐
F07             -0.0760   0.0636   +0.1397
F11             -0.0075   0.0960   +0.1035
평균             0.0850   0.1306   +0.0456
```

```
판정선   0.363
상반신   0.131   →  못 넘었다
```

기준선(타인 0.023 / 본인 0.937) 안에서 9% → **11.5%**로 옮겨온 정도다.
얼굴 픽셀은 1.6~2.1배 커졌는데(1단계 예측) 정체성 개선은 그 비율만큼
따라오지 않았다.

**F01은 오히려 나빠졌다.** 전신에서 유일하게 판정선에 근접했던 케이스였다
(0.3385) — 상반신으로 바꾸며 자세·표정·프레이밍이 달라져 그 근접함이
깨졌을 가능성이 있다. 표본 1개라 단정할 수 없다.

### 왜 픽셀 개선이 정체성 개선으로 온전히 안 이어졌나

1단계 예측은 "얼굴이 224 안에서 몇 px 인가"만 쟀다. DINOv2 인코더가 그
픽셀로 무엇을 하는지, ControlNet 힌트(Sobel)가 흉상 실루엣으로 바뀌며 다른
신호를 주는지, 확산이 512 캔버스에 인물을 다시 그리는 과정에서 정체성이
얼마나 전사되는지는 안 쟀다. **정보량 병목(17→39px)은 풀었지만, 그것이
얼굴 정체성 손실의 유일한 원인은 아니었다.**

### 결론

**2번(상반신 크롭) 단독으로는 부족하다.** 방향은 맞다(+0.0456, 3쌍 중 2쌍
개선) 그런데 판정선까지 필요한 폭의 일부만 좁혔다. 3번(원본 얼굴을
정렬해 이식하는 후처리)이 필요하다는 것이 이 측정으로 확인됐다.

---

## 2026-09-22 · 3번 — 얼굴 정체성 복원 (얼굴 이식)

**정식 기능으로 추가했다.** `Settings.face_restore=True` 로 켠다. 기본은
꺼짐. `cgiv2/face_restore.py` 신설, `Compositor`/`Settings`/`_finish()`에 배선.

### 왜 필요했나

1번(얼굴 지표)이 전신 정체성 0.107(판정선 0.363의 9%)을 쟀고, 2번(상반신
크롭)은 얼굴을 1.6~2.1배 키웠는데도 0.131까지만 올랐다. **정보량 병목이
유일한 원인이 아니라, 모델이 얼굴 정체성을 전달하는 경로 자체가 약하다**는
뜻이었다. 그래서 확산이 만든 얼굴을 신뢰하지 않고, AnyDoor 가 잘하는 것
(자세·조명·배경 통합)은 그대로 두고 **얼굴만 원본을 직접 이식**하기로 했다.

### 기법

```
1. YuNet 랜드마크(눈 2·코 1·입꼬리 2)로 참조·생성물 양쪽에서 얼굴을 찾는다.
2. cv2.estimateAffinePartial2D 로 5점 대응 닮음변환(회전+균등스케일+평행이동)을 구한다.
3. 참조 얼굴을 그 변환으로 생성물 좌표계에 워프한다.
4. 타원/실루엣 마스크로 섞는다. 워프된 얼굴을 생성물 얼굴의 LAB 색 통계에 맞춘다.
```

`evaluate.FaceScorer` 의 검출기를 재사용한다 — ONNX 모델을 두 번 안 띄운다.

### 🐛 1차 시도 — 숫자는 좋았는데 육안으로 실패

`face_margin`(생성물 얼굴 bbox 기준 타원 반경 배율)만으로 마스크를 만들었다.

```python
mask = ellipse(center, (fw/2*face_margin, fh/2*face_margin))   # 1차
```

SFace 로 재보니: **0.1131 → 0.9414, 12/12 판정선 통과.** 숫자만 보면 완전
성공이었다.

**육안으로 보니 실패였다.** 얼굴이 경계가 보이는 스티커처럼 붙어 있고, 목과
옷깃이 끊기고, 피부색이 장면 조명과 안 맞았다. `face_margin` 2.6·`feather`
0.4·`blend=poisson` 로 더 풀어봐도 이번엔 머리 둘레에 **흰 안개 같은 halo**
가 생겨 오히려 나빠 보였다.

**원인**: 타원이 얼굴 실루엣을 모른다. 참조 사진의 흰 스튜디오 배경이 타원
안쪽에 같이 들어가 워프됐고, 그게 머리 둘레에 번졌다. `_lab_stats` 로 "워프된
얼굴" 색을 잴 때도 이 배경 픽셀이 섞여 색 매칭 자체가 어긋났다.

**이 사례가 중요한 이유**: SFace 점수(0.94)만 보고 판단했다면 실패를 성공
으로 보고할 뻔했다. 점수는 "타원 안 얼굴이 원본과 같은가"만 쟀지 "자연스럽게
붙었는가"는 재지 않았다. **정량 지표와 육안 확인을 같이 하지 않으면 안 되는
이유가 이것이다.**

### 수정 — 실루엣 교집합

타원 대신, 참조의 **실제 인물 마스크(BiRefNet)** 와 얼굴 주변 ROI 를
교집합해 워프 소스로 쓴다.

```python
roi = 사각형(얼굴 bbox 기준 head_room/torso_ratio/width_ratio 만큼 확장)
src_mask = ref_mask & roi        # 스튜디오 배경은 ref_mask=0 이라 애초에 제외됨
```

`borderMode` 도 `BORDER_REPLICATE` → `BORDER_CONSTANT(0)` 로 바꿨다 — 워프
후 마스크 바깥은 확실히 0이어야 한다.

**재확인 (같은 12쌍)**: SFace 평균 0.1131 → **0.9488**, 12/12 통과 — 숫자는
1차 시도와 비슷했지만, **육안으로 F01·F07·F11 세 장을 확인하니 흰 테두리가
사라지고 목·머리카락 경계가 자연스러웠다.** F11(경복궁)이 특히 좋았다.

남은 흠: 피부·머리색이 장면 조명보다 살짝 밝게 남는 경우가 있다
(`color_match=0.5`로 완전히는 안 맞음). 2D 닮음변환이라 생성물의 얼굴이
참조와 크게 다른 각도(옆모습 등)로 나오면 부자연스러울 수 있는데, 이번
12쌍은 대체로 정면이라 그 경우를 실측하지 못했다.

### 최종 기본값

```python
head_room    = 0.6    # 정수리 위 여백 = 얼굴 높이 x 이 비율
torso_ratio  = 1.3    # ROI 높이 = 얼굴 높이 x 이 비율 (턱 아래로 목까지만 — 크롭보다 훨씬 좁음)
width_ratio  = 1.7    # ROI 폭  = 얼굴 높이 x 이 비율
feather      = 0.10   # 페더 커널 = 생성물 얼굴 높이 x 이 비율
color_match  = 0.5    # 워프된 얼굴을 생성물 얼굴 색에 맞추는 강도
blend        = "feather"   # "poisson" 도 가능
```

`prep.crop_to_face`(2번, `torso_ratio=3.6`)보다 `torso_ratio`가 훨씬 좁다 —
2번은 상반신 전체를 참조로 쓰려는 것이고, 이건 얼굴+목만 이식하는 것이라
범위가 다르다.

### 파이프라인 배선

```python
Settings(face_restore=True, ...)   # 기본 False
Compositor(engine, anydoor_root, face_transplanter=FaceTransplanter(scorer))
                                    # 안 주면 face_restore 켜도 조용히 건너뜀
```

`_finish()` 맨 끝(색 정합·그림자 다음)에서 실행된다. 실패(얼굴 미검출 등)
해도 예외를 던지지 않고 원본 결과를 그대로 쓴다 — 이식은 보강이지 필수
단계가 아니다. `Result.repost()`도 `ref_image`/`ref_mask`/`transplanter`를
받으면 GPU 없이 다시 이식할 수 있다(raw 만으로는 안 됨 — 얼굴 이식은 참조
원본이 필요하다).

와이어링은 실제 GPU 생성으로는 아직 검증하지 않았다 — `_finish()` 시그니처와
`Settings` 필드 접근을 더미 값으로 점검했을 뿐이다(모델 없이 `getattr` 확인).
다음 실제 합성 때 `face_restore=True` 로 한 번 돌려 확인할 것.

### 기술·도구 등록부에 추가

| 기능 | 기술 | 도구 | 등급 |
|---|---|---|:---:|
| 얼굴 정체성 복원 | 5점 랜드마크 닮음변환 + 실루엣 마스크 이식 | `FaceTransplanter` (YuNet+SFace, OpenCV 내장) | 🟢 |

---

## 2026-09-22 · face_restore 프로덕션 배선 검증

### 🐛 사전 점검에서 하드 블로커 재확인

GPU 15~20분을 쓰기 전에 AnyDoor venv 안에서 YuNet 만 먼저 불러봤다.

```python
scorer.detect(참조_1200폭)    # cv2.error: NaryEltwise ... [1 64 112 75] vs [1 64 112 74]
scorer.detect(생성물_1600폭)  # cv2.error: NaryEltwise ... [1 64 149 100] vs [1 64 148 100]
```

**두 크기 다 재현됐다.** 상반신 크롭 검증(2번) 때 겪은 것과 같은 cv2 4.7.0
버그이고, 우연이 아니라 **AnyDoor venv에서 YuNet을 쓰는 한 항상 재현되는
하드 블로커**임이 확인됐다. `Settings(face_restore=True)`를 AnyDoorEngine과
같은 프로세스에서 켜면 안 된다 — 파이프라인에 배선은 해놨지만, **AnyDoor
venv 프로세스 안에서 직접 켜서는 안 된다**는 제약이 문서로 남아야 한다.

### 2단계로 쪼갬

```
gen_keep_raw.py       AnyDoor venv (GPU)   face_restore=False, keep_raw=True
                       raw(512)·extra_sizes·crop_box·배경·미이식 결과를 저장
apply_face_restore.py CGI venv (GPU 없음)   Result.repost() 로 이식 적용
                       AnyDoorEngine 을 전혀 안 쓴다 — repost() 는 순수 후처리
```

`apply_face_restore.py`가 부르는 것은 `FaceTransplanter.transplant()`를
직접 호출하는 게 아니라 **`Settings`→`_finish()`→`Result.repost()`로 이어지는
실제 프로덕션 경로**다. `test_face_transplant.py`(12쌍, 2026-09-22 앞선 절)는
이 경로를 거치지 않고 `FaceTransplanter`를 직접 불렀으므로, 이번이 배선
자체의 첫 검증이다.

### 결과 — F01 × W03(콜로세움)

```
설정   steps=50 cfg=5.0 strength=1.0 seed=1234 tar_crop_ratio=2.0
      normalize_object=True feather=6
      (fh 기본값: head_room 0.6 · torso_ratio 1.3 · width_ratio 1.7 ·
       feather 0.10 · color_match 0.5 · blend feather)

이식 전   0.1642   못 넘었다
이식 후   0.9277   넘었다
```

육안 확인: 흰 테두리 없음, 목·옷깃 연결 자연스러움 — 앞선 절의 실루엣
교집합 수정이 프로덕션 경로에서도 그대로 유효했다.

**참고**: 같은 F01×W03 조합의 "이식 전" 점수가 실행마다 다르다
(0.3385 재채점 / 0.2321 첫 이식 테스트 / 0.1642 이번). seed=1234로
고정해도 CUDA 연산의 미세한 비결정성 때문에 확산 결과 자체가 매 실행마다
조금씩 달라진다. 이식 전/후 비교는 같은 실행 안에서 재는 것이라 결론에는
영향이 없지만, **"seed를 고정했으니 재현된다"고 가정하면 안 된다.**

### 결론

**배선이 실제로 동작한다.** 다만 사용 규칙이 하나 붙는다 — `face_restore`는
AnyDoorEngine을 만든 프로세스에서 직접 켜지 말고, 항상 `keep_raw=True`로
생성한 뒤 별도 CGI venv 프로세스에서 `Result.repost()`로 적용해야 한다.

---

## 2026-09-23 · 배치 위치 — 발은 지면 위에, 크기는 원근에 맞게

`cgiv2/placement.py` · `scripts/check_placement.py` · `scripts/gen_placed.py` 신설.

### 문제

`prep.place_box(center=(0.62, 0.5), height_ratio=0.45)`가 장면을 모른 채 고정
좌표에 박스를 놓았다. 2026-09-21~22의 **모든 결과**에서 인물의 발이 떠 있거나
(콜로세움: 전경 수풀 위), 주변 관광객보다 거인처럼 컸다.

### 방식 결정

사용자에게 "자동 추정 vs UI 클릭"을 물었고 답 없이 진행하게 돼 판단했다 —
**자동 추정으로 하되 UI가 덮어쓸 수 있는 구조**. 이유: 400쌍 같은 배치 테스트는
자동이어야 하고, 최종 제품에서 사용자가 발 위치를 클릭하더라도 **크기(원근)는
어차피 자동 계산이 필요**하다.

### 기법 — 두 갈래

```
어디에 서나   걸을 수 있는 지면을 의미 분할로 찾는다 (ADE20K 150 클래스)
얼마나 크나   장면 속 사람들로 원근을 맞춘다
              지면에 선 사람의 이미지상 키 h 는 발 위치 v 에 선형:  h = r·(v − v0)
              v0 = 지평선 행,  r = 사람 키 / 카메라 높이
```

두 번째는 Hoiem·Efros·Hebert, "Putting Objects in Perspective" (CVPR 2006).
눈높이로 찍은 사진이면 r≈1 — 서 있는 사람들 머리가 전부 지평선에 걸린다.

**사람 수에 따른 대체 사슬** (정확도 순, `info["method"]`에 기록)

| 사람 | 방식 | 계산 |
|---|---|---|
| ≥3명 | `fit` | Theil-Sen 직선 맞춤 (쌍별 기울기 중앙값, 이상치에 강함) |
| 1~2명 | `eye_level` | r=1.0 가정, 지평선 = 머리 윗변 중앙값 |
| 0명 | `ground_top` | r=1.0 가정, 지평선 = 지면 행의 2 백분위 |

`ground_top`은 **작게 치우친다** — 건물이 먼 지면을 가리면 보이는 지면의 윗변
(건물 밑동)이 실제 지평선보다 아래에 있어서다. 페트라처럼 건물이 가까우면
오차가 작고(한 사람 키 정도), 멀면 커진다.

### 모델 선택 — 🐛 첫 선택이 보안 검사에 막혔다

| 시도 | 결과 |
|---|---|
| `nvidia/segformer-b2-finetuned-ade-512-512` | **로딩 거부.** `.bin` 가중치뿐인데 transformers 4.55.4가 torch<2.6 에서 `.bin` 로딩을 막는다 (CVE-2025-32434) |
| torch 업그레이드 | **안 함** — 환경 설정이라 사용자 영역 |
| 보안 검사 우회 (`weights_only=False`로 직접 로드) | **안 함** |
| `facebook/mask2former-swin-small-ade-semantic` | **채택.** safetensors 배포. ADE20K mIoU 약 51 (SegFormer-b2 약 46보다 오히려 높다) |

사람 검출은 `facebook/detr-resnet-50` — HF 캐시에 이미 있었고 safetensors 배포.

### venv 제약 — 또 쪼갬

AnyDoor venv의 transformers 4.19.2에는 **Mask2Former가 없다** (DETR은 있다,
2026-09-23 확인). 배치 계산은 CGI venv에서 하고 `_tar.png`로 저장, AnyDoor
venv가 읽는다. predict/generate를 나눴던 것과 같은 방식.

### 지면 라벨 `WALKABLE`

```
floor · road · grass · sidewalk · earth · rug · field · sand · path · stairs ·
runway · stairway · dirt track · land · step · pier
```

**인덱스가 아니라 라벨 이름으로 매칭**한다 — 모델을 바꿔도 안 깨진다.
`bridge`는 뺐다: 시드니 하버 브리지처럼 "서 있는 곳"이 아니라 배경 구조물로
잡히는 경우가 많다.

### 1차 점검 — 확산 없이 20개 배경에 그려봄

`check_placement.py`가 지면(초록)·사람(파랑)·지평선(빨강)·제안 배치(노랑)를
콘택트 시트로 그린다. **확산을 돌리기 전에 배치가 말이 되는지 본다.**

지면 분할은 거의 완벽했다 — 20장 전부 플라자·산책로·잔디·해변을 정확히 잡고,
콜로세움 전경 수풀은 지면에서 뺐다. 그런데 셋이 틀렸다.

| 🐛 | 예 | 원인 |
|---|---|---|
| **랜드마크를 가림** | W01 에펠탑, W04 피사탑 | 기본 x=0.5. 사진가는 랜드마크를 가운데 둔다 — 최악의 기본값 |
| **기존 사람과 겹침** | K07 골목, K09 해변 | 겹침 회피가 없었다 |
| **앉은 사람이 원근 왜곡 가능** | K09 | 앉은 사람 박스는 키가 절반 |

### 수정

| 수정 | 값 |
|---|---|
| 가로 위치 | **삼등분선** `x_ratios=(1/3, 2/3)`, 후보마다 가장 가까운 자리를 찾아 더 가까운 쪽 |
| 겹침 회피 | 기존 사람 박스와 겹침 비율 ≤ **0.05**. 적분 영상으로 후보 전체를 한 번에 계산 |
| 앉은 사람 제외 | 박스 세로/가로 < **1.5** 면 원근 맞춤에서 뺀다 (서 있는 사람은 보통 2~4) |
| 좌우 잘림 방지 | 박스가 화면 좌우를 벗어나는 후보 제외 |

K09는 수정 후에도 수치가 같았다 — 앉은 두 사람은 원래 화면 아래 가장자리에
닿아(`y2 ≥ H−2` 필터) 이미 빠져 있었다. 앉은 사람 필터는 다른 배경을 위한 안전장치로 둔다.

### 2차 점검 결과

```
배경                       사람  방식        지평선    r     키    면적
K01 경복궁 회랑              0   ground_top   0.54   1.00   40%   5.5%
K02 경복궁 정면              4   eye_level    0.77   1.00   23%   2.0%
K03 경복궁 푸른하늘          0   ground_top   0.59   1.00   40%   3.0%
K04 창덕궁                   0   ground_top   0.81   1.00   19%   1.3%
K05 수원 화성길              2   eye_level    0.42   1.00   40%   2.9%
K06 남산 산책로              6   fit          0.14   0.13   11%   0.4%  ⚠
K07 북촌 골목                1   eye_level    0.53   1.00   40%   7.8%
K08 전주 골목                1   eye_level    0.57   1.00   40%   5.5%
K09 해운대                  15   fit          0.21   0.49   38%   6.1%
K10 사려니숲                 0   ground_top   0.73   1.00   27%   1.4%
W01 에펠탑 광장             22   fit          0.81   2.37   44%   6.6%
W02 루브르 안뜰              1   eye_level    0.72   1.00   28%   3.2%
W03 콜로세움                33   fit          0.58   0.16    6%   0.1%  ⚠
W04 피사                    25   fit          0.85   1.70   26%   2.3%
W05 산토리니                 0   ground_top   0.64   1.00   36%   4.8%
W06 아라시야마 대나무        0   ground_top   0.86   1.00   14%   0.8%  ⚠
W07 대나무길 2               0   ground_top   0.80   1.00   20%   1.6%
W08 페트라                   0   ground_top   0.89   1.00   11%   0.5%  ⚠
W09 브란덴부르크 문         12   fit          0.70   1.13   34%   4.8%
W10 시드니 오페라하우스      0   ground_top   0.88   1.00   12%   0.3%  ⚠
```

육안: W01은 탑 옆 오른쪽 1/3로, K07은 행인 오른쪽으로, K09는 앉은 사람과 안
겹치게 옮겨졌다. K05·W02·W09는 기존 관광객 옆에 비슷한 크기로 선다.

### ⚠ 전신을 크게 넣을 수 없는 배경 5개 — 물리적으로 맞다

K06·W03·W06·W08·W10은 원근상 사람이 **면적 1% 미만**(관문 하한)으로 작게 나온다.
**버그가 아니다.** 높은 데서 내려다봤거나(콜로세움 r=0.16 · 남산 r=0.13 —
카메라가 사람 키의 6~8배 높이) 위로 올려다본(페트라·시드니 · 지평선이 화면
아래 10% 근처) 사진이라, 전신이 발까지 들어가면 작을 수밖에 없다.

K06은 처음에 맞춤 오류로 의심했다. 다시 보니 먼 산 능선이 이미지 위 14%에 있고,
전경의 빨간 옷 행인조차 이미지 높이의 8%라 맞춤이 옳았다.

억지로 키우면 거인이 된다. 이 배경들에서 인물을 크게 넣으려면 **발이 화면
아래로 나가게(다리가 잘리게)** 놓아야 하고, 그러면 참조도 그만큼 위쪽만 잘라
넣어야 한다 — 2번 검증의 상반신 크롭(`prep.crop_to_face`)과 이어지는 방향이다.
다음 과제로 남긴다.

### 기본값 전체

```python
# SceneAnalyzer
SEG_MODEL        = "facebook/mask2former-swin-small-ade-semantic"
DET_MODEL        = "facebook/detr-resnet-50"
det_threshold    = 0.7
labels_present   ≥ 0.01 (면적비)

# fit_perspective
min_h            = 12.0     # px. 이보다 작은 사람은 박스 오차가 키 오차를 삼킨다
min_hw           = 1.5      # 세로/가로. 미만이면 앉은 사람
r_range          = (0.05, 3.0)
v0 허용 범위      = [−1.0·H, 1.2·H]
Theil-Sen        |Δv| > 5 px 쌍만 기울기 계산
fit 조건          ≥3명 (지면 위 발 ≥3명이면 그들만, 아니면 전원)
_feet_on_ground  발 아래 띠 높이 max(4, 0.05·h), 지면 비율 ≥ 0.3

# auto_place
target_height_ratio = 0.40
x_ratios            = (1/3, 2/3)
max_height_ratio    = 0.78     # 관문 최대 변 0.8 회피
min_area            = 0.01     # 관문 면적 하한 — 미만이면 경고만
max_people_overlap  = 0.05
step                = 2        # 후보 픽셀 간격
발 폭 침식           max(3, int(0.12·target_h) | 1) × 5 직사각형

# check_placement.py 실행 값
bg_width 1600 · aspect 0.274 (F01 마스크) · target 0.40 · x (1/3, 2/3)
```

`place_feet()`는 박스 **아랫변**을 발에 맞춘다 — `prep.place_box`는 **중심**을 받아서
지면에 세우는 데 쓸 수 없다.

### 기술·도구 등록부에 추가

| 기능 | 기술 | 도구 | 등급 |
|---|---|---|:---:|
| 지면 분할 | 의미 분할 (ADE20K) | Mask2Former Swin-S | 🟢 |
| 사람 검출 | 객체 검출 (COCO) | DETR ResNet-50 | 🟢 |
| 원근 추정 | 지평선·카메라 높이 (Hoiem 2006) | Theil-Sen + 대체 사슬 | 🟢 |
| 배치 | 지면 제약 + 삼등분선 + 겹침 회피 | `auto_place` | 🟢 |

### 합성 결과 — 발이 땅에 붙었다

방식별로 하나씩 골라 **현재 파이프라인 전체**(새 배치 + 얼굴 이식)로 돌렸다.
객체는 F01. `gen_placed.py`(AnyDoor venv) → `apply_face_restore.py`(CGI venv).

```
설정  steps 50 · cfg 5.0 · strength 1.0 · seed 1234 · tar_crop_ratio 2.0
      normalize_object True · feather 6 · 얼굴 이식 기본값
```

| 배경 | 방식 | 키 | 얼굴 이식 전→후 | 육안 |
|---|---|---:|---|---|
| K05 수원 화성길 | eye_level (2명) | 40% | 0.1802 → 0.8726 | ✅ 걷는 두 관광객 옆에 비슷한 크기 |
| W01 에펠탑 | fit (22명) | 44% | 0.1945 → 0.9483 | ✅ 탑 옆 광장 타일 위. 전형적 기념사진 구도 |
| W05 산토리니 | ground_top | 36% | 0.2479 → 0.9706 | ⚠️ 땅엔 붙었는데 작다 ↓ |
| W09 브란덴부르크 | fit (12명) | 34% | 0.1490 → 0.9461 | ✅ 왼쪽 행인과 비슷한 크기, 기둥 옆 |

**예전 배치(`place_box` 고정)와 달리 4건 모두 발이 지면에 닿았다.** W05는 같은 배경의
예전 결과와 나란히 비교했다 — 예전엔 가운데서 바다 전망을 가렸고, 새 배치는
오른쪽 벽 쪽에 서서 전망을 가리지 않는다.

### 🐛 W05 — 지평선을 너무 낮게 잡았다 → 수정

W05는 사람이 없어 `ground_top`(지면 윗변 = 지평선)을 썼다. 그런데 이 사진은
산책로가 난간에서 끝나고 **그 너머로 바다 수평선이 훤히 보인다.** 진짜 지평선은
바다 수평선인데 산책로 끝을 지평선으로 잡아 인물이 작아졌다.

**원리**: 지평선은 **모든 수평면보다 위**에 있다. 지면뿐 아니라 바다·호수·강도
수평면이다. 보이는 수평면 중 가장 높은 것의 윗변이 지평선의 가장 좋은 추정치
(상한)이고, 바다가 수평선까지 이어지면 그게 정확히 지평선이다.

```python
HORIZON_SURFACES = WALKABLE | {"water", "sea", "lake", "river"}
min_surface      = 0.005        # 이보다 작은 수평면 조각은 뺀다 (물 오인식 점 등)
method 이름      ground_top → surface_top
```

`Scene.surfaces`(지면 + 물) 필드 추가. `surface_top`은 이게 비어 있으면 `ground`로 되돌아간다.

| 배경 | 이전 지평선 | 수정 후 | 키 | 면적 |
|---|---:|---:|---:|---:|
| **W05** | 0.64 (산책로 끝) | **0.46** (바다 수평선) | 36% → **40%** | 4.8% → 5.9% |
| K10 | 0.73 | 0.73 | 27% → 26% | 1.4% → 1.3% |
| 나머지 18개 | 변화 없음 | | | |

W05만 바뀌었다 — 물이 있는 배경 중 사람이 없는 건 W05뿐이다(K09도 `water 6%`가
있지만 사람 15명으로 `fit`을 쓴다). K10의 작은 변화는 `min_surface` 필터가 위쪽의
작은 지면 조각을 빼서 생긴 것이다. 이전 수치는 `work/placement/placement_v1.json`에 보관.

**W05 재합성 (v2)** — 얼굴 이식 0.1886 → **0.9591**. 세 버전 육안 비교:

| 버전 | 지평선 | 머리 위치 | 판정 |
|---|---|---|---|
| 예전 (고정 박스) | — | 섬(수평선) 높이 | 크기는 **우연히** 맞았지만 가운데서 바다 전망을 가림 |
| v1 `ground_top` | 0.64 산책로 끝 | 난간 높이, 수평선보다 아래 | **바로 앞에 선 아이처럼 보임** — 틀림 |
| v2 `surface_top` | 0.46 바다 수평선 | 섬(수평선) 높이 | **복도 끝에 선 성인 크기, 전망도 안 가림** ✅ |

v2는 눈높이 사진의 성질 그대로 머리가 수평선에 걸린다. v1은 지평선을 너무 낮게
잡아 사람을 가깝게 세웠는데 크기가 작으니 아이처럼 보였다. v1 결과는
`outputs/placed/_v1_F01_man-olive-sweater-cr__W05_santorini-walkway_16_restored.png`에 보관.

### 🐛 새로 드러난 문제 — 랜드마크가 저해상도로 재생성된다

W01 원본 해상도에서 **인물 주변에 큰 사각형 경계**가 보였다(x≈440~끝, y≈610~끝).

**원인**: AnyDoor는 512 크롭 **전체**를 다시 그린다. 크롭 = 인물 박스의 1.1배 →
`tar_crop_ratio` 2.0배 → 정사각. 인물이 크면(W01 키 44%) 크롭이 화면의 3분의 2를
덮고, **그 안에 에펠탑이 들어간다.** 탑이 512로 줄어 다시 그려진 뒤 약 3.5배
늘려져 붙는다 — 탑 격자가 뭉개지고 탑 밑 사람들이 일그러진 이유다.

**랜드마크 사진에서 가장 중요한 랜드마크가 저해상도로 재생성되고 있다.** 삼등분선
배치로 인물을 랜드마크 옆에 세우니 오히려 이 문제에 더 걸리기 쉬워졌다.

**배치 문제가 아니라 합성(되붙이기) 문제다.** `crop_back`이 크롭 전체를 되붙이는 게
원인이라, 인물 영역만 되붙이고 나머지는 원본 고해상도 배경을 쓰면 해결된다.
다음 과제로 남긴다 (아래 백로그). → **같은 날 해결 — 바로 아래 절.**

---

## 2026-09-23 · 인물만 되붙이기 — 크롭 안 배경을 원본으로 되돌린다

`cgiv2/paste.py` 신설. `Settings.paste`(`crop` | `box` | `person`), `_finish()`에 배선,
**얼굴 이식 순서를 되붙이기 앞으로 옮김**, `scripts/compare_paste.py`·`scripts/apply_post.py`
신설. 기본값은 `crop`(기존 동작)이고, 배치 합성 3단계(`apply_post.py`)는 `person`을 쓴다.

### 진단 — 문제는 색이 아니라 해상도

배치 검증 4건(F01, 위 절)의 생성 결과를 원본 배경과 비교했다. 일회성 측정 스크립트
(모델 없음, numpy만)로 쟀고, 재는 곳은 **크롭 안(가장자리 8px 제외) ∩ 배치 박스 밖**
(박스를 41×41 사각 커널로 팽창한 것의 밖)이다.

| 배경 | 크롭 면적 | 선명도 (원본 대비) | ΔL | Δa | Δb | 발밑 밝기비 |
|---|---:|---:|---:|---:|---:|---:|
| K05 | 45% | **9%** | +1.46 | +0.05 | +0.98 | 1.143 |
| W01 | 51% | **13%** | −2.59 | −0.21 | +0.21 | 0.883 |
| W05 | 67% | **30%** | −2.14 | −0.27 | +0.56 | 0.918 |
| W09 | 41% | **13%** | +2.50 | −0.18 | +0.57 | 1.233 |

```
선명도      라플라시안 분산 비 (생성 / 원본)
ΔL·Δa·Δb   LAB 평균 차 (생성 − 원본)
발밑 밝기비  가우시안(σ = max(3, int(0.02·키)) | 1)으로 흐린 L 의 비 (생성+1)/(원본+1),
            범위 = 행 [박스 아랫변 − 0.02·키, + 0.06·키], 열 [박스 좌 − 0.2·폭, 우 + 0.2·폭], 박스 제외
```

- **색 차이는 작다** (ΔL ±2.6, Δa·Δb < 1). 색 보정은 필요 없다
- **선명도가 원본의 9~30%로 무너졌다.** 영역을 줄이는 게 답이다
- **발밑은 그림자가 아니라 바닥을 새로 그린 것이다.** 밝기비가 0.88~1.23으로 들쭉날쭉하고
  (1보다 크면 오히려 밝아진 것), 확대해 보면 W01은 타일 배열이 바뀌었고 W09는 자갈이
  매끈해졌다. **그래서 발밑 생성 영역은 가져오지 않는다** — 그림자로 옮길 신호가 못 된다

### 원저자도 데모에서는 막아뒀다

```python
# run_gradio_demo.py:140-143
# keep background unchanged
y1,y2,x1,x2 = item['tar_box_yyxx']      # 배치 마스크 bbox × expand_bbox [1.1, 1.2]
raw_background[y1:y2, x1:x2, :] = tar_image[y1:y2, x1:x2, :]
return raw_background
```

**`run_inference.py`에는 이 처리가 없다.** 우리 `crop_back`은 `run_inference.py`를 따랐다.
원저자도 크롭 전체 되붙이기가 배경을 망친다는 걸 알고 데모에서는 박스 밖을 원본으로
되돌렸다 — 그게 `box` 방식이다.

### 방식 세 가지 — `Settings.paste`

| 방식 | 되붙이는 범위 | 출처 | 필요한 것 |
|---|---|---|---|
| `crop` (기본) | 512 크롭 전체 | `run_inference.py` | 없음 — 기존 동작 그대로 |
| `box` | 배치 박스 bbox × **1.2**, 크롭 안으로 클램프, 가장자리 `feather`px 선형 | `run_gradio_demo.py:140-143` | 없음 — **AnyDoor venv에서도 된다** |
| `person` | 생성물에서 분할한 **인물 알파** | 우리 | 분할 도구 (CGI venv) |

`person`이 실패하면(분할 도구 없음 · 박스 안 인물 미검출) **`box`로 물러나고**
`Result.notes`에 사유를 남긴다. 조용히 넘어가지 않는다.

### `person` 절차 — `paste.person_alpha()` → `estimate_foreground()` → `compose()`

1. **창** — 배치 박스를 인물 키 × `margin` 만큼 사방으로 넓힌다. 가로가 세로 × `min_aspect`
   보다 좁으면 가로를 넓힌다(중심 유지). 크롭과 화면 안으로 클램프.
   **이유**: 분할 모델은 창을 정사각(2048²)으로 늘려 넣는다. 1:3 창이면 사람이 옆으로
   3배 늘어난 채 들어간다
2. **분할** — `masker.alpha(창)` → 0~1 연속 알파. `alpha()`가 없는 도구는 `binary()`
3. **덩어리 선택** — `thresh`로 이진화, 8-연결 성분 중 **면적의 `min_inside` 이상이 배치 박스
   안**인 것만 남긴다. 창에 들어온 다른 관광객·랜드마크를 버리는 단계다
4. **경계** — 남긴 덩어리를 키 × `grow`(최소 1px, 타원 커널)만큼 팽창한 범위 안에서
   **모델의 연속 알파를 그대로** 쓴다 (머리카락 반투명 경계 보존)
5. **전경색 추정** — 경계 픽셀은 `I = αF + (1−α)B_생성`이다. 그대로 얹으면 생성 배경색이
   테두리로 남는다. **Blur-Fusion**(Forte & Pitié, "Approximate Fast Foreground Colour
   Estimation", ICIP 2021)으로 F를 추정한다. 박스 블러 두 번이라 수십 ms
6. **합성** — `out = α·F + (1−α)·B_원본`
7. 이후 단계(`postproc.apply`)의 기준 영역을 **배치 박스 → 인물 실루엣(α > 0.5)** 으로
   바꾼다. 박스에는 이제 원본 배경이 섞여 있어 박스 기준으로 색을 맞추면 원본 픽셀까지 바뀐다

```python
# paste.person_alpha  (Settings.paste_* 로 전달)
margin       = 0.08    # 창 여백 = 인물 키 × 0.08, 사방
min_aspect   = 0.6     # 창 가로 ≥ 창 세로 × 0.6
thresh       = 0.5     # 덩어리 이진화 · 이후 기준 영역
min_inside   = 0.5     # 덩어리 면적의 50% 이상이 박스 안이어야 남김
grow         = 0.01    # 팽창 반경 = 키 × 0.01 (최소 1px), MORPH_ELLIPSE
connectivity = 8

# paste.box_alpha
BOX_EXPAND   = 1.2     # 원본 데모 expand_bbox [1.1, 1.2] 의 상한 — 생성물이 박스를 약간 넘는다
feather      = Settings.feather   # 배치 검증 실행값 6

# paste.estimate_foreground  (Settings.paste_fg = "blur_fusion" | "none")
FG_RADII     = (90, 6) # 두 단계 박스 블러 반경 — 논문 기본값 그대로
eps          = 1e-5
계산 범위     = (알파 > 0) 의 bbox + 90px, 화면 안으로 클램프
```

분할 도구는 `mask.get_masker("birefnet_hr")` — 마스크 생성에 쓰던 **BiRefNet_HR-matting을
그대로 재사용**한다(2048 입력, fp16). 새 모델을 들이지 않았다.

### 🐛 머리 둘레 흰 테두리 — 얼굴 이식 순서를 바꿔 해결

**1차** (`crop_back → 블렌딩 → 되붙이기 → 색 정합/그림자 → 얼굴 이식`, 기존 순서 끝에 되붙이기만
끼움): 배경 선명도는 4건 모두 100%. 그런데 **W09에서 머리·턱 둘레에 흰 테두리**가 생겼다.
원본의 어두운 기둥 앞이라 도드라졌다.

**2차** — 경계 픽셀의 생성 배경색 번짐으로 보고 Blur-Fusion을 넣었다. **줄긴 했지만 남았다.**

**원인** — 되붙이기가 아니라 **얼굴 이식**이었다. `FaceTransplanter`는 참조 실루엣 마스크를
가우시안(커널 = 생성 얼굴 높이 × 0.10)으로 흐려 섞는다. 흐린 가장자리가 **실루엣 밖, 즉 참조
사진의 크림색 스튜디오 배경까지 번진다.** 지금까지는 그 둘레가 AnyDoor가 새로 그린 **밝은**
배경이라 안 보였다. 되붙이기 뒤에 이식하니 원본의 어두운 기둥 위에 번져 드러났다.

**수정** — 순서 변경. 얼굴 이식을 되붙이기 **앞**으로.

```
전  crop_back → 블렌딩 → [되붙이기] → 색 정합/그림자 → 얼굴 이식
후  crop_back → 블렌딩 → 얼굴 이식 → 되붙이기 → 색 정합/그림자
```

- 이식이 **검증했던 조건 그대로**(crop_back 결과 위) 돈다. 테두리는 생성 배경 쪽에 떨어지고,
  되붙이기가 그 배경을 버린다. 4배 확대로 사라진 것을 확인
- 부수 효과: `color_match`·`shadow`가 이제 **이식된 얼굴까지 포함한 인물 전체**에 적용된다.
  둘 다 기본 꺼짐이라 기본 결과는 안 바뀐다 — `crop` 방식 정체성이 배치 절의 값과 소수
  넷째 자리까지 같다 (0.8726 / 0.9483 / 0.9591 / 0.9461)
- `FaceTransplanter` 자체는 안 고쳤다. 가장자리를 실루엣 **안쪽**으로만 흐리는 수정(침식 후
  블러)도 가능하지만, 순서 변경만으로 해결돼 검증된 코드를 건드리지 않았다

### 결과 — 4건 × 4방식 (`scripts/compare_paste.py`)

`gen_placed.py`가 남긴 raw를 `Result.repost()`로 후처리했다 — **확산을 다시 돌리지 않았다.**
네 방식 모두 얼굴 이식을 켰다. `person_nofg`는 `person`에서 Blur-Fusion만 끈 것.

**배경 보존** — 선명도 / 변화량

| 배경 | 크롭 면적 | `crop` | `box` | `person_nofg` | `person` |
|---|---:|---:|---:|---:|---:|
| K05 | 45% | 8.9% / 14.51 | 95.6% / 1.26 | 100.0% / 0.00 | **100.0% / 0.00** |
| W01 | 51% | 13.5% / 8.90 | 95.5% / 1.25 | 100.0% / 0.00 | **100.0% / 0.00** |
| W05 | 67% | 30.8% / 3.69 | 91.1% / 0.53 | 100.0% / 0.00 | **100.0% / 0.00** |
| W09 | 41% | 13.0% / 7.95 | 94.0% / 1.08 | 100.0% / 0.00 | **100.0% / 0.00** |

```
재는 곳    크롭 안(가장자리 8px 제외) ∩ 인물 밖
           인물 = person 알파 > 0.5 를 키 × 0.02(최소 3px) 타원 팽창
           인물 알파는 모든 방식에 공통 — feather 6 crop_back → 얼굴 이식 → person_alpha
선명도      라플라시안 분산 비 (결과 / 원본)
변화량      |결과 − 원본| 평균, RGB, 0~255
```

**정체성** (SFace, 판정선 0.363)

| 배경 | `crop` | `box` | `person_nofg` | `person` |
|---|---:|---:|---:|---:|
| K05 | 0.8726 | 0.8735 | 0.8669 | 0.8628 |
| W01 | 0.9483 | 0.9486 | 0.9493 | 0.9492 |
| W05 | 0.9591 | 0.9593 | 0.9595 | 0.9564 |
| W09 | 0.9461 | 0.9463 | 0.9240 | 0.9406 |

이식 입력이 네 방식 모두 같으므로 차이(최대 0.022)는 채점 때 얼굴을 다시 검출하며 생기는
정렬 차이다. 전부 판정선 통과.

**분할** — 4건 모두 덩어리 1개 남김 · 0개 버림 · 창 가장자리 닿음 없음. 인물 = 화면의
1.9~3.4%. BiRefNet 0.7~1.3초/건(첫 건은 예열 포함), `apply_post.py` 후처리 전체 1.8~2.3초/건.

**육안**

| 배경 | `crop` | `person` |
|---|---|---|
| W01 | 탑 아래 격자 뭉개짐, 관광객 일그러짐, x≈440·y≈610 사각 경계 | 격자·관광객 원본, 경계 없음. 신발 둘레 **보라색 번짐도 사라짐** (생성 배경이라 버려짐) |
| W09 | 기둥 아래 행인이 뭉개진 그림자 | 행인 원본 |
| K05 | 수풀이 흐림 | 잔가지까지 원본. 원본의 볼라드·체인이 인물 **뒤로** 드러남 (물리적으로 맞음) |
| W05 | 바다 질감 흐림 | 바다 질감 원본 |

W05 인물 왼쪽에 겹친 머리 하나와 스웨터 아래쪽 격자 무늬는 **생성 결함**이라 네 방식 모두
같다 — 되붙이기와 무관하다.

### 새로 드러난 것

`crop` 방식에서는 AnyDoor가 크롭을 통째로 다시 그려 **가려지던** 것들이다.

- **접지 그림자가 없다** — `person`은 발밑 생성 영역을 버리므로 AnyDoor가 그린 희미한 어둠
  (W01 발밑 밝기비 하위 10% 0.67, W05 0.80)도 같이 사라진다. 흐린 날(W01)은 자연스럽지만
  볕이 강한 장면에서는 그림자가 있어야 한다. `Settings.shadow`가 이제 **인물 실루엣 기준**으로
  드리우므로 이걸로 검증할 차례다
- **K05 — 발이 연석 모서리에 걸쳤다.** `crop`에서는 AnyDoor가 바닥을 다시 그려 티가 안
  났는데, 원본 바닥이 돌아오며 드러났다. 배치(`auto_place`)가 지면 **경계**(길/잔디, 연석)를
  피하도록 해야 한다
- **원경 인물이 뒤에 겹친다** (W09 어깨 뒤 행인 2명). AnyDoor가 지웠던 사람들이다. 가림
  관계는 물리적으로 맞지만, 배치의 겹침 기준(DETR 박스 5%)이 작은 원경 인물을 못 거른다

### 파이프라인 변경 — 값과 시그니처

```python
_finish(raw, background, region, extra_sizes, crop_box, st,
        ref_image=None, ref_mask=None, transplanter=None,
        masker=None, notes=None)                         # masker · notes 신규
Result.repost(background, st, ref_image=None, ref_mask=None,
              transplanter=None, masker=None)            # masker 신규, 메모는 self.notes 에
Compositor(engine, anydoor_root, face_transplanter=None,
           paste_masker=None)                            # paste_masker 신규
Settings.tag()   paste != "crop" 이면 "_paste-box" / "_paste-person"
                 person 이면서 paste_fg != "blur_fusion" 이면 "-none" 추가
```

기존 스크립트(`run_single`·`run_batch`·`swap_tools`·`gen_keep_raw`·`apply_face_restore` 등)는
`paste` 기본값 `crop` + 후처리 기본 꺼짐이라 **결과가 바뀌지 않는다.**

### 배치 합성 3단계 — 3단계가 바뀌었다

```
1. CGI venv      scripts/check_placement.py                         배치 마스크
2. AnyDoor venv  scripts/gen_placed.py --object F01 --backgrounds …  확산 → raw 저장
3. CGI venv      scripts/apply_post.py                              얼굴 이식 + 인물만 되붙이기  ← 신규
```

- `apply_post.py` — `--work work/placed` · `--out outputs/placed` · `--only` · `--paste person`
  (`crop`|`box`|`person`) · `--mask-tool birefnet_hr`. 산출물 `<키>_final.png`,
  `<키>_final.json`(설정 전체 · 정체성 · 메모 · 소요 시간)
- `gen_placed.py` 마지막 안내문을 `apply_face_restore.py` → `apply_post.py`로 바꿨다
- 예전 `outputs/placed/<키>_restored.png`는 `crop` 방식 결과로 보관한다
- `compare_paste.py` — 산출물 `outputs/pasted/<키>_<방식>.png`, `<키>_sheet.png`(전체 · 디테일 ·
  머리 · 머리카락 경계 · 발, 패널 폭 460), `<키>_alpha.png`, `paste_metrics.json`.
  디테일 창 = 크롭 안 · 인물 밖에서 원본 |라플라시안| 합이 가장 큰 정사각(크롭 짧은 변 × 0.3,
  보폭 max(8, 변/6), 인물 겹침 5% 초과 창 제외)

### `Settings` 전체 기본값 — 2026-09-23 현재

```python
steps            = 50
cfg              = 5.0
control_strength = 1.0
seed             = 1234
shape_control    = False
tar_crop_ratio   = 2.0
normalize_object = True
feather          = 0
color_match      = 0.0
color_tool       = 'lab'          # lab | hist
shadow           = False
mask_tool        = 'birefnet_hr'  # 기록용
blend_tool       = 'feather'      # feather | poisson | poisson_mixed | none
face_restore     = False
face_head_room   = 0.6
face_torso_ratio = 1.3
face_width_ratio = 1.7
face_feather     = 0.10
face_color_match = 0.5
face_blend       = 'feather'      # feather | poisson
paste            = 'crop'         # crop | box | person           ← 신규
paste_margin     = 0.08                                           ← 신규
paste_min_aspect = 0.6                                            ← 신규
paste_thresh     = 0.5                                            ← 신규
paste_min_inside = 0.5                                            ← 신규
paste_grow       = 0.01                                           ← 신규
paste_fg         = 'blur_fusion'  # blur_fusion | none            ← 신규
```

### 기술·도구 등록부에 추가

| 기능 | 기술 | 도구 | 등급 |
|---|---|---|:---:|
| 되붙이기 범위 | 알파 합성 (크롭 / 박스 / 인물) | `paste.py` | 🟢 |
| 인물 분할 (생성물) | 매팅 분할 + 덩어리 선택 | BiRefNet_HR-matting (재사용) | 🟢 |
| 경계 전경색 추정 | Blur-Fusion (Forte & Pitié 2021) | `cv2.blur` | 🟢 |

---

## 2026-09-26 · 그림자 — 접지 그림자 기본, 투영 그림자는 해를 알 때만

`cgiv2/shadow.py` 신설. `Settings.shadow_tool`(`contact` | `cast` | `offset`), `_finish()`에 배선,
`check_placement.py`가 해를 추정해 기록, `apply_post.py --shadow`(기본 `contact`),
`scripts/compare_shadow.py` 신설.

### 왜
`person` 되붙이기가 발밑 생성 영역을 버리면서 AnyDoor가 남긴 희미한 어둠도 사라졌다
(위 절 '새로 드러난 것'). 되살리지 않고 새로 그린다 — 그건 그림자가 아니라 새로 그린 바닥이었다.

### 기존 `offset`은 서 있는 사람에게 못 쓴다
`postproc.add_contact_shadow`는 이름과 달리 **실루엣을 통째로 평행이동**한다(`estimate_light_direction`
방향으로 키 × 0.25). **W01에서 사람 모양 그림자가 하늘에 떴다** — 광원 추정이 위쪽을 가리켜
실루엣이 위로 옮겨졌다. 코드는 남기되 `shadow_tool="offset"`으로만 쓴다.

### 두 종류

| 도구 | 무엇 | 언제 |
|---|---|---|
| `contact` | 접지 그림자 (ambient occlusion). 발바닥이 땅에 닿는 곳의 어둠 | **항상** — 흐린 날·그늘에서도 생긴다 |
| `cast` | 투영 그림자. 해가 몸을 땅에 드리운 것 (+ `contact`) | 해의 방향·길이·색을 알 때만. 틀리면 없느니만 못하다 |

**`contact`** — 발 = 실루엣 맨 아래 키의 4%. 가우시안 타원 두 겹을 곱으로 합친다.

```python
FEET_BAND        = 0.04     # 발 = 실루엣 아래 키 × 0.04
CONTACT_WIDTH    = 1.25     # 넓은 타원 가로 반경 = 발 폭/2 × 1.25   (발 폭 하한 키 × 0.1)
CONTACT_HEIGHT   = 0.03     # 넓은 타원 세로 반경 = 키 × 0.03
CONTACT_CORE     = 0.3      # 좁은 타원: 가로 = 발 폭/2, 세로 = 넓은 것 × 0.3
g = exp(−2·((x−xc)²/a² + (y−y_f)²/b²))           # 타원 중심 = (발 가운데, 발 선)
어둡기 = 1 − (1 − 0.6·s·g_넓은) · (1 − s·g_좁은)    # s = contact_strength = 0.5
계산 범위 = 가로 ±2·a_넓은, 세로 ±3·b_넓은. 인물 자신(마스크)은 어둡게 하지 않는다
```

**`cast`** — 실루엣을 발 선에 붙인 채 땅으로 눕히는 아핀 하나.

```python
x' = x + (y_f − y)·len·dx        # 발(y = y_f)은 제자리
y' = y_f + (y_f − y)·len·dy      # 키 H 인 머리 → 발에서 방향 d 로 H·len
CAST_MIN_DY = 0.08               # |dy| 하한 — 0 이면 특이행렬 (옆으로 지는 그림자)
soft        = (0.002, 0.008)     # 흐림 σ = 키 × (발 쪽, 끝 쪽), 거리 비율 t 로 섞음
fade        = 0.2                # 끝에서 1 − 0.2
결과        = 원본 × (1 − 매트 · (1 − β))      # β = 그림자 속 RGB / 볕 RGB (장면에서 잰 값)
β 가 없으면  1 − cast_strength = 0.55 회색
```

β는 Chuang et al. 2003 "Shadow Matting and Compositing"의 그림자 비율이다. 장면의 기존 그림자에서
재므로 **그림자 색이 장면과 같아진다.**

### 해 추정 — `shadow.estimate_sun()`

사람마다 발에서 사방으로 광선을 쏴 **가장 어두운 방향**을 찾는다.

```python
L          = LAB L, 가우시안 σ 1.5
제외        = 모든 사람 박스 + 3px (자기·남의 몸을 그림자로 착각하지 않게)
기준 밝기   = 발 주변 고리(키 × 0.35~0.9, 반경 12개 × 각도)의 지면 L 중앙값 (표본 ≥ 30)
광선        = 키 × 0.05~0.5, 간격 max(1, 키 × 0.01)px, 각도 5° 간격 (표본 ≥ 8)
어둡기      = 1 − 광선 평균 L / 기준
min_h       = 40px · 발이 화면 아래 끝(H − 2) 이면 제외
dark_min    = 0.3            # 이 이상이면 그 사람이 증거
길이        = 그 방향 키 × 0.05~1.5 프로파일에서 최저점 뒤 어둠이 절반 풀리는 거리 / 키
β           = 그 방향 키 × 0.05 ~ 0.8·길이 (10점) RGB 평균 / 고리 RGB 중앙값, [0.05, 1]
min_evidence      = 2        # 증거 인원
min_concentration = 0.9      # 단위벡터 평균 길이 (≈ 흩어짐 ±25°)
해 = 방향: 원형 평균, 길이·β: 증거의 중앙값
```

**한계** — 우리 인물이 선 자리가 **볕인지 그늘인지는 모른다.** 바닥 재질 차이와 그늘을 밝기만으로
구분할 수 없다(W09 앞마당은 그늘인데 볕 쪽 사람들 그림자가 있으면 해가 잡힌다). 그래서 `cast`는
자동으로 켜지 않는다.

### 결과

**해 검출 — 20개 배경 중 0개.** `check_placement.py` 전체 재실행 기록:

| 배경 | 사람 | 증거 | 판정 |
|---|---:|---:|---|
| K05 | 2 | 1 | 해 없음 — 1명 < 2. **그 1명은 맞았다**: 0°(오른쪽), 어둡기 0.44, 길이 0.53, β ≈ (0.44, 0.47, 0.47). 원본 확대로 커플 오른쪽 그림자 띠 확인 |
| K06 · W04 | 6 · 25 | 1 · 1 | 해 없음 — 1명 |
| W01 (흐림) | 22 | 7 | 해 없음 — 방향 흩어짐 **R 0.49**. 바닥 타일 줄무늬를 그림자로 오인한 7명(165°~185° 다섯, 25° 둘). **집중도 검사가 막았다** |
| W03 | 33 | 6 | 해 없음 — 흩어짐 |
| W09 (역광) | 12 | 4 | 해 없음 — 흩어짐 R 0.50 (220° · 175° · 40° · 190°) |
| 나머지 13 | | 0 | 해 없음 |

배치 수치는 재실행 전후로 **20개 × 8항목 차이 0** (`method`·`v0`·`r`·`height_ratio`·`area`·`box`·`feet`·`n_people`).
이전 기록은 `work/placement/placement_v2.json`에 보관.

**육안 (`compare_shadow.py`, 4건 × none/offset/contact/cast)**

| 도구 | 결과 |
|---|---|
| `none` | 발이 바닥에 얹힌 느낌 |
| `offset` | ❌ W01 하늘에 사람 모양 그림자 |
| `contact` | ✅ 4건 모두 신발 아래·둘레가 은은하게 어두워져 **땅에 닿아 보인다.** 과하지 않다 |
| `cast` | 해 없음 → 4건 모두 `contact`와 같음 |

**K05 투영 그림자 시연** (`--min-evidence 1`, `outputs/shadow_min1/`) — 1명 증거로 해를 인정하면 발에서
오른쪽으로 연석 위에 그림자 띠가 생긴다. 원본 커플 그림자와 방향이 같다.

### 🐛 투영 그림자가 녹아 없어졌다 → 흐림 값 수정

첫 값 `soft=(0.006, 0.03)`, `fade=0.5`로 K05를 돌리니 그림자가 거의 안 보였다(평균 어두워짐 8~11 / 255).
옆으로 지는 그림자는 얇은 띠(키 426 × 길이 0.53 × `CAST_MIN_DY` 0.08 ≈ 18px)인데 σ 12.8px로
흐려 녹았다. **해의 시직경은 0.53°라 반그림자 폭은 거리 × 0.009뿐** — 맑은 날 사람 그림자는 머리
끝까지 거의 선명하다. `soft=(0.002, 0.008)`, `fade=0.2`로 바꾸자 평균 **17.1**, 최대 **62.7**.
연석·풀 위라 원본 커플(밝은 포장) 그림자보다 옅은데, β를 곱하므로 어두운 바닥에서 옅은 게 맞다.

### 결정

- **`apply_post.py` 기본 `--shadow contact`** — 4건 최종본 갱신, 정체성 변화 없음(0.8628 / 0.9492 / 0.9564 / 0.9406)
- `--shadow cast`는 `placement.json`에 해가 있을 때만 그리고, 없으면 `contact` + 메모
- 투영 그림자 자동화는 보류 — **UI에서 광원 방향을 고르게** 하는 쪽이 현실적이다(볕/그늘도 사용자가 안다)

### 파이프라인 변경

```python
# Settings (신규)
shadow_tool      = 'contact'   # contact | cast | offset
contact_strength = 0.5
cast_strength    = 0.45        # β 가 없을 때만
sun              = None        # estimate_sun 결과 dict {dir, len, beta, n, R}
# Settings.tag():  shadow 이면 '_sh-contact' / '_sh-cast' (offset 은 기존대로 '_sh')
# _finish():       shadow_tool 검증 → postproc.apply(shadow = offset 일 때만)
#                  → shadow.apply(contact | cast) — 기준은 post_region (person 이면 실루엣)
```

- `check_placement.py` — 배경마다 `estimate_sun` → `placement.json` 행에 `sun` · `sun_why` · `sun_evidence`,
  표에 `해(dx,dy)` / `해없음(증거 수)` 열
- `gen_placed.py` — meta `placement`에 `sun` 복사 (이후 생성분)
- `apply_post.py` — `--shadow {none,contact,cast}` 기본 `contact`, `--placement`(기본 `work/placement/placement.json`).
  해는 meta → 없으면 `placement.json`의 같은 배경 행에서 찾는다
- `compare_shadow.py` — `--min-evidence`(기본 2), 산출물 `outputs/shadow/<키>_<도구>.png` ·
  `_sheet.png`(전체 + 발 주변 가로 ±0.7·키, 세로 −0.35~+0.3·키, 패널 460) · `_sun.png`(사람 박스 · 증거 화살표) ·
  `shadow_report.json`

### 기술·도구 등록부에 추가

| 기능 | 기술 | 도구 | 등급 |
|---|---|---|:---:|
| 접지 그림자 | 가우시안 타원 2겹 (ambient occlusion 근사) | numpy | 🟢 |
| 투영 그림자 | 평면 투영 아핀 + β 곱 (shadow matting) | `cv2.warpAffine` | 🟢 |
| 해 추정 | 사람 발 광선 탐색 + 원형 평균 | numpy + DETR/Mask2Former 결과 재사용 | 🟢 |

---

## 2026-09-26 · 2안 첫 시도 — 사람 사진에 가방 들리기

지금까지 1안(사람을 명소에)만 했다. 2안은 **배경 = 사람 사진, 객체 = 시계·가방·자동차**다.

### 데이터 — 가방만 있다

`CGI/objects/`에는 사람 사진(F01~F12, p01~p20)뿐이고 시계·가방·자동차가 없다. AnyDoor 예제
(`examples/Gradio/FG` 16장 · `examples/TestDreamBooth/FG` 4장)를 훑어보니 쓸 만한 건
**빨간 백팩 하나**다(`TestDreamBooth/FG/02.png`, 952×1132, 알파 채널 있음). 시계·자동차는
사진이 필요하다.

`scripts/import_rgba.py` 신설 — 알파 PNG → RGB(투명 = 흰색 255, AnyDoor 참조 규약과 같은 색) +
0/255 마스크(알파 > 128).

```
B01_backpack-red-anydoor   952×1132 · 면적 68.8% · 덩어리 2개 (최대 덩어리 100.0%)
→ work/plan2/objects/ · work/plan2/masks/
```

### 방향이 1안과 반대다 — 장면이 아니라 몸을 본다

| | 1안 | 2안 |
|---|---|---|
| 붙이는 것 | 사람 | 물건 |
| 기준 | **장면** — 지면·원근 (`placement.py`) | **몸** — 관절 (`anchor.py`) |
| 가방 | — | 손목에 매단다 |
| 시계 | — | 손목에 감는다 (예정) |
| 자동차 | — | 사람 옆 지면 — 1안 배치를 재사용할 수 있다 (예정) |

### `cgiv2/anchor.py` — 몸 기준 배치

**관절 추정 도구 — torchvision Keypoint R-CNN ResNet-50 FPN** (COCO 17점).
- CGI venv에 이미 있는 torchvision으로 돈다 — **새 패키지가 없다**
- 가중치가 `.pth`라 transformers의 `torch.load` 보안 검사(CVE-2025-32434)와 무관하다
  (`keypointrcnn_resnet50_fpn_coco-fc266e95.pth`, 첫 실행에 download.pytorch.org에서 받음)
- ViTPose(transformers) 등으로 갈아끼울 수 있다 🟢

```python
PoseEstimator(device="cuda", det_threshold=0.8)   # 사람 박스 점수 기준
main_person()      가장 큰 박스 한 명
KP_MIN_SCORE = 2.0 # 관절 신뢰 기준. 점수는 확률이 아니라 히트맵 로짓 — torchvision 예제 시각화 기준

bag_in_hand(person, aspect, image_shape, size=0.26, grip=0.03, drop=0.08, side="auto")
  size   가방 높이 / 사람 키 — 백팩 약 45cm / 키 175cm ≈ 0.26
  grip   박스 윗변 = 손목 y − 키 × 0.03 (손이 손잡이를 쥐는 높이)
  drop   팔이 내려왔다 = 손목이 팔꿈치보다 키 × 0.08 이상 아래
  side   auto = 내려온 팔 중 몸 중심(엉덩이·어깨 x 평균)에서 더 먼 손
  가로    손목 x 가 가운데, 가로 = 높이 × 물건 가로세로비
  사람 키 = Keypoint R-CNN 사람 박스 높이
```

### `scripts/check_anchor.py` — 2안 1단계

사람 사진마다 관절 → 물건 박스 → 관문 검사 → `placement.json`·`_tar.png`·`_overlay.png`·`sheet.png`.
**산출물 형식이 `check_placement.py`와 같아 2단계 `gen_placed.py`가 그대로 읽는다.**
`--silhouette`는 배치 마스크를 사각형 대신 물건 실루엣으로 만든다 — **`shape_control`은 사각
마스크면 효과가 없다**(`pairs.build`가 `cropped_tar_mask`를 그대로 쓰므로). 실루엣을 줘야 따른다.

**배치 결과** (배경 폭 1600, 물건 가로세로비 0.841):

| 배경 | 손 | 사람 키 | 가방 (폭×높이) | 면적 | 관문 |
|---|---|---:|---:|---:|---|
| F03 남·블레이저 | 왼손 | 1966px | 430×511 | 6.0% | 통과 |
| F04 남·정장 | 왼손 | 2239px | 490×582 | 7.4% | 통과 |
| F12 여·카디건 | 오른손 | 1718px | 376×447 | 4.4% | 통과 |

F03·F04·F12를 고른 이유 — 12장 중 팔이 몸 옆으로 내려와 손이 보이는 사진이다(F01·F05는 주머니,
F07·F09는 팔을 든 자세).

### 흐름 — 1안과 같은 3단계, 옵션만 다르다

```
1. CGI venv      check_anchor.py --object B01 --only F03 F04 F12
2. AnyDoor venv  gen_placed.py --placement work/plan2/anchor --bg-dir <CGI/objects>
                   --obj-dir work/plan2/objects --mask-dir work/plan2/masks
                   --object B01 --backgrounds F03 F04 F12 --out work/plan2/gen
3. CGI venv      apply_post.py --work work/plan2/gen --out outputs/plan2 --paste box
                   --shadow none --no-face --obj-dir work/plan2/objects --mask-dir work/plan2/masks
```

- `gen_placed.py` — `--shape-control` 추가, meta `settings`에 `shape_control` 기록
- `apply_post.py` — `--no-face` 추가(2안은 사람이 배경이라 얼굴이 원본 그대로), meta의
  `shape_control`을 `Settings`로 넘김
- 3단계 `--paste box` — 가방은 사람 몸 앞에 붙으므로 `person` 분할이 사람+가방을 한 덩어리로 잡아
  박스 밖으로 넘친다(덩어리 선택에서 탈락 → `box`로 물러남). `--shadow none` — 손에 든 가방은
  땅에 닿지 않는다(`contact`는 박스 아랫변을 발로 본다)

### 기술·도구 등록부에 추가

| 기능 | 기술 | 도구 | 등급 |
|---|---|---|:---:|
| 관절 추정 (2안 배치) | 2단계 검출 + 키포인트 히트맵 | torchvision Keypoint R-CNN R50-FPN | 🟢 |
| 몸 기준 배치 | 손목·팔꿈치 규칙 | `anchor.bag_in_hand` | 🟢 |
| 알파 PNG 가져오기 | 알파 > 128 이진화, 투명 → 흰색 | `import_rgba.py` | 🟢 |

### 결과 — 가방 자체는 잘 옮겨졌다

```
2단계  steps 50 · cfg 5.0 · strength 1.0 · seed 1234 · tar_crop_ratio 2.0 · normalize_object True
       feather 6 · shape_control False (사각 박스)
       모델 로딩 119.1초 + 3건 1.7분 (건당 약 0.6분)
3단계  --shadow none --no-face, 되붙이기 crop / box / person 셋 다
```

**객체 정체성 — 좋다.** 버건디 색, 앞 지퍼 주머니, 컬러 패치, 옆 스트랩까지 참조와 같다. 사람 얼굴(1안
0.107)과 정반대 — AnyDoor는 **물건 수준 모델**이라 원래 이걸 잘한다.

**되붙이기 — `person` 분할이 물건에도 통한다.** BiRefNet이 창 안에서 가장 눈에 띄는 빨간 가방을 잡았다.

| 방식 | 바뀐 면적 (화면 대비) | 박스 밖에서 바뀐 면적 | 육안 |
|---|---:|---:|---|
| `crop` | 9.6~19.7% | **4.6~14.2%** | 밝은 그라데이션 배경(F03)에 사각 경계가 옅게 보인다. 옷도 다시 그려짐 |
| `box` | 5.1~6.9% | 0.7~1.2% | 박스 밖으로 나간 **스트랩이 잘린다**(F04), 박스 가장자리 이음매 |
| `person` | 3.7~5.7% | **0.2~0.5%** | 가방 실루엣만 바뀜. 스트랩 온전. F03 가방 왼쪽 아래 흰 점 하나 |

(변화 = 원본과 RGB 최대차 > 6. `person`은 3건 모두 "창 가장자리 닿음" 메모 — 가방 스트랩이 창 끝까지 뻗은
것으로, 바뀐 영역을 그려보면 가방 모양 그대로다.)

**2안에서 `person`이라는 이름은 헷갈려서 `paste="object"`를 별칭으로 추가했다**(동작 같음). `apply_post.py`
`--paste`에도 추가.

**손 — 반만 맞았다.**

| 배경 | 결과 |
|---|---|
| F04 | 가방 윗부분이 왼손을 덮어 **"뒤에서 손잡이를 쥔" 모습**으로 읽힌다. 가장 자연스럽다 |
| F03 | 같은 방식(왼손을 덮음). 다만 **오른손**이 가방 바로 옆에 보여 떠 있는 듯한 인상 |
| F12 | ❌ 원본을 확대하니 **두 손이 카디건 주머니 안**이었다. 손목이 아래로 내려와 "팔이 내려옴" 기준을 통과했지만, 주머니 속 손으로 가방을 들 수 없어 치마 앞에 떴다 |

### 🐛 주머니 손 → 규칙 추가

관절 좌표로 구분된다. 주머니 손은 **팔뚝이 몸 쪽으로 꺾이고 손목이 엉덩이보다 위**에 있다.

| | 팔뚝 기울기 (몸 쪽 +) | 손목이 엉덩이보다 위 (키 대비) | 판정 |
|---|---:|---:|---|
| F03 왼손 | −5.8° | 0.005 | 통과 |
| F04 왼손 | −8.1° | 0.032 | 통과 |
| F12 오른손 | **+22°** | **0.075** | 주머니 손 |
| F12 왼손 | — | — | 팔이 안 내려옴 |

```python
bag_in_hand(..., max_tilt=15.0, max_above_hip=0.05)
# 팔뚝(팔꿈치→손목)이 수직에서 몸 쪽으로 15° 넘게 기울거나
# 손목이 같은 쪽 엉덩이 관절보다 키 × 0.05 넘게 위면 탈락. 사유는 info["rejected"]
```

재실행 결과 F12는 **"가방을 들 수 있는 손이 없음"**으로 빠지고 F03·F04 박스는 그대로다(이전 기록
`work/plan2/anchor/placement_v1.json`). 산출물은 `outputs/plan2/{crop,box,person}/`.

### 남은 것

- **손이 가방을 쥐는 모습** — AnyDoor는 손-물건 상호작용을 그리지 않는다. 지금은 손을 가방으로 덮어
  가린다. `grip`을 음수로(손가락 아래에서 가방 시작) 두는 실험, 어깨에 멘 모습(`crossbody`) 기준점
- **시계·자동차** — 사진이 없다. 시계는 손목 박스가 화면의 1%에 못 미치므로(키 2000px에서 약 70×70px
  = 0.13%) **손목 주변을 잘라 그 안에서 합성한 뒤 되붙이는** 방식이 필요하다. 자동차는 1안 배치
  (지면 + 원근)를 재사용해 사람 옆 지면에 세운다
- `shape_control` + `--silhouette` — 가방은 모양이 이미 잘 유지돼 안 돌렸다. 강체(시계·자동차)에서 시험

---

## 2026-09-26 · 2안 시계·자동차

### 데이터 — Unsplash에서 검색과 받기를 나눠 수집

`scripts/fetch_objects.py` 신설. 1안 수집(`AnyDoor/data_test/fetch_unsplash.py`)과 같은 경로
(napi 검색, API 키 없음, curl — 파이썬 urllib는 401)지만 **두 단계로 나눴다.**

```
search   후보 목록만 — 이미지는 안 받고 크기는 HEAD 요청으로 잰다 → work/plan2/raw/_candidates.json
get      사람이 고른 것만 받는다 → work/plan2/raw/<이름>.jpg + _credits.json
받는 폭   1200px (q=85, jpg)
제외      Unsplash+ (premium/plus) — 유료
검색어    watch: "wristwatch isolated white background", "analog watch product photo white background" (squarish)
          car:   "car isolated white background", "car studio side view white background" (landscape)
          질의당 8장 → 후보 40장 (시계 18 · 자동차 22)
```

자동차 후보 22장 중 **절반 가까이가 장난감·축소 모형**이었다. 설명(alt)으로 걸러 6장을 골라 사용자
승인 후 받았다(총 777KB). 받은 뒤 확인:

| 파일 | 크기 | 판정 |
|---|---:|---|
| `A01_watch-silver-bracelet` | 280KB | ✅ 정면, 전체, 옅은 하늘색 천 배경 |
| `A02_watch-white-leather` | 156KB | ⚠️ **뚜껑이 열린 점자 시계** + 가죽 지갑 위 — 일반 손목시계가 아니라 제외 |
| `A03_watch-black-minimal` | 177KB | ✅ 비스듬히 누움, 한쪽 줄이 화면 밖으로 잘림 |
| `C01_car-white-sedan` | 56KB | ✅ 옆모습, 흰 배경 (모형 같지만 실차처럼 보임) |
| `C02_car-white-room` | 54KB | ⚠️ **위에서 내려다본 각도** — 눈높이 사진 지면에 세우면 원근이 안 맞아 제외 |
| `C03_car-yellow-sports` | 54KB | ✅ 스튜디오 뒷모습 |

마스크 — `make_masks.py --src work/plan2/raw --out work/plan2/masks --names A01 A03 C01 C03 --save-alpha`
(BiRefNet_HR-matting, 1안과 같은 도구):

| | 크기 | 면적 | 연결성 | 가로세로비 |
|---|---|---:|---:|---:|
| A01 | 1200×1200 | 8.8% | 1.00 | 0.461 |
| A03 | 1200×1214 | 22.9% | 0.99 | 1.317 |
| C01 | 1200×900 | 11.5% | 1.00 | 2.750 |
| C03 | 1200×675 | 16.9% | 1.00 | 1.282 |

4장 모두 관문 통과. A03은 줄 아래 작은 그림자 조각이 섞였다(미미).

### 자동차 — 1안 배치를 그대로 쓴다

2안 자동차는 "사람이 있는 장면에 차"다. 사람 사진(스튜디오)보다 **사람이 있는 거리**가 맞다.
1안 배경 중 **실제로 차가 다니는 골목** K08(전주, 이미 주차된 차들 + 사람 1)·K07(북촌, 사람 1)을 골랐다.

크기는 원근이 준다 — 그 자리 사람 키 × (차 높이 / 사람 키). `check_placement.py --height-scale` 추가:

```python
obj_persp = dataclasses.replace(persp, r=persp.r * height_scale)   # 지평선 v0 는 그대로
# 세단 1.45m / 1.70m ≈ 0.85 (C01),  스포츠카 1.29m / 1.70m ≈ 0.76 (C03)
check_placement.py --only K07 K08 --aspect <차> --height-scale <비> --target 0.22 --out work/plan2/car_<차>
```

| | 결과 |
|---|---|
| C01 × K07 | ❌ "기존 사람과 겹치지 않는 자리가 없다" — 좁은 골목에 옆모습 차(가로 2.75배)가 안 들어간다 |
| C01 × K08 | 높이 20% · 면적 14.2% — 길을 가로지르는 배치, **오른쪽 주차 차량과 겹침**(배치는 사람만 피한다) |
| C03 × K07 | 높이 18% · 면적 7.5% — 여자 오른쪽 담장 앞. 여자 키의 약 0.7배 |
| C03 × K08 | 높이 22% · 면적 7.8% — 오른쪽 차선, 멀어지는 뒷모습. **가장 자연스럽다.** 기존 검은 차와 살짝 겹치지만 우리 차가 앞(아랫변 더 아래)이라 가림 순서가 맞다 |

### 시계 — 손목 둘레 부분 이미지 + 돌린 시계 머리

시계는 가방보다 세 가지가 더 어렵다.

1. **크기** — 전신 사진에서 문자판 약 40px, 박스 면적 ≈ 0.1%. AnyDoor 면적 관문(1%) 아래다.
   이 관문은 학습 때 너무 작은 물체를 거르던 것이고, 추론의 실제 제약은 512 크롭의 해상도다.
   → **손목 둘레 정사각 부분 이미지**(박스 긴 변 × 6, 박스 면적 ≈ 1/36 ≈ 2.8%)를 배경으로 합성하고
   3단계가 원래 사진 제자리에 되붙인다(`anchor.zoom_box`, `apply_post.py`의 zoom 처리)
2. **방향** — 줄은 손목을 **감는다.** 이미지에서 줄 축 ⟂ 팔뚝이어야 한다
3. **보이는 부분** — 감긴 줄은 손목 뒤로 돌아가 안 보인다. 제품 사진처럼 줄을 다 펼친 채 넣으면
   팔 위에 시계를 납작하게 얹은 모양이 된다

```python
watch_head(ref_rgb, ref_mask, keep=0.75)
  줄 축 = 마스크 주축 (PCA, np.linalg.eigh)  → rotate_bound 로 가로로 눕힘 (캔버스 확장, 흰색 채움)
  문자판 = 주축 방향 폭 프로파일(가우시안 폭 = 길이 × 0.03 | 1)의 최댓값 위치, 그 폭 = 지름 D
  남기는 범위 = 주축 방향 ±0.75·D  (1.5·D ≈ 손목 폭 6cm / 문자판 4cm)

watch_on_wrist(person, head_shape, image_shape, face=0.023, offset=0.012, side="auto")
  손목   auto = 왼손목(관례) 먼저, 안 되면 오른손목 (손목·팔꿈치 점수 ≥ 2)
  u      팔꿈치 → 손목 단위벡터,  n = (−u_y, u_x) = 줄 축
  중심   손목 − u · 키 × 0.012 (≈ 2cm 팔꿈치 쪽 — 손목뼈 바로 위)
  크기   머리 세로(팔뚝 방향) = 문자판 지름 = 키 × 0.023 (4cm / 175cm)
  회전   atan2(−n_y, n_x) — 머리의 가로축을 n 에 맞춘다 (cv2 는 반시계 +)
  박스   돌린 머리 사각형의 축 정렬 bbox

zoom_box(box, image_shape, factor=6.0)   정사각, 화면 안으로 밀어 넣음
```

**참조가 배경마다 다르다**(팔뚝 각도가 다르므로). 파이프라인이 한 물건 = 한 참조를 가정해서 두 곳을 넓혔다:
- `check_anchor.py --kind watch` — 배경마다 `<배경>_ref.png`·`_ref_mask.png`(돌린 머리), `<배경>_zoom.png`(부분 이미지),
  행에 `ref_file`·`ref_mask_file`·`zoom {full_bg_file, box, full_size}`·`full_box`
- `gen_placed.py` — 행에 `ref_file`이 있으면 그 참조를 쓴다. meta에 `ref_path`·`ref_mask_path`(절대 경로),
  `placement.zoom` 기록 (차 실행 도중 수정 — 행에 `ref_file`이 없으면 기존과 같은 경로라 영향 없음)
- `apply_post.py` — meta의 `ref_path` 우선, `placement.zoom`이 있으면 결과를 `--full-bg-dir`(기본
  `CGI/objects`)의 원래 사진 제자리에 되붙인다. 부분 이미지 결과는 `<키>_final_zoom.png`

### 🐛 시계가 정장 소매 위에 올라갔다 → 손목 점 보정

첫 배치(offset +0.012, keep 0.75)를 부분 이미지에 그려보니 **4건 모두 박스가 소매 위**였다. 생성을
시작한 뒤 발견해 **중단**(`TaskStop`)하고 고쳤다 — 소매 위 시계를 만드는 데 GPU를 쓸 이유가 없다.

- **Keypoint R-CNN 손목 점이 실제 손목이 아니라 소매 끝(커프스)에 찍힌다.** F03·F04에서 실제 손목보다
  키 × 0.02~0.03 위. 거기서 팔꿈치 쪽으로 키 × 0.012를 더 올렸으니 소매 한가운데가 됐다
- F04는 소매 끝 바로 아래 **이미 금속 장신구**(시계 또는 팔찌)를 차고 있었다 — 바로 그 자리가 정답

```python
watch_on_wrist(offset = +0.012 → −0.025)   # 음수 = 손 쪽. 소매 끝 바로 아래 드러난 손목
watch_head(keep = 0.75 → 0.6)              # 박스 77px > F04 손목 폭 53px(키 × 0.024) → 1.2·D
check_anchor.py --offset --keep             # 명령줄로도 뺐다
```

재배치: F04 = 드러난 손목(원래 장신구 자리) ✅, F03 = 소매가 손목을 덮어 소매 끝과 손등 경계(시계가
소매 밖으로 살짝 나온 모습). 부분 이미지 336~402px, 박스 면적 2.4~2.5%, 관문 통과.

```
시계 머리  A01: 주축 93.3° · 문자판 지름 296px · 머리 355×300
           A03: 주축 −154.4° · 문자판 지름 374px · 머리 449×389
배치       문자판 F03 45px · F04 52px, 회전 −174° / −172° (늘어뜨린 팔 → 줄 축 ≈ 가로)
```

### 자동차 결과

```
2단계  3건 — C01×K08 3.3분 · C03×K07 3.2분 · C03×K08 3.3분 (각 모델 로딩 약 110초 별도)
3단계  --paste object --shadow contact --no-face (접지 그림자 기본값 — 사람용)
```

| 조합 | 결과 |
|---|---|
| **C03 × K08** | ✅ 가장 자연스럽다. 오른쪽 차선을 멀어지는 뒷모습, 크기·차선 위치 맞음, 기존 검은 차 앞(가림 순서 맞음) |
| C03 × K07 | △ 원근상 크기는 맞는데(여자 키의 약 0.7배) **사람에 너무 붙었다** — 배치의 겹침 기준 5%는 통과 |
| C01 × K08 | △ 차 재현은 좋은데 **차체 밑으로 밝은 바닥이 보여 떠 보인다.** 오른쪽 주차 차량을 가린다 |

공통 한계 둘:
- **조명** — 참조가 스튜디오 사진이라 볕 드는 거리에서 차가 고르게 밝다(특히 흰 세단). AnyDoor의 조화가 부족
- **접지** — 접지 그림자 기본값(두께 = 높이 × 0.03)은 **사람 발 두 개** 기준이라 차에는 얇다. 실제 차는
  차체 밑 전체가 어둡다

접지 그림자 폭·두께를 `Settings`로 뺐다(`contact_width` 1.25 · `contact_height` 0.03 기본 — 사람 결과 불변).
`shadow.contact_shadow(width, height)`, `shadow.apply(contact_width, contact_height)`, `apply_post.py`
`--contact-strength` · `--contact-width` · `--contact-height` · `--color-match` 추가.

**자동차 접지 그림자 비교** (3건 모두, 확산 재실행 없이 3단계만):

| 변형 | 값 (strength / width / height, color_match) | 결과 |
|---|---|---|
| v1 | 0.5 / 1.25 / 0.03, 0 (사람 기본값) | 차체 밑으로 밝은 바닥 — **떠 보임** |
| **v2** | **0.7 / 1.05 / 0.08, 0** | ✅ 차체 밑 전체가 어두워져 **땅에 붙음**. 3건 모두 개선 |
| v3 | 0.7 / 1.05 / 0.08, **0.3** | ❌ 노란 차가 **탁한 올리브색**으로 — 둘레 배경(회색 아스팔트·녹음) 통계로 끌려감. **제품 색이 바뀌므로 2안 금지** |

→ **자동차 권장값: `--contact-strength 0.7 --contact-width 1.05 --contact-height 0.08`**, 색 정합 없음.
산출물 `outputs/plan2/{car, car_v2, car_v3}/`.

### 시계 결과

```
2단계  4건 — A01×F03 3.4분 · A01×F04 3.4분(누적 6.8) · A03×F03 3.2분 · A03×F04 약 3.3분 (각 모델 로딩 약 110초 별도)
3단계  --paste object --shadow none --no-face (zoom 되붙이기 자동)
```

🐛 **3단계 첫 실행이 모델 로딩 중 네이티브 크래시**(종료 코드 0xC0000409). 2단계 AnyDoor 프로세스가
끝난 **직후** 시작해 GPU 해제와 겹친 것으로 보인다 — 바로 뒤 자동차 3단계 두 번은 같은 모델을 정상
로딩했고, 같은 명령 재실행도 정상 종료. **2단계 직후 3단계를 이어 붙일 때는 몇 초 간격을 둘 것.**

| 조합 | 결과 |
|---|---|
| A01 × F04 | △+ **전신 크기에서는 손목에 찬 것처럼 보인다.** 확대하면 손등 쪽으로 조금 내려와 얹힌 느낌이고, **원래 팔찌가 소매 끝에 그대로 남아** 장신구가 둘이다. 손목은 옆모습인데 문자판은 정면(참조 사진 각도 그대로) |
| A03 × F04 | △+ 같은 양상 — 검은 시계 |
| A01 × F03 | △ 소매 끝과 손등 경계 — 시계가 소매 밖으로 살짝 나온 모습 |
| A03 × F03 | △ 같은 자리, 문자판이 소매 끝에 얹힌 듯 |

처음엔 F04 두 건을 ✅로 적었다가 확대 비교(`outputs/report/p2_watch.jpg`)를 보고 고쳤다.
다음 손볼 곳: `offset` −0.025 → −0.015 정도로 소매 쪽에 붙이기, 기존 장신구를 박스에 넣어 **교체**하기,
옆모습 손목이면 참조도 옆으로 기운 시계 사진을 쓰기.

- `object` 분할이 시계에도 통했다 — 4건 모두 `box`로 물러나지 않음(A03×F04만 "창 가장자리 닿음")
- 세부 색은 조금 바뀐다 — A01 갈색 문자판이 더 어둡게. 전신 사진에서 문자판이 45~52px라 눈에 잘 띄지 않는다
- **드러난 손목이 있는 사진이 관건이다.** 소매가 손목을 덮은 F03은 어색하다

---

## 2026-09-28 · 진행 보고서 (Word)

1안·2안 전체 진행을 Word 문서 하나로 정리했다. HTML 페이지로 먼저 만들었다가 사용자 요청으로 Word로 바꿨다.

```
원본       docs/build_report.js        (docx npm — 이 스크립트가 원본, .docx 는 산출물)
그림       outputs/report/*.jpg        10장 (p1_face · p1_place · p1_paste · p1_shadow · p1_final ·
                                             p2_refs · p2_bag · p2_car · p2_car_shadow · p2_watch)
산출물     Downloads/CGIv2_진행보고서.docx (1,206KB) · 사본 outputs/report/CGIv2_진행보고서.docx
실행       set NODE_PATH=<docx 가 설치된 node_modules>
           node docs/build_report.js <출력.docx>
구성       A4 · 여백 2cm · 맑은 고딕 · 8장(설계 원칙 · 파이프라인 · 1안 · 2안 · 숫자 · 남은 과제 · 실행 · 기록)
           표 8 · 그림 10 · 쪽 번호 바닥글
```

검증 — 문서 구조는 파이썬 표준 라이브러리로 확인했다(XML 19파트 형식 오류 없음, 제목1 8 · 제목2 3 · 표 8 ·
그림 10). **화면 렌더링은 못 봤다.** LibreOffice·pdftoppm이 없어 Word(COM, 창 없이)로 PDF를 뽑으려 했는데
5분 넘게 멈춰 종료했다. CPU를 계속 쓰면서 아무 창 제목도 없어, 보이지 않는 첫 실행·라이선스 창을 기다린
것으로 보인다(`scratchpad/docgen/docx_to_png.ps1` — Word PDF 내보내기 + Windows.Data.Pdf 페이지 PNG).

---

## 2026-09-29 · git 첫 등록과 인계 문서

다른 PC나 새 대화에서 이어가려고 CGIv2를 처음으로 git에 올렸다 (`JungUH-0/JungPra`, `main`).
코드 변경은 없다.

| 파일 | 내용 |
|---|---|
| `HANDOFF.md` | 2026-09-23 ~ 09-29 대화 요약 · 작업 규칙 · 결정 대기 (학습 방향) · 다른 PC로 옮기는 방법 |
| `.gitignore` | `outputs/` (436MB) · `work/` (324MB) 제외 |
| `env/cgi-venv.txt` | CGI venv 설치 목록, 패키지 83개 |
| `env/anydoor-venv.txt` | AnyDoor venv 설치 목록, 패키지 125개 |

- 두 venv 모두 uv로 만든 Python 3.10.20이고 **pip가 없다.** 그래서 `pip freeze` 대신
  `importlib.metadata.distributions()`로 `이름==버전`을 읽었다. 첫 줄은 `# Python 3.10.20` 주석이다.
- CGI 쪽 파일 두 개를 함께 올렸다. 환경을 다시 만들 때 필요하다.
  `CGI/_anydoor_backup/anydoor_10gb_fixes.patch` (AnyDoor 원본 커밋 `44ca2b2a`에 거는 10GB 패치)와
  그 설명 `CGI/docs/anydoor_local_10gb.md`.
- 가중치 (`CGI/AnyDoor/path/` 14GB) · 사진 · 얼굴 모델 (`work/models/`) · 생성물은 git에 없다.
  목록과 옮기는 법은 `HANDOFF.md`의 "환경과 데이터".

---

## 다음에 할 것

- [x] `scripts/rescore.py` — 저장된 PNG를 BiRefNet으로 재분할 후 `cutout` 기반 재채점
- [x] 비교 실행 완료 후 `rescore.py` 돌리기 — 정체성 0.85~0.88 확인 (기준선 내 72~78%)
- [x] `compare/` 9장 육안 확인
- [x] 얼굴 지표 추가 (1번) — SFace, 전신 정체성 0.107 확인 (판정선 0.363의 9%)
- [x] 상반신 크롭 실험 (2번) — 얼굴 1.6~2.1배 키웠으나 0.131까지만 (부족)
- [x] 얼굴 정체성 복원 (3번) — 이식으로 0.9488, 12/12 판정선 통과, 육안 확인 완료
- [x] **face_restore 를 실제 GPU 생성 파이프라인에서 검증** — 2026-09-22 완료.
      `Settings(face_restore=True)` 를 AnyDoorEngine 과 같은 프로세스에서 켜면
      **크래시한다**(아래). `gen_keep_raw.py`/`apply_face_restore.py` 로 쪼개
      `Result.repost()` 프로덕션 경로를 검증. F01×W03: 0.1642 → 0.9277, 육안
      확인 완료(흰 테두리 없음, 목·옷깃 연결 자연스러움)
- [x] **배치 위치** — 2026-09-23 `placement.py`. 지면 분할(Mask2Former) +
      원근 맞춤(DETR 사람들, Hoiem 2006) + 삼등분선 + 겹침 회피. 20개 배경
      점검 완료. 합성 검증은 아래 절 참조
- [x] **인물 영역만 되붙이기** — 2026-09-23 `paste.py`. 크롭 안 배경 선명도
      9~31% → **100%**, 변화량 → 0. 발밑 생성 영역은 그림자가 아니라 새로 그린
      바닥이라 안 가져왔다. 얼굴 이식의 흰 테두리를 순서 변경(이식 → 되붙이기)으로
      해결. 3단계는 `apply_post.py`(CGI venv)
- [x] **접지 그림자 (person 방식)** — 2026-09-26 `shadow.py`. `contact`를 3단계 기본으로.
      투영 그림자(`cast`)는 구현했지만 해 자동 검출이 20개 중 0개라 보류
- [ ] **투영 그림자 켜기** — UI에서 광원 방향을 고르게 하거나(볕/그늘도 사용자가 안다),
      해 추정을 사람 그림자 외의 단서(기둥·나무 그림자)로 넓히기
- [x] **2안 첫 시도 (가방)** — 2026-09-26. 관절 기준 배치 + AnyDoor + `object` 되붙이기.
      가방 재현 좋음, 손 상호작용은 가림으로 처리. 주머니 손 규칙 추가
- [x] **2안 시계·자동차 사진** — 2026-09-26 Unsplash 6장 수집(4장 사용), `fetch_objects.py`
- [x] **2안 시계** — 손목 둘레 부분 이미지 합성 + 되붙이기. 드러난 손목(F04)은 전신 크기에서
      자연스럽고, 확대하면 손등 쪽 치우침·기존 팔찌 잔존·문자판 각도가 남는다
- [x] **2안 자동차** — 1안 배치 + `--height-scale`. C03×K08 자연스러움, 차용 접지 그림자 v2
- [ ] **2안 자동차 배치가 다른 차를 피하게** — 지금은 사람만 피한다(C01이 주차 차량을 가림).
      DETR의 car 클래스도 겹침 제외에 넣기
- [ ] **2안 조명** — 스튜디오 참조를 볕 드는 장면에 넣으면 고르게 밝다. 색 정합은 제품 색을
      바꿔서 못 쓴다 — 밝기(L)만 맞추는 도구 필요
- [ ] **2안 시계 배경 선택** — 소매가 손목을 덮지 않은 사진 고르기(드러난 손목 검출)
- [ ] **2안 가방 자세** — 쥔 손이 보이는 모습(`grip` 음수), 어깨에 멘 모습
- [ ] **지면 경계 피하기** — K05 발이 연석 모서리에 걸쳤다(원본 바닥이 돌아오며
      드러남). `auto_place`가 지면 마스크의 경계(길/잔디, 연석)에서 떨어지도록
- [ ] **원경 인물 겹침** — W09 어깨 뒤 행인 2명. 겹침 기준(DETR 박스 5%)이 작은 원경
      인물을 못 거른다. 가림 관계는 맞으므로 우선순위 낮음
- [ ] **다리가 잘리는 구도** — K06·W03·W06·W08·W10은 원근상 전신이 1% 미만이다.
      인물을 크게 넣으려면 발이 화면 밖으로 나가야 하고, 그러면 참조도 그만큼
      위쪽만 잘라야 한다 (`prep.crop_to_face`와 이어짐)
- [ ] **UI 연결** — 사용자가 발 위치를 클릭하면 `Perspective.height_at(v)`로 크기를
      자동 계산하는 경로. `place_feet()`가 이미 있어 붙이기만 하면 된다
- [ ] 얼굴 색 정합 개선 — `face_color_match=0.5`로도 피부·머리색이 장면보다
      밝게 남는 사례가 있다(F01×콜로세움)
- [ ] 극단적 각도 검증 — 이번 12쌍은 대체로 정면이라, 생성물 얼굴이 참조와
      크게 다른 각도(옆모습 등)일 때 2D 닮음변환이 버티는지 확인 안 됨
