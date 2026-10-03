# 진행 중 실패·이슈 기록

환경: anomalib 2.6.2 / torch 2.12 / lightning 2.6.6 / Windows / RTX 3080
기록 기준일: 2026-10-02

## 해결한 실패

### 1. EfficientAD `model_size="s"` → ValueError
- 증상: `ValueError: 's' is not a valid EfficientAdModelSize` (모델 생성 단계)
- 원인: anomalib 의 `EfficientAdModelSize` 값은 `"small"` / `"medium"` 이다. (docstring 은 `S`/`M`)
- 조치: `common.py` 의 `EFFICIENTAD_CONFIG = dict(model_size="small")`

### 2. EfficientAD 체크포인트 저장 실패 (pickle 오류) — anomalib 2.6.2 버그
- 증상: 100 step 학습이 끝난 직후 `AttributeError: Can't get local object
  'MaxStepsProgressCallback.on_train_start.<locals>._FixedRichProgressBar'`
  (ModelCheckpoint -> `_atomic_save`)
- 원인: `max_steps` 로 학습하면 `Engine` 이 자동으로 붙이는 `MaxStepsProgressCallback` 이
  진행바 객체의 `__class__` 를 함수 안에서 만든 지역 클래스로 바꾼다. 체크포인트 저장 때 pickle 불가.
  이 콜백은 진행바의 "Epoch X/-2" 표시만 고치는 외관용이다.
- 조치: `common.py` 에서 `anomalib.engine.engine.MaxStepsProgressCallback` 을 아무 동작 없는
  콜백으로 교체. 학습 결과에는 영향 없음, 진행바 epoch 표시만 원래대로 나온다.
  (site-packages 는 수정하지 않음. `max_epochs` 로 바꾸는 방법은 step 수가 장수에 따라 달라져 불가)

### 3. `UnicodeEncodeError: 'cp949' ... '•'`
- 증상: 위 2번 실패 뒤 예외 정리 과정에서 추가로 발생
- 원인: 출력을 파일로 리다이렉트하면 cp949 인코딩이 되어 rich 진행바의 `•` 를 못 쓴다.
- 조치: 별도 수정 없음 (2번의 부수 효과). 파일로 리다이렉트할 때는 `PYTHONUTF8=1` 을 준다.

## 작업 방식상 문제 (코드 아님)
- PowerShell 5.1 의 `*>` 리다이렉트는 파이썬 출력이 끝날 때까지 파일에 거의 쓰이지 않아
  진행 확인이 안 됐다. 이후 Bash 리다이렉트(`> log 2>&1`)로 대체.

## 확인 필요 (미해결)
- **[코드] EfficientAD 에서만 `engine.test` 의 Image AUROC 와 `engine.predict` 로 모은 점수의 AUROC 가 다르다.**
  - 증상: 같은 체크포인트로 test() = 0.6436, predict 점수를 sklearn 으로 계산 = 0.7186 (n=110).
    predict 를 두 번 돌려도 같은 값이라 비결정성은 아님. PaDiM·PatchCore 는 1e-7 수준으로 일치.
  - 영향: `results/scores/efficientad_*.csv` 로 그리는 ROC 곡선 범례의 AUROC 가
    CSV·막대그래프의 image_auroc(= anomalib test 값)와 다르게 나온다.
    benchmark.py 는 불일치 시 `[검증] ... 불일치` 를 출력하고 계속 진행한다(중단하지 않음).
  - 소스 확인으로 배제한 것: 검증 재실행(EfficientAD 는 `_should_run_validation` 이 False),
    test_step 과 predict_step 의 차이(둘 다 `self.model(batch.image)` 로 동일),
    PostProcessor/Evaluator 콜백 순서(PostProcessor 가 먼저).
  - 미확정: 원인. 코드만으로는 특정하지 못했고, 추가 진단 실행이 필요하다.
  - **2026-10-03 갱신: 본 실행(70,000 step, 100/200/300장)에서는 재현되지 않음.**
    EfficientAD 3회 모두 auroc_diff 5.7e-08 이하로 일치. 불일치는 smoke(100 step)에서만 관찰됨.
    smoke 의 불일치는 학습이 거의 안 된 상태(점수 분포가 정규화 범위를 벗어남)와 관련이 있을 것으로
    추정하지만 확인하지 않았다. 본 실행 결과에는 영향 없음 -> 코드 수정 없이 종결.
- PaDiM Image AUROC 0.7152 (원본 391장, smoke). Pixel AUROC 0.9718 에 비해 낮다.
  본 실행 결과가 나오면 점검한다. test 성능을 보고 설정을 바꾸지는 않는다 (명세 3장).
- Windows 에서 `num_workers=4` 는 데이터 로더마다 워커 4개가 anomalib 을 다시 import 해서
  워커당 약 20초씩 낭비된다. `--num-workers 0` 권장.
- (정리 완료) 시험 실행 로그 `smoke_log*.txt`, `inspect_check_log.txt` 와 `results/smoke/` 는 2026-10-03 삭제함.
