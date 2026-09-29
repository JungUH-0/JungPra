# CGIv2 인계

2026-09-23 ~ 09-29 대화를 요약한 문서다. 다른 PC나 새 대화에서 이어갈 때 이것부터 읽는다.
값 하나하나는 [CHANGELOG.md](CHANGELOG.md), 실행 명령은 [README.md](README.md)에 있다.

## 목표

- AnyDoor 가중치는 그대로 두고, 앞뒤 전처리·후처리만 직접 만든다.
- 출시용이 아니라 **내부 테스트용**이다. 각자 PC에서 로컬로 돌려 보고 끈다.
- 1안: 명소 배경 × 사용자 사진. 얼굴이 그 사람으로 보여야 한다.
- 2안: 사람 사진 × 시계·가방·자동차.
- 3안: 퍼스널 컬러. 아직 시작하지 않았다.

## 작업 규칙

사용자가 정한 규칙이다. 새 대화에서도 그대로 지킨다. 이 PC에서는 Claude 메모리
(`C:\Users\AISW_203_104\.claude\projects\D--JungPra\memory\`)에 있고, 다른 PC에는 없다.

1. 학습·실험 코드는 AI가 실행하지 않는다. 작성·수정까지만 하고, 사용자가 실행한 뒤 결과를 붙여 주면 해석한다.
2. 가상환경 생성·패키지 설치는 명령어만 알려 준다.
3. 명령을 실행하기 전에 무엇을, 왜, 얼마나 걸리는지(모델 로딩·확산 포함) 먼저 말한다.
4. 요청한 것만 바꾼다. 관련 개선점은 한두 줄로 알리고, 넣을지는 사용자가 정한다.
5. CGIv2를 고치면 CHANGELOG.md에 값 하나까지 기록한다.
6. AnyDoor 저장소 파일은 CGIv2 때문에 고치지 않는다 (import·감싸기만). 10GB 패치는 적용된 채로 둔다.
7. torch를 올리지 않는다. `torch.load` 보안 검사를 우회하지 않는다.
8. 파일을 내려받기 전에 파일명·출처·크기를 보여 주고 승인을 받는다.
9. GPU(10GB) 작업은 동시에 돌리지 않는다.

## 전체 흐름

| 날짜 | 한 일 |
|---|---|
| 09-21 | CGIv2 골격. 원본 버그 3개 수정, BiRefNet 마스크, 정체성 지표 수정 |
| 09-22 | 얼굴 지표(SFace). 전신 합성 얼굴 0.107 (판정선 0.363) → 상반신 크롭 0.131 → 얼굴 이식 0.9488 (12/12 통과) |
| 09-23 | 배치 위치 (지면 분할 + 원근). 인물만 되붙이기로 크롭 안 배경 선명도 9~31% → 100% |
| 09-26 | 그림자 (접지 기본). 2안 가방·시계·자동차 |
| 09-28 | Word 진행 보고서. 학습 방향 검토 |
| 09-29 | git 첫 등록, 이 문서 |

## 이번 대화에서 한 일

1. **인물만 되붙이기** — `cgiv2/paste.py`. `Settings.paste` = `crop` | `box` | `person` | `object`
   - AnyDoor가 다시 그린 512 크롭에서 인물만 원본 배경 위에 올린다. 랜드마크 선명도가 원본 그대로 남는다.
   - 머리 둘레 흰 테두리는 얼굴 이식을 되붙이기 **앞으로** 옮겨 해결했다.
   - 순서: crop_back → blend → 얼굴 이식 → 되붙이기 → 그림자
2. **그림자** — `cgiv2/shadow.py`
   - `contact` (기본): 강도 0.5, 폭 1.25, 높이 0.03
   - `cast`: 해 방향이 있어야 한다. 해 자동 추정(`estimate_sun`)이 배경 20개 중 0개를 찾아서 보류
3. **2안 가방** — `cgiv2/anchor.py` (Keypoint R-CNN, 관절 점수 기준 2.0), `scripts/check_anchor.py`
   - `bag_in_hand`: 가방 높이 = 키 × 0.26, grip 0.03
   - 주머니에 넣은 손은 뺀다 (안쪽 기울기 15° 초과, 또는 손목이 엉덩이보다 키 × 0.05 이상 위)
   - 가방 자체는 잘 옮겨진다. 쥔 손은 그리지 못해 가방으로 가린다.
4. **2안 시계** — 시계는 화면의 1%가 안 돼 AnyDoor 면적 관문에 걸린다.
   - 손목 둘레를 박스 긴 변 × 6으로 잘라 그 안에서 합성하고, 원본 사진에 되붙인다.
   - 시계 머리를 줄 축이 팔뚝과 직각이 되게 돌린다. face 0.023, offset −0.025, keep 0.6
   - 전신 크기에서는 찬 것처럼 보인다. 확대하면 손등 쪽 치우침, 원래 팔찌 잔존, 문자판 정면이 남는다.
5. **2안 자동차** — 1안 배치에 `--height-scale`
   - 차용 접지 그림자 v2: `--contact-strength 0.7 --contact-width 1.05 --contact-height 0.08`, 색 맞춤 없음
   - C03×K08은 자연스럽다. C01은 주차된 차를 가린다 (지금은 사람만 피한다).
6. **사진** — Unsplash에서 6장을 받아 4장 사용 (`scripts/fetch_objects.py`). 출처는 `work/plan2/objects/_credits.json`
7. **Word 보고서** — `outputs/report/CGIv2_진행보고서.docx` (A4, 8장, 표 8, 그림 10). 원본은 `docs/build_report.js`
   - 파일 구조만 확인했다. 화면에서 어떻게 보이는지는 확인하지 못했다.
8. **학습 검토** — 아래 절

## 현재 위치 — 학습 방향 결정 대기

원칙은 유지한다. 학습을 붙인다면 **LoRA**다. AnyDoor 가중치는 고정하고 수 MB 어댑터만
학습하므로, 끄면 지금과 결과가 같다.

AnyDoor 원본 학습 (AnyDoor 저장소에서 확인):

- 학습 대상: ControlNet, U-Net `output_blocks`·`out`, DINOv2 뒤 projector(1536→1024) — `AnyDoor/cldm/cldm.py:422`
- 고정: DINOv2, U-Net 인코더·중간 블록, VAE
- 데이터: 같은 물체가 두 장면에 나오는 쌍. 12개 데이터셋 (영상 6, 정지 이미지 3, 가상 착용 2, 다시점 1)
- 노이즈 단계 (`AnyDoor/datasets/base.py:74`): 30%는 전체 구간에서 고르게. 나머지는 영상 t 500~1000, 정지 이미지 t 0~500, 다시점·착용 전체
- 자원 (`AnyDoor/README.md:138`): A100 2장, GPU당 배치 16, fp16, lr 1e-5, 30만 스텝

RTX 3080 10GB에서:

| 방식 | 학습 파라미터 | 가능 여부 |
|---|---|---|
| 원본 방식 | 약 9억 (추정) | ✗ 가중치·기울기·Adam 상태만 약 14GB |
| LoRA (디코더 attention) | 수백만 이하 | ○ (추정) DINOv2 출력 캐시 + gradient checkpointing, 배치 1~2 |
| projector만 | 157만 | ○ 효과 불확실 |

남은 문제별 판단:

- 규칙으로 고칠 것: 자동차 겹침, 시계 위치, 원래 팔찌 (인페인팅)
- 데이터가 막는 것: 시계 문자판 각도, 가방을 쥔 손
- 학습이 유력한 것: 스튜디오 조명 (2안), 사람별 얼굴·머리·체형 (1안)
- AnyDoor 밖: 그림자 방향

제안 — **사용자가 아직 고르지 않았다.**

- **1순위: 1안 사람별 LoRA.** 한 사람 사진 10~20장이나 30초 영상으로 쌍 수백 개. 1,500스텝에 30분~1시간 (추정).
  지금 결과를 기준선으로 두고 `cgiv2/evaluate.py`의 FaceScorer로 비교한다.
- **2순위: 2안 조명 LoRA.** 물체 분할 사진이 수천 장 필요해 데이터를 받아야 한다 (목록·크기를 먼저 보여 주고 승인).
- 구현 계획: 새 폴더 `train/`에 쌍 만들기, DINOv2 출력 캐시, LoRA 학습 스크립트.
  AnyDoor 파일은 고치지 않고 실행할 때 LoRA를 끼운다. LoRA를 직접 구현해 새 패키지가 없다.
  파이프라인에는 `lora` 설정 하나 (기본 꺼짐)만 추가한다.

## 다음 단계

1. 학습 방향 결정 — 위 1순위 / 2순위
2. CHANGELOG `다음에 할 것`의 미완료 항목
   - 투영 그림자 켜기 (UI에서 광원 방향 선택 등)
   - 2안 자동차가 다른 차도 피하게 (DETR car 클래스)
   - 2안 조명 — 밝기(L)만 맞추는 도구
   - 2안 시계 배경 선택 (드러난 손목), 2안 가방 자세 (쥔 손, 어깨에 멘 모습)
   - 지면 경계(연석) 피하기, 원경 인물 겹침, 다리가 잘리는 구도
   - UI 연결 (발 위치 클릭 → 크기 자동 계산)
   - 얼굴 색 정합, 옆얼굴 검증
3. Word 보고서를 열어 화면 확인
4. `scripts/swap_tools.py`는 만들었지만 한 번도 실행하지 않았다.
5. 3안 (퍼스널 컬러)

## 환경과 데이터 — 다른 PC로 옮길 때

### git에 있는 것

- `pythonpra/CGIv2/` 코드와 문서 (`outputs/`, `work/` 제외)
- [env/cgi-venv.txt](env/cgi-venv.txt), [env/anydoor-venv.txt](env/anydoor-venv.txt) — 두 가상환경의 설치 목록 (2026-09-29)
- [../CGI/docs/anydoor_local_10gb.md](../CGI/docs/anydoor_local_10gb.md), `../CGI/_anydoor_backup/anydoor_10gb_fixes.patch`
  — AnyDoor를 10GB 카드에서 돌리는 패치와 설명

### git에 없는 것

| 무엇 | 이 PC 위치 | 크기 | 옮기는 법 |
|---|---|---|---|
| AnyDoor 저장소 | `CGI/AnyDoor` | — | 아래 명령으로 받고 패치 적용 |
| AnyDoor 가중치 | `CGI/AnyDoor/path/` | 14GB | 복사. `anydoor_pruned.ckpt` 9.13GB, `dinov2_vitg14_pretrain.pth` 4.23GB |
| 대화형 분할 가중치 | `CGI/AnyDoor/iseg/` | 7.6MB | 복사 (Gradio 데모용) |
| 사람·물건 사진 | `CGI/objects` | 22MB · 32장 | 복사 |
| 배경 사진 | `CGI/backgrounds` | 88MB · 41장 | 복사 |
| AnyDoor 예제 데이터 | `CGI/AnyDoor/data_test` | 17MB | 복사 (`config.yaml`이 가리킨다) |
| 얼굴 모델 | `CGIv2/work/models/` | 38MB | 복사. YuNet `2023mar`, SFace `2021dec` (OpenCV Zoo) |
| 중간 산출물 | `CGIv2/work/` | 324MB | 후처리만 다시 하려면 복사 (raw 512, 배치 마스크) |
| 결과 | `CGIv2/outputs/` | 436MB | 기준선과 비교하려면 복사 |
| Hugging Face 모델 | `~/.cache/huggingface/hub` | — | 첫 실행 때 자동. BiRefNet_HR-matting, mask2former-swin-small-ade-semantic, detr-resnet-50 |
| Keypoint R-CNN | `~/.cache/torch/hub/checkpoints` | — | 첫 실행 때 자동 (torchvision) |

AnyDoor 저장소 (원본 커밋 `44ca2b2a` + 10GB 패치):

```bash
git clone https://github.com/ali-vilab/AnyDoor.git D:/JungPra/pythonpra/CGI/AnyDoor
```

```bash
git -C D:/JungPra/pythonpra/CGI/AnyDoor checkout 44ca2b2a70ec2cf107f3d26a5b46def6670fb0a5
```

```bash
git -C D:/JungPra/pythonpra/CGI/AnyDoor apply ../_anydoor_backup/anydoor_10gb_fixes.patch
```

- 경로: `config.yaml`과 스크립트 기본값이 `D:/JungPra/pythonpra/...` 절대경로다. 같은 자리에 두면 고칠 것이 없다.
- 이 PC: RTX 3080 10GB, RAM 31.7GB, Windows 11. 24GB 이상이면 `config.yaml`의 `save_memory`를 `false`로 둔다
  (패치 문서의 "24GB 이상으로 옮길 때").

### 가상환경 — 두 개, 둘 다 uv · Python 3.10.20

| | 위치 | 핵심 버전 | 쓰임 |
|---|---|---|---|
| CGI venv | `CGI/.venv` | torch 2.4.1+cu121, transformers 4.55.4, opencv 4.11.0.86 | 배치 · 얼굴 이식 · 되붙이기 · 그림자 · 평가 |
| AnyDoor venv | `CGI/AnyDoor/.venv` | torch 2.0.0+cu118, transformers 4.19.2, opencv 4.7.0.72, pytorch-lightning 1.5.0, xformers 0.0.18 | 확산만 |

AnyDoor venv에서는 YuNet이 죽고 (cv2 4.7.0) Mask2Former가 없어서 (transformers 4.19.2) 둘로 나눴다.
그래서 1안·2안 모두 3단계로 돈다: CGI venv 배치 → AnyDoor venv 확산 → CGI venv 후처리.

다시 만드는 명령이다. 이 PC에서 돌려 보지는 않았다. 목록은 의존성까지 전부 버전을 고정한 것이라,
안 깔리는 것이 있으면 핵심 버전만 맞춘다.

```bash
uv venv D:/JungPra/pythonpra/CGI/.venv --python 3.10
```

```bash
uv pip install --python D:/JungPra/pythonpra/CGI/.venv/Scripts/python.exe -r D:/JungPra/pythonpra/CGIv2/env/cgi-venv.txt --extra-index-url https://download.pytorch.org/whl/cu121 --index-strategy unsafe-best-match
```

```bash
uv venv D:/JungPra/pythonpra/CGI/AnyDoor/.venv --python 3.10
```

```bash
uv pip install --python D:/JungPra/pythonpra/CGI/AnyDoor/.venv/Scripts/python.exe -r D:/JungPra/pythonpra/CGIv2/env/anydoor-venv.txt --extra-index-url https://download.pytorch.org/whl/cu118 --index-strategy unsafe-best-match
```

옮긴 뒤 첫 확인은 README.md의 "시작" (GPU 없이 `check_dataset.py`) → "1안 배치 합성 — 3단계" 순서다.

## 새 대화 시작용 요청

```
D:/JungPra/pythonpra/CGIv2/HANDOFF.md를 먼저 읽고, 필요한 부분만 README.md와 CHANGELOG.md에서 찾아 읽어 주세요.
한국어로 설명하고 HANDOFF.md의 작업 규칙을 지켜 주세요.
특히 학습 코드는 실행하지 말고, 설치는 명령어만 알려 주고, 무엇이든 실행하기 전에 먼저 설명해 주세요.
지금은 학습(LoRA) 방향을 정하는 단계입니다. 제가 고른 쪽은 ___ 입니다.
코드를 쓰기 전에 어떤 파일을 만들고 무엇을 바꿀지부터 설명해 주세요.
```
