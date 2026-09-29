# CGIv2

AnyDoor의 **가중치 라인은 그대로 쓰고**, 그 앞뒤(전처리·후처리)만 우리가 짠다.

```
[전처리]   마스크 생성 · 객체 정규화 · 배치 마스크        우리 영역
     ↓
process_pairs                                             규약 — 숫자를 지킨다
     ↓
[가중치]   DINOv2 → ControlNet → U-Net → DDIM → VAE      손대지 않음
     ↓
crop_back 역변환                                          규약
     ↓
[후처리]   얼굴 이식 · 인물만 되붙이기 · 색 정합 · 그림자 · 평가   우리 영역
```

## 왜 가운데를 안 건드리나

AnyDoor에는 **조건 경로가 하나뿐**이다. 텍스트 인코더가 없어 대체 경로가 없다.

```
DINOv2 → projector(1536→1024) → c_crossattn
                                      ↓
                        U-Net의 to_k / to_v 전부
                        ControlNet의 context 전부
```

인코더를 바꾸면 도미노가 넘어간다. 2,452M 중 **VAE 84M만 남는다 (3.4%)**.

반면 다음은 가중치와 무관해 자유롭게 바꿀 수 있다.

| 자유 | 이유 |
|---|---|
| 샘플러 · 스텝 수 | 같은 β 스케줄을 다르게 훑을 뿐 |
| `cfg` · `control_strength` | 추론 시 조작 |
| 조건 토큰 **개수** | 어텐션은 가변 길이 (차원 1024만 고정) |
| 정밀도 · 배치 크기 | |

**차원은 고정, 개수는 자유. 스케줄은 고정, 샘플러는 자유.**

---

## 구조

```
cgiv2/
  anydoor.py    가중치 라인 래퍼 — 감싸기만 한다 + DINOv2 토큰 캐싱
  pairs.py      process_pairs 통합본 (세 벌 → 한 벌) + crop_back
  mask.py          BiRefNet 마스크 생성            ← AnyDoor에 없음
  prep.py          객체별 정규화 + 배치 마스크      ← AnyDoor에 없음
  placement.py     지면 분할 + 원근으로 배치 위치    ← AnyDoor에 없음 (1안)
  anchor.py        관절 기준 배치 — 가방을 손에      ← AnyDoor에 없음 (2안)
  face_restore.py  원본 얼굴 정렬 이식              ← AnyDoor에 없음
  paste.py         되붙일 범위 (크롭 / 박스 / 인물·물건) ← AnyDoor 데모에만 박스 버전
  shadow.py        접지 · 투영 그림자 + 해 추정      ← AnyDoor에 없음
  postproc.py      페더링 · 색 정합 · 그림자        ← AnyDoor에 없음
  evaluate.py      DINOv2 코사인 · SFace 얼굴 · 이음매 · OCR ← AnyDoor에 없음
  pipeline.py      연결

scripts/
  check_dataset.py   관문 사전검사 (GPU 불필요)
  run_single.py      한 장 합성
  run_batch.py       베이스라인 일괄 + 격자 탐색 + 지표 집계
  check_placement.py 배치 점검 (CGI venv)          ┐
  gen_placed.py      배치대로 확산 (AnyDoor venv)  ├ 1안 배치 합성 3단계
  apply_post.py      얼굴 이식 + 되붙이기 + 그림자 (CGI venv) ┘ (2안도 3단계 공용)
  check_anchor.py    2안 1단계 — 관절 기준 배치 (CGI venv)
  import_rgba.py     누끼 PNG → 사진 + 마스크
  compare_paste.py   되붙이기 방식 비교
  compare_shadow.py  그림자 방식 비교
```

**AnyDoor 저장소는 한 줄도 수정하지 않는다.** `sys.path`로 import만 한다.

---

## 시작

```bash
pip install pyyaml opencv-python-headless numpy
```

`config.yaml`의 `paths`를 확인한 뒤, GPU 없이 먼저 돌려본다.

```bash
python scripts/check_dataset.py
```

