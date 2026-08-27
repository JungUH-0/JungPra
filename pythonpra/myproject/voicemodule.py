# ============================================================
#  개인 AI 비서 - 음성 입력 모듈 (웨이크워드 감지 + 명령 녹음/변환)
#  마이크 오디오를 일정 주기로 로컬 Whisper(faster-whisper)에 넘겨서
#  웨이크워드가 들렸는지 확인한다.
#
#  명령을 녹음하는 방식은 트리거 종류에 따라 다르다:
#  - 웨이크워드로 시작한 경우: 무음(VAD)이 일정 시간 이어지면 자동으로 녹음 종료
#    ("말하고 나면 알아서 끝남")
#  - 손등 5초 유지(제스처)로 시작한 경우: main.py가 손등 자세가 풀리는 순간
#    stop_command_recording()을 호출해서 종료시킴 ("무전기 방식" - 누르고 있는
#    동안만 듣고, 떼면 끝)
#  녹음이 끝나면 Whisper로 텍스트 변환까지 여기서 끝내고, 그 결과(문장)를
#  self.result["command_text"]에 담아둔다. 그걸 LLM에 넘겨서 실행하는 건
#  main.py의 몫 (commandmodule.execute_text 사용).
# ============================================================

import time
import threading
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE   = 16000
BLOCK_SEC     = 0.1                              # 마이크 콜백 주기
BLOCK_SAMPLES = int(SAMPLE_RATE * BLOCK_SEC)

CHUNK_SEC          = 3.0   # 웨이크워드 검사에 쓸 오디오 길이(최근 몇 초를 볼지)
CHECK_INTERVAL_SEC = 1.5   # 웨이크워드 검사 반복 주기

WAKE_WORD  = "웨이크"  # [수정 예정] 아직 확정 아님 - 나중에 바뀔 수 있음
MODEL_SIZE = "medium"

BUFFER_SAMPLES = int(SAMPLE_RATE * CHUNK_SEC)

# [추가] 명령 녹음(무음 감지) 설정
VAD_RMS_THRESHOLD = 0.02   # 이 이상이면 "말하는 중"으로 판단 (마이크 감도에 따라 조정 필요)
VAD_SILENCE_SEC    = 1.2   # 웨이크워드로 시작한 경우, 이 시간 동안 조용하면 자동 종료
MAX_RECORD_SEC      = 15.0  # 무전기 방식이든 무음감지든, 이 시간 넘으면 안전하게 강제 종료
MIN_RECORD_SEC       = 0.3  # 이보다 짧으면(실수로 트리거된 경우 등) 변환 없이 무시


