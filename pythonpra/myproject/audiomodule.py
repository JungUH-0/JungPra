# ============================================================
#  개인 AI 비서 - 오디오 입력 모듈
#  감지 대상: 박수
#  mediapipe AudioClassifier(YAMNet)는 윈도우에서 classify() 호출 시
#  access violation으로 크래시하는 문제가 확인되어 사용하지 않음.
#  대신 엔벨로프(순간 음량 급증) + 스펙트럼(고주파 대역 비율) 분석으로
#  직접 박수를 판별한다.
#
#  [수정] 박수의 역할이 바뀜: 예전에는 예/아니오 신호였지만(지금은 엄지척/
#  엄지다운이 그 역할을 가져감), 이제는 손동작 모드 <-> 전신 포즈 모드를
#  전환하는 신호로만 쓴다. 그래서 단발/더블 구분도 필요 없어져서 없앴다.
#  오인식 방지는 main.py에서 "박수 소리 + 양손 모임(시각 확인)"을 함께
#  요구하는 방식으로 처리한다.
# ============================================================

import time
import threading
import numpy as np
import sounddevice as sd

# ── 오디오 캡처 설정 ───────────────────────────────────────
SAMPLE_RATE   = 16000
BLOCK_MS      = 30
BLOCK_SAMPLES = int(SAMPLE_RATE * BLOCK_MS / 1000)

# ── 박수(클랩) 판별 설정 ───────────────────────────────────
# [수정] 예전엔 박수 하나로 예/아니오가 바로 발동해서 오인식을 막으려고 엄격하게
# 잡아뒀지만, 지금은 "박수 + 양손 모임(시각 확인)"을 둘 다 요구하므로 소리 쪽은
# 훨씬 느슨하게 풀어도 안전하다. (인식이 잘 안 된다는 피드백에 따라 완화)
BASELINE_EMA_ALPHA = 0.02   # 주변 소음 바닥값 적응 속도 (느리게)
SPIKE_RATIO         = 2.0   # 바닥값 대비 이 배수 이상 튀어야 스파이크
# [수정] 실측 로그(debug_audio.txt) 기준으로 다시 조정함.
#  - 진짜 박수: rms 0.03~0.29 / peak 0.2~1.0 / band_ratio 0.5~0.95
#  - 키보드·마우스 클릭 등 잡음: rms 0.009 안팎 / peak 0.03 안팎 (고주파 비율은 높음)
# 둘을 가르는 건 고주파 비율이 아니라 "음량(특히 peak)"이었다. 그래서 값을 다시 올림.
MIN_ABS_RMS         = 0.02
HIGH_BAND_HZ        = (1500, 7000)  # 박수 특유의 넓은 고주파 임팩트 대역
BAND_RATIO_THRESHOLD = 0.25
CLAP_COOLDOWN_SEC    = 0.25  # 한 번 인식 후 같은 박수의 잔향으로 중복 인식되는 것 방지

# [수정] 30ms 블록 RMS만 보면 짧은 충격음이 두 블록에 나뉘며 희석돼 놓치기 쉬운데,
# 박수는 순간 최대값(peak)이 확실히 튀므로 peak을 주 판별 기준으로 삼는다.
# 실측상 진짜 박수는 peak 0.2 이상, 잡음은 0.05 이하라 그 사이에 문턱을 둠.
PEAK_ABS_THRESHOLD = 0.12

# [추가] 진단용 - 박수 후보(스파이크)가 잡힐 때마다 실제 수치를 파일로 남김.
# 인식이 잘 안 될 때 이 파일을 보고 어느 조건에서 걸러지는지 확인해서 조정한다.
DEBUG_LOG_PATH = "debug_audio.txt"