관문 네 개(연결성 0.90 / 면적 1~64% / 변 10%)에 우리 객체가 걸리는지 나온다.
**이걸 먼저 하는 이유** — 학습 경로의 `__getitem__`이 예외를 통째로 삼키고
무한 재시도하므로, 탈락한 객체가 섞이면 에러 없이 멈춘다.

그다음 한 장:

```bash
python scripts/run_single.py --object p01 --background kr01_gyeongbokgung
```

그다음 베이스라인:

```bash
python scripts/run_batch.py
python scripts/run_batch.py --grid        # cfg 3종 x strength 3종
```

`outputs/baseline_report.json`에 지표가 쌓인다.

---

## 1안 배치 합성 — 3단계

venv가 둘로 나뉜다. AnyDoor venv(cv2 4.7.0 · transformers 4.19.2)에서는 YuNet이
크래시하고 Mask2Former가 없다. 그래서 계산은 CGI venv, 확산만 AnyDoor venv에서 한다.

```bash
D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/check_placement.py
```

```bash
D:/JungPra/pythonpra/CGI/AnyDoor/.venv/Scripts/python.exe scripts/gen_placed.py --object F01 --backgrounds K05 W01 W05 W09
```

```bash
D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/apply_post.py
```

1. 배경마다 지면·원근을 보고 발 위치와 키를 정한다 → `work/placement/`
2. 확산 → raw 512를 저장한다 → `work/placed/`
3. 얼굴 이식 후 **인물만** 원본 배경 위에 되붙인다 → `outputs/placed/<키>_final.png`

3단계가 인물만 되붙이는 이유 — AnyDoor는 512 크롭 전체를 다시 그리는데, 크롭이
화면의 41~67%를 덮어 그 안의 랜드마크가 원본 선명도의 9~31%로 뭉개진다.
원저자도 데모(`run_gradio_demo.py:140-143`)에서는 박스 밖을 원본으로 되돌렸다.
발밑에는 접지 그림자(`--shadow contact`, 기본)를 넣는다.

## 2안 — 사람 사진에 물건 (지금은 가방)

1안과 같은 3단계인데 1단계가 **장면 대신 몸(관절)**을 본다.

```bash
D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/check_anchor.py --object B01 --only F03 F04
```

```bash
D:/JungPra/pythonpra/CGI/AnyDoor/.venv/Scripts/python.exe scripts/gen_placed.py --placement work/plan2/anchor --bg-dir D:/JungPra/pythonpra/CGI/objects --obj-dir work/plan2/objects --mask-dir work/plan2/masks --object B01 --backgrounds F03 F04 --out work/plan2/gen
```

```bash
D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe scripts/apply_post.py --work work/plan2/gen --out outputs/plan2/object --paste object --shadow none --no-face --obj-dir work/plan2/objects --mask-dir work/plan2/masks
```

주머니에 넣은 손은 관절 규칙으로 걸러진다(가방을 들 수 없다).

---

## 원본에서 고친 것 셋

모두 가중치와 무관한 버그다.

### 패딩 센티넬

`run_inference.py:255`가 `pad_value=-1` 뒤에 `uint8` 캐스팅을 한다. `-1`은
`255`로 감기고, 이어지는 `> 0.5`를 통과해 **1.0(= 여기 생성해라)** 이 된다.
학습 쪽은 이걸 알고 센티넬 `2`를 쓴 뒤 나중에 `-1`로 되돌린다.

죽은 경로가 아니다. `box2squre`가 `max(0,x1)`로 경계를 클램프하므로 **객체가
프레임 가장자리에 있으면 패딩이 실제로 생긴다.**

### 타깃 크롭 랜덤성

`expand_bbox`가 범위에서 `np.random`으로 뽑는다. 추론에서도 `[1.5, 3]`이라
매 실행마다 크롭이 달라진다. diffusion seed를 고정해도 크롭이 흔들리므로
**"strength 0.8이 나았나"를 판정할 수 없다.** 추론에서는 고정값을 쓴다.