class VoiceModule:
    """
    마이크로부터 웨이크워드를 감지하고, 트리거된 뒤에는 명령을 녹음해서
    Whisper로 텍스트 변환까지 수행하는 모듈.
    감지/변환 결과는 self.result 딕셔너리에 저장됨 - 외부에서 get_result()로 읽는다.
    """

    def __init__(self, device=None):
        self.device  = device
        self.running = False

        # [추가] 웨이크워드 검사용 - 최근 CHUNK_SEC초 분량을 담아두는 링 버퍼
        self._buffer = np.zeros(BUFFER_SAMPLES, dtype=np.float32)
        self._buffer_lock = threading.Lock()

        # [추가] 명령 녹음 상태
        self._recording       = False
        self._record_buffer   = []    # 녹음 중 들어오는 오디오 블록들을 순서대로 담음
        self._record_mode     = None  # "vad"(웨이크워드) / "manual"(손등 무전기 방식)
        self._record_started  = None  # 녹음이 시작된 시각 (MAX_RECORD_SEC 안전장치용)
        self._last_speech_time = None  # VAD용 - 마지막으로 말소리(RMS 임계값 이상)가 감지된 시각

        self.result = {
            "wake_word"    : False,  # 방금 검사 주기에 웨이크워드가 감지됐는지 (1회성)
            "last_text"    : "",     # 마지막으로 인식된 텍스트 (디버그/화면 표시용)
            "recording"    : False,  # 지금 명령을 녹음 중인지
            "command_text" : None,   # 녹음이 끝나고 변환된 명령 문장 (소비 후 None으로 리셋해줘야 함)
        }
        self._lock = threading.Lock()

        print("[VoiceModule] Whisper 모델 로딩 중 (최초 1회, 시간이 좀 걸릴 수 있음)...")
        self._model = WhisperModel(MODEL_SIZE, device="cuda", compute_type="float16")
        print("[VoiceModule] 모델 로딩 완료")

    # ── 내부: 마이크 콜백 (블록 단위로 호출됨) ───────────────
    def _audio_callback(self, indata, frames, time_info, status):
        mono = indata[:, 0] if indata.ndim > 1 else indata

        with self._buffer_lock:
            # 웨이크워드 검사용 링 버퍼 - 오래된 샘플을 밀어내고 새 샘플을 뒤에 채움
            self._buffer = np.concatenate([self._buffer[len(mono):], mono])

            if self._recording:
                self._record_buffer.append(mono.copy())
                rms = float(np.sqrt(np.mean(mono.astype(np.float64) ** 2)))
                if rms > VAD_RMS_THRESHOLD:
                    self._last_speech_time = time.time()

    # ── 외부에서 호출: 명령 녹음 시작 ─────────────────────────
    def start_command_recording(self, mode):
        """
        mode="manual": 손등 무전기 방식 - main.py가 stop_command_recording()을
                       직접 호출해줘야 끝남 (무음 감지로 자동 종료되지 않음)
        mode="vad"   : 웨이크워드 방식 - 조용해지면 자동으로 끝남
        """
        with self._buffer_lock:
            self._record_buffer   = []
            self._recording        = True
            self._record_mode      = mode
            self._record_started   = time.time()
            self._last_speech_time = time.time()
        with self._lock:
            self.result["recording"] = True

    # ── 외부에서 호출: 명령 녹음 종료 + 변환 ───────────────────
    def stop_command_recording(self):
        """녹음을 멈추고 지금까지 모은 오디오를 Whisper로 변환해서 command_text에 반영"""
        with self._buffer_lock:
            chunks = self._record_buffer
            self._record_buffer = []
            self._recording = False
            self._record_mode = None

        with self._lock:
            self.result["recording"] = False

        if not chunks:
            return
        audio = np.concatenate(chunks)
        if len(audio) < SAMPLE_RATE * MIN_RECORD_SEC:
            return  # 너무 짧으면(실수로 트리거된 경우 등) 변환 없이 무시

        segments, _ = self._model.transcribe(audio, language="ko", vad_filter=True)
        text = "".join(seg.text for seg in segments).strip()
        if text:
            with self._lock:
                self.result["command_text"] = text
            print(f"[VoiceModule] 명령 인식: \"{text}\"")

    def clear_command_text(self):
        """main.py가 command_text를 처리한 뒤 호출 - 다음 녹음까지 재사용되지 않게 비움"""
        with self._lock:
            self.result["command_text"] = None

    # ── 메인 루프 ─────────────────────────────────────────
    def run(self):
        self.running = True
        print(f"[VoiceModule] 시작 - 웨이크워드 '{WAKE_WORD}' 대기 중")

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            blocksize=BLOCK_SAMPLES,
            dtype="float32",
            device=self.device,
            callback=self._audio_callback,
        ):
            while self.running:
                time.sleep(CHECK_INTERVAL_SEC)

                # [추가] 녹음 중이면: 안전 시간 초과 체크 + (vad 모드일 때만) 무음 자동 종료
                if self._recording:
                    elapsed = time.time() - self._record_started
                    if elapsed > MAX_RECORD_SEC:
                        self.stop_command_recording()
                    elif (self._record_mode == "vad" and self._last_speech_time and
                            time.time() - self._last_speech_time > VAD_SILENCE_SEC):
                        self.stop_command_recording()
                    continue  # 녹음 중엔 웨이크워드 검사를 건너뜀

                # 웨이크워드 검사 (녹음 중이 아닐 때만)
                with self._buffer_lock:
                    audio = self._buffer.copy()

                segments, _ = self._model.transcribe(
                    audio, language="ko", vad_filter=True,
                )
                text = "".join(seg.text for seg in segments).strip()

                wake_detected = bool(text) and WAKE_WORD in text

                with self._lock:
                    self.result["wake_word"] = wake_detected
                    self.result["last_text"] = text

                if wake_detected:
                    print(f"[VoiceModule] 웨이크워드 감지! (\"{text}\") - 명령 녹음 시작")
                    self.start_command_recording(mode="vad")

        print("[VoiceModule] 종료")

    def get_result(self):
        """현재 감지/변환 결과 반환 (스레드 안전)"""
        with self._lock:
            return dict(self.result)

    def stop(self):
        self.running = False


# ── 테스트용 실행 ─────────────────────────────────────────
if __name__ == "__main__":
    voice = VoiceModule()

    t = threading.Thread(target=voice.run, daemon=True)
    t.start()

    try:
        while True:
            res = voice.get_result()
            if res["command_text"]:
                print(f"[명령 완료] {res['command_text']}")
                voice.clear_command_text()
            time.sleep(0.5)
    except KeyboardInterrupt:
        voice.stop()
