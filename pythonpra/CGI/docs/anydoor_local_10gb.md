# AnyDoor 로컬 실행 패치 (10GB VRAM)

원본 AnyDoor는 **10GB 카드에서 그대로 실행되지 않는다.** 체크포인트를 GPU에
직접 올리는 구조라 로딩 중에 OOM으로 죽는다. 이 문서는 그것을 포함해 7군데를
고친 내역과 실행 방법을 기록한다.

- 대상 커밋: `44ca2b2a70ec2cf107f3d26a5b46def6670fb0a5`
- 패치 파일: `_anydoor_backup/anydoor_10gb_fixes.patch`
- 검증 환경: RTX 3080 10GB · RAM 31.7GB · Windows 11 · Python 3.10
- 검증일: 2026-09-21 (Gradio 데모 기동 및 HTTP 200 확인)

> 현재 저장소에는 이 패치가 **적용된 상태**다. 원본과 비교하려면 아래
> [되돌리기](#되돌리기) 참조.

---

## 전제

`AnyDoor/path/` 에 가중치 두 개가 있어야 한다.

```
path/anydoor_pruned.ckpt          9.13 GB
path/dinov2_vitg14_pretrain.pth   4.23 GB
iseg/coarse_mask_refine.pth       약 10 MB   (대화형 세그멘테이션용)
```

---

## 패치 내역

### ① 체크포인트 경로

**파일** `configs/demo.yaml`, `configs/inference.yaml`

```diff
-pretrained_model: path/epoch=1-step=8687.ckpt
+pretrained_model: path/anydoor_pruned.ckpt
```

원본 설정이 가리키는 파일명이 실제 배포본(ModelScope / HuggingFace)과 다르다.
고치지 않으면 `FileNotFoundError` 로 즉시 죽는다.

### ② 체크포인트를 CPU로 로드 — 가장 중요

**파일** `run_inference.py`, `run_gradio_demo.py`

```diff
 model = create_model(model_config).cpu()
-model.load_state_dict(load_state_dict(model_ckpt, location='cuda'))
-model = model.cuda()
+model.load_state_dict(load_state_dict(model_ckpt, location='cpu'))
```

`location='cuda'` 는 **체크포인트 전체를 GPU에 먼저 올린다.** 모델이 이미 CPU에
만들어져 있는데도 그렇다. 그래서 순간적으로 9.8GB가 VRAM에 앉고, 그 위에 모델을
올리려다 터진다.

**증상** — 로딩 중 `torch.cuda.OutOfMemoryError`. 10GB 카드에서는 여기서 바로
막힌다.

### ③ save_memory 활성화

**파일** `configs/demo.yaml`, `configs/inference.yaml`

```diff
-save_memory: False
+save_memory: True
+use_sliced_attention: False
```

`ControlLDM.low_vram_shift()` 로 모듈을 CPU/GPU 간 교대 배치한다. 확산 중에는
U-Net·ControlNet이 GPU에 있고, 인코딩/디코딩 중에는 VAE·DINOv2가 GPU에 있다.

### ④ 최상위 버퍼 수동 이동 — 조용히 물리는 함정

**파일** `run_inference.py`, `run_gradio_demo.py`

```python
if save_memory:
    # low_vram_shift 는 서브모듈만 옮기므로 최상위 버퍼는 직접 GPU 로 (약 56KB)
    for _k, _v in list(model._buffers.items()):
        if _v is not None:
            model._buffers[_k] = _v.cuda()
    model.low_vram_shift(is_diffusing=False)
else:
    model = model.cuda()
```

`low_vram_shift` 가 옮기는 것은 서브모듈 **넷뿐**이다.

```python
# cldm/cldm.py:432
self.model = self.model.cuda()                    # U-Net
self.control_model = self.control_model.cuda()    # ControlNet
self.first_stage_model = ...                      # VAE
self.cond_stage_model = ...                       # DINOv2
```

`ControlLDM` 자신이 들고 있는 버퍼(`betas`, `alphas_cumprod`,
`sqrt_alphas_cumprod` 등)는 건드리지 않는다. 원본은 `model.cuda()` 로 함께
올라갔던 것들이다.

**증상** — 에러가 아니라 **극단적인 느려짐**. `cldm/ddim_hacked.py:130` 이
`device = self.model.betas.device` 로 디바이스를 정하므로, 버퍼가 CPU에 남으면
샘플링 전체가 CPU에서 돈다. 원인 찾기가 고약하다.

### ⑤ 원본 버그 — use_interactive_seg

**파일** `run_gradio_demo.py`

```diff
-use_interactive_seg = config.config_file
+use_interactive_seg = bool(config.get('use_interactive_seg', True))
```

`config_file` 은 `"configs/anydoor.yaml"` 문자열이다. **항상 truthy** 라서
`demo.yaml` 에 `use_interactive_seg: False` 를 써도 무시된다. 변수명을 잘못 쓴
업스트림 버그로 보인다.

### ⑥ sliced attention 을 save_memory 에서 분리

**파일** `run_inference.py`, `run_gradio_demo.py`

```diff
-save_memory = False
-if save_memory:
-    enable_sliced_attention()
+save_memory = bool(config.get('save_memory', False))
+use_sliced_attention = bool(config.get('use_sliced_attention', False))
+if use_sliced_attention:
+    enable_sliced_attention()
```

원본은 둘이 한 덩어리였다. sliced attention 은 xformers 보다 느리므로 기본은
꺼두고, VRAM 이 정말 부족할 때만 켠다.

### ⑦ 네트워크 노출 제한

**파일** `run_gradio_demo.py`

```diff
-demo.launch(server_name="0.0.0.0")
+demo.launch(server_name="127.0.0.1", server_port=7860)
```

`0.0.0.0` 은 같은 네트워크의 다른 기기에도 열린다. 로컬 테스트용이므로
루프백으로 제한하고 포트를 고정했다.

---

## 추가한 파일

`_anydoor_backup/run_demo_single.py` — 번들 예제 1장으로 추론하고 피크 VRAM을
찍는 24줄. 원본 `run_inference.py` 의 `__main__` 은 VITON-HD 데이터셋 전체를
도는 코드라 그냥은 돌릴 수 없다.

---

## 실행

```bash
cd D:/JungPra/pythonpra/CGI/AnyDoor && .venv/Scripts/python.exe run_gradio_demo.py
```

브라우저에서 `http://127.0.0.1:7860` 을 연다.

### 사용

```
① 왼쪽에 객체 사진 업로드    브러시로 넣고 싶은 물체를 칠한다
② 오른쪽에 배경 사진 업로드  브러시로 놓을 자리를 칠한다
③ Run
```

`use_interactive_seg: True` 이므로 왼쪽은 대충 칠해도 `iseg` 가 경계를 다듬는다.

### 종료

```bash
taskkill //PID <PID> //F
```

### 대안 — Claude Code 미리보기 패널

`.claude/launch.json` 에 `anydoor-demo` 설정이 있다. Claude Code 안에서
미리보기 패널로 띄울 때 쓴다. 터미널에서 직접 돌릴 때는 필요 없다.

---

## 측정값 (RTX 3080 10GB)

| 단계 | 값 |
|---|---|
| `create_model()` | 약 10.4 GB RSS (fp32 구조 생성) |
| 체크포인트 로드 피크 | 11.6 GB RSS |
| 로드 완료 후 | 5.9 GB RSS (임시 딕셔너리 해제) |
| 기동 시간 | 2분 남짓 |
| 기동 후 VRAM | **9978 / 10240 MiB** |
| 종료 후 VRAM | 725 MiB |

### 알려진 제약 — VRAM 여유가 262MiB뿐이다

`save_memory` 모드인데도 거의 꽉 찬다. `low_vram_shift` 는 **모듈을 옮길 뿐
PyTorch 캐시 할당자가 잡은 블록을 반납하지 않기 때문**이다.

큰 이미지에서 OOM이 나면 순서대로 시도한다.

1. 배경 이미지를 가로 1024 이하로 줄인다
2. `configs/demo.yaml` 에서 `use_sliced_attention: True` (느려지는 대신 메모리 절감)

첫 합성은 U-Net·ControlNet 을 CPU→GPU 로 올리는 시간이 더해져 느리다. 두 번째
부터 빨라진다.

---

## 24GB 이상으로 옮길 때

**7개 중 4개가 불필요해진다.**

| 패치 | 10GB | 24GB |
|---|---|---|
| ① 경로 | 필요 | 필요 |
| ② CPU 로드 | **필수** | 선택 (RAM 넉넉하면) |
| ③ save_memory | **필수** | **불필요** — `False` |
| ④ 버퍼 이동 | **필수** | 불필요 (③에 딸린 것) |
| ⑤ 원본 버그 | 필요 | 필요 |
| ⑥ sliced 분리 | 필요 | 불필요 |
| ⑦ 노출 제한 | 필요 | 필요 |

`save_memory: False` 하나로 ③④⑥ 이 함께 빠진다. 모델이 전부 GPU에 상주하므로
CPU↔GPU 왕복이 사라져 **눈에 띄게 빨라진다.**

---

## 되돌리기

```bash
cd D:/JungPra/pythonpra/CGI/AnyDoor && git checkout -- configs run_inference.py run_gradio_demo.py
```

다시 적용:

```bash
cd D:/JungPra/pythonpra/CGI/AnyDoor && git apply ../_anydoor_backup/anydoor_10gb_fixes.patch
```

---

## 콜랩 패치와의 관계

**별개다.** 콜랩 노트북의 패치(`checkpoint` 재바인딩 · SDPA 교체 ·
fp16/GroupNorm · DINOv2 CPU 상주)는 T4의 VRAM이 아니라 **12.7GB 시스템 RAM**
제약에 대응한 것이다.

두 세트를 `patches/` 모듈로 합치면 로컬과 콜랩에서 같은 코드를 쓸 수 있다.
그때는 원본 파일을 수정하는 대신 런타임 몽키패치로 바꾸는 것이 낫다 — 그래야
`git diff` 가 우리가 쓴 코드만 보여준다.