### crop_back 1픽셀 밀림

호출부가 `pred[1:,:,:]`로 맨 윗줄을 버린 뒤 resize해서 결과가 세로로 1px
밀린다. 여기서는 자르지 않는다.

---

## 후처리는 기본이 전부 꺼짐

AnyDoor에 후처리가 없는 건 빠뜨린 게 아니라 **"확산이 암묵적으로 처리한다"는
설계**다. 그 위에 덧칠하면 이중 보정이 된다.

```
0단계  아무것도 켜지 않고 베이스라인 400쌍
       → 실패 유형을 숫자로 분류
1단계  그 유형에 해당하는 것만 켠다
       조명 안 맞음 → color_match 0.3부터
       떠 보임      → shadow
       경계 티      → feather
```

**측정 없이 다 켜면 무엇이 효과였는지 알 수 없다.**

### 가져오지 못한 것 — 정체성 복원

CGI의 Frequency Separation이 통했던 건 SD 1.5 inpainting이 물체의 픽셀 위치를
유지했기 때문이다. AnyDoor는 동영상 쌍으로 **자세를 바꾸도록** 학습됐다.
참조와 결과 사이에 픽셀 대응이 없으므로 고주파를 되붙일 좌표가 없다.

예외는 강체 + `shape_control=True`로 실루엣을 고정한 경우뿐이고, 그때도
부분적이다. 구현하지 않았다.

---

## 객체별로 다른 관문에 걸린다

| 객체 | 걸리는 곳 | `prep`의 대처 |
|---|---|---|
| 시계 | 면적 하한 1% | `crop_to_area` — 손목 주변 크롭 |
| 가방 | 연결성 0.90 (어깨끈) | `mask.bridge_thin_parts` |
| 자동차 | 면적 상한 64% | `pad_to_area` — 여백 덧대기 |
| 사람 | 대체로 통과 | — |

`normalize_object()`가 면적 하한/상한을 자동으로 처리한다. 연결성은 마스크를
훼손할 수 있어 자동으로 하지 않는다 — `check_dataset.py`가 알려주면 수동으로
`bridge_thin_parts`의 반지름을 올려가며 최소값을 찾는다.

---

## shape_control

`collage_mask`를 bbox 사각형 대신 실제 실루엣으로 만든다.

| | 효과 |
|---|---|
| `false` (기본) | 모델이 bbox 안에서 형태를 자유롭게 만듦 |
| `true` | 사용자가 준 실루엣을 그대로 따름 |

**1안(사람)은 `false`, 2안(시계·자동차)은 `true`를 시험해볼 값이 있다.**
강체는 형태가 변하면 안 되고 비강체는 자세가 배경에 맞게 변해야 한다.
`run_batch.py --grid`의 `shape_control` 항목에 `[false, true]`를 넣으면 비교가
나온다.

---

## 알아둘 것

**VRAM.** 10GB 카드에서 `save_memory: true`로 돌면 여유가 260MiB 남짓이다.
큰 배경에서 OOM이 나면 배경을 가로 1024 이하로 줄인다. 24GB로 옮기면
`save_memory: false`가 맞고, CPU↔GPU 왕복이 사라져 눈에 띄게 빨라진다.

**DINOv2 캐싱.** 원본은 합성마다 1.1B 모델을 돌린다. 400회 생성이면 400번인데,
참조가 같으면 토큰도 같으므로 20번이면 된다. `run_batch.py`가 절약 횟수를
보고서에 남긴다.

**평가 지표 검증.** `IdentityScorer`가 실제로 작동하는지 먼저 확인하는 편이
좋다 — 같은 사람 두 장의 유사도가 다른 사람 두 장보다 높게 나오면 된다.

**학습은 여기 없다.** 이 폴더는 추론·평가 전용이다. 학습은 `pairs.py`의
`build(train=True)`가 학습용 item을 만들어 주므로, 별도 스크립트에서
`BaseDataset`을 상속해 쓰면 된다.