class AudioModule:
    """
    마이크로부터 박수를 감지하는 모듈 (모드 전환 신호용)

    감지 결과는 self.result 딕셔너리에 저장됨
    외부에서 self.result를 읽어서 모드 전환 판정에 사용
    """

    def __init__(self, device=None):
        self.device  = device
        self.running = False

        self._baseline_rms = MIN_ABS_RMS  # 초기 바닥값 추정치
        self._last_clap_time = 0.0

        self.result = {
            "clap"  : False,  # 이번 블록에 박수가 감지됐는지 (음량 급증 + 고주파 비율 둘 다 통과)
            "spike" : False,  # 스펙트럼 검사 없이 순간 음량 급증만 감지 (더 느슨한 보조 신호)
        }
        self._lock = threading.Lock()

        # [추가] 진단용 로그 - 오디오 콜백에서 직접 파일을 쓰면 녹음이 끊길 수 있어서,
        # 콜백은 메모리에 쌓기만 하고 실제 파일 쓰기는 run() 루프에서 처리한다.
        self._debug_lines = []
        self._debug_lock  = threading.Lock()
        try:
            with open(DEBUG_LOG_PATH, "w", encoding="utf-8") as f:
                f.write(f"[박수 진단 로그 시작 @ {time.strftime('%H:%M:%S')}]\n")
                f.write(f"설정: SPIKE_RATIO={SPIKE_RATIO} MIN_ABS_RMS={MIN_ABS_RMS} "
                        f"PEAK_ABS={PEAK_ABS_THRESHOLD} BAND_RATIO={BAND_RATIO_THRESHOLD}\n")
        except OSError:
            pass

    # ── 내부: 고주파 대역 에너지 비율 계산 ───────────────────
    def _high_band_ratio(self, block):
        n = len(block)
        spectrum = np.fft.rfft(block * np.hanning(n))
        power    = np.abs(spectrum) ** 2
        freqs    = np.fft.rfftfreq(n, d=1.0 / SAMPLE_RATE)

        band_mask = (freqs >= HIGH_BAND_HZ[0]) & (freqs <= HIGH_BAND_HZ[1])
        total = power.sum() + 1e-9
        band  = power[band_mask].sum()
        return band / total

    # ── 내부: 마이크 콜백 (블록 단위로 호출됨) ───────────────
    # [재활성화] 모드 전환 신호로 쓰기 위해 박수 감지를 다시 켬.
    # [수정] 단발/더블 구분은 제거 - 조건을 통과한 박수는 전부 clap=True로 처리한다.
    # (예전엔 단발=예, 더블=아니오였지만 그 역할은 엄지척/엄지다운으로 옮겨갔음)
    def _audio_callback(self, indata, frames, time_info, status):
        mono = indata[:, 0] if indata.ndim > 1 else indata
        rms  = float(np.sqrt(np.mean(mono.astype(np.float64) ** 2)) + 1e-9)
        now  = time.time()

        # 큰 스파이크가 아닐 때만 바닥값을 천천히 적응시킴
        if rms < self._baseline_rms * (SPIKE_RATIO * 0.6):
            self._baseline_rms = (
                (1 - BASELINE_EMA_ALPHA) * self._baseline_rms + BASELINE_EMA_ALPHA * rms
            )

        clap = False

        # 1차: 순간 음량이 급증했는지
        # [수정] RMS 조건에 더해 블록 내 최대 진폭(peak) 조건을 OR로 추가.
        # 박수는 아주 짧은 충격음이라 30ms 블록 RMS로는 희석돼 놓치기 쉬운데,
        # peak은 확실히 튀기 때문에 짧은 박수도 잡힌다.
        peak = float(np.max(np.abs(mono))) if len(mono) else 0.0
        rms_spike  = rms > max(self._baseline_rms * SPIKE_RATIO, MIN_ABS_RMS)
        peak_spike = peak > PEAK_ABS_THRESHOLD
        is_spike = rms_spike or peak_spike

        if is_spike and (now - self._last_clap_time) > CLAP_COOLDOWN_SEC:
            # 2차: 박수 특유의 넓은 고주파 임팩트가 있는지 (말소리/문 닫는 소리 등 걸러냄)
            band_ratio = self._high_band_ratio(mono)
            passed = band_ratio > BAND_RATIO_THRESHOLD
            if passed:
                self._last_clap_time = now
                clap = True

            # [추가] 스파이크가 잡힐 때마다 실제 수치를 남겨둠 - 인식이 안 될 때
            # "소리는 잡혔는데 고주파 조건에서 걸러진 것"인지 바로 확인할 수 있음
            with self._debug_lock:
                self._debug_lines.append(
                    f"{time.strftime('%H:%M:%S')} rms={rms:.4f} peak={peak:.4f} "
                    f"baseline={self._baseline_rms:.4f} band_ratio={band_ratio:.3f} "
                    f"→ {'박수 인정' if passed else '고주파 부족으로 제외'}"
                )

        with self._lock:
            self.result["clap"]  = clap
            self.result["spike"] = is_spike

    # ── 메인 루프 ─────────────────────────────────────────
    def run(self):
        """마이크 캡처 루프 실행 (메인 스레드 or 별도 스레드에서 호출)"""
        self.running = True
        print("[AudioModule] 시작 - 박수 감지 대기 중")

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            blocksize=BLOCK_SAMPLES,
            dtype="float32",
            device=self.device,
            callback=self._audio_callback,
        ):
            while self.running:
                time.sleep(0.05)
                self._flush_debug()

        self._flush_debug()
        print("[AudioModule] 종료")

    # ── 내부: 콜백이 쌓아둔 진단 로그를 파일로 내보냄 ──────────
    def _flush_debug(self):
        with self._debug_lock:
            if not self._debug_lines:
                return
            lines = self._debug_lines
            self._debug_lines = []
        try:
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except OSError:
            pass

    def get_result(self):
        """현재 감지 결과 반환 (스레드 안전)"""
        with self._lock:
            return dict(self.result)

    def stop(self):
        self.running = False


# ── 테스트용 실행 ─────────────────────────────────────────
if __name__ == "__main__":
    audio = AudioModule()

    t = threading.Thread(target=audio.run, daemon=True)
    t.start()

    try:
        while True:
            res = audio.get_result()
            if res["clap"]:
                print("CLAP!")
            time.sleep(0.05)
    except KeyboardInterrupt:
        audio.stop()
