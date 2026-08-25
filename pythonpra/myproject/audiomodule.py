# ============================================================
#  개인 AI 비서 - 오디오 입력 모듈
#  감지 대상: 박수 1번 / 박수 2번 (더블 클랩)
#  mediapipe AudioClassifier(YAMNet)는 윈도우에서 classify() 호출 시
#  access violation으로 크래시하는 문제가 확인되어 사용하지 않음.
#  대신 엔벨로프(순간 음량 급증) + 스펙트럼(고주파 대역 비율) 분석으로
#  직접 박수를 판별한다.
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
BASELINE_EMA_ALPHA = 0.02   # 주변 소음 바닥값 적응 속도 (느리게)
SPIKE_RATIO         = 3.0   # 바닥값 대비 이 배수 이상 튀어야 스파이크
MIN_ABS_RMS         = 0.02  # 너무 조용할 때 배수만으로 오인식되는 것 방지용 절대 하한
HIGH_BAND_HZ        = (1500, 7000)  # 박수 특유의 넓은 고주파 임팩트 대역
BAND_RATIO_THRESHOLD = 0.27  # 이 비율 이상이면 박수로 판정 (실측 후 조정 필요)
CLAP_COOLDOWN_SEC    = 0.25  # 한 번 인식 후 같은 박수의 잔향으로 중복 인식되는 것 방지

# 더블 클랩 판정 윈도우 
DOUBLE_CLAP_WINDOW_SEC = 1.0


class AudioModule:
    """
    마이크로부터 박수(클랩) 1번/2번을 감지하는 모듈

    감지 결과는 self.result 딕셔너리에 저장됨
    외부에서 self.result를 읽어서 명령 매핑에 사용
    """

    def __init__(self, device=None):
        self.device  = device
        self.running = False

        self._baseline_rms = MIN_ABS_RMS  # 초기 바닥값 추정치
        self._last_clap_time = 0.0
        self._pending_single_clap_time = None

        self.result = {
            "clap"        : False,  # 이번 블록에 박수 1번 발생 여부
            "double_clap" : False,  # 1.5초 안에 박수 2번 발생 여부
            "spike"       : False,  # [추가] 스펙트럼 검사 없이 순간 음량 급증만 감지 (시각 보조 판정용, 더 느슨함)
        }
        self._lock = threading.Lock()

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
    # [비활성화] 박수(클랩) 감지 로직 전체 - 지금 단계에서는 카메라(손/눈) 쪽만
    # 테스트하기 위해 꺼둠. 로직은 지우지 않고 주석 처리만 했으니 나중에 필요하면
    # 주석만 풀면 됨.
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
        double_clap = False
        is_spike = False

        # is_spike = rms > max(self._baseline_rms * SPIKE_RATIO, MIN_ABS_RMS)
        # if is_spike and (now - self._last_clap_time) > CLAP_COOLDOWN_SEC:
        #     band_ratio = self._high_band_ratio(mono)
        #     if band_ratio > BAND_RATIO_THRESHOLD:
        #         self._last_clap_time = now
        #
        #         # 더블 클랩으로 확정되면 clap/double_clap을 배타적으로 처리
        #         # (안 그러면 더블의 두 번째 탭에서 clap=True와 double_clap=True가 동시에 켜져
        #         #  main.py에서 예/아니오 신호가 같은 순간에 같이 발동해버림)
        #         if (self._pending_single_clap_time is not None and
        #                 now - self._pending_single_clap_time <= DOUBLE_CLAP_WINDOW_SEC):
        #             double_clap = True
        #             self._pending_single_clap_time = None
        #         else:
        #             clap = True
        #             self._pending_single_clap_time = now

        with self._lock:
            self.result["clap"]        = clap
            self.result["double_clap"] = double_clap
            self.result["spike"]       = is_spike

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

        print("[AudioModule] 종료")

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
                print("CLAP!", "DOUBLE!" if res["double_clap"] else "")
            time.sleep(0.05)
    except KeyboardInterrupt:
        audio.stop()
