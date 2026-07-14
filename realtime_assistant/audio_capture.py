"""音声キャプチャ (Windows 専用)。

- マイク入力: 自分の声
- WASAPI ループバック: PC で再生されている音 = Web会議の相手の声

エネルギーベースの簡易VADで発話単位に区切り、(speaker, np.ndarray) を
キューに積む。文字起こしは transcriber 側で行う。
"""
import queue
import threading

import numpy as np

from config import Config


class _CaptureThread(threading.Thread):
    """1つの入力デバイスを読み続け、発話単位に切り出すスレッド。"""

    def __init__(self, config: Config, speaker: str, device_index: int,
                 device_rate: int, channels: int,
                 out_queue: "queue.Queue[tuple[str, np.ndarray]]", pa):
        super().__init__(daemon=True, name=f"capture-{speaker}")
        self.config = config
        self.speaker = speaker
        self.device_index = device_index
        self.device_rate = device_rate
        self.channels = channels
        self.out_queue = out_queue
        self.pa = pa
        self.stop_flag = threading.Event()

    def run(self) -> None:
        import pyaudiowpatch as pyaudio

        cfg = self.config
        frames_per_buffer = int(self.device_rate * cfg.frame_ms / 1000)
        stream = self.pa.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.device_rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=frames_per_buffer,
        )

        silence_frames_limit = cfg.silence_ms // cfg.frame_ms
        min_frames = cfg.min_utterance_ms // cfg.frame_ms
        buf: list[np.ndarray] = []
        silence_count = 0

        try:
            while not self.stop_flag.is_set():
                data = stream.read(frames_per_buffer, exception_on_overflow=False)
                frame = np.frombuffer(data, dtype=np.float32)
                if self.channels > 1:
                    frame = frame.reshape(-1, self.channels).mean(axis=1)

                if np.sqrt(np.mean(frame ** 2)) >= cfg.energy_threshold:
                    buf.append(frame)
                    silence_count = 0
                elif buf:
                    buf.append(frame)
                    silence_count += 1
                    if silence_count >= silence_frames_limit:
                        # 発話終了
                        if len(buf) - silence_count >= min_frames:
                            audio = np.concatenate(buf)
                            self.out_queue.put((self.speaker, self._resample(audio)))
                        buf = []
                        silence_count = 0
        finally:
            stream.stop_stream()
            stream.close()

    def _resample(self, audio: np.ndarray) -> np.ndarray:
        """デバイスのレートから whisper 用 16kHz へ線形補間で変換する。"""
        target = self.config.sample_rate
        if self.device_rate == target:
            return audio
        n = int(len(audio) * target / self.device_rate)
        x_old = np.linspace(0.0, 1.0, num=len(audio), endpoint=False)
        x_new = np.linspace(0.0, 1.0, num=n, endpoint=False)
        return np.interp(x_new, x_old, audio).astype(np.float32)


class AudioCapture:
    """マイク+ループバックの2系統を起動し、発話キューを提供する。"""

    def __init__(self, config: Config):
        import pyaudiowpatch as pyaudio

        self.config = config
        self.utterances: "queue.Queue[tuple[str, np.ndarray]]" = queue.Queue()
        self.pa = pyaudio.PyAudio()
        self.threads: list[_CaptureThread] = []

        # 自分の声: 既定のマイク
        mic = self.pa.get_default_input_device_info()
        self.threads.append(_CaptureThread(
            config, "self", mic["index"], int(mic["defaultSampleRate"]),
            min(int(mic["maxInputChannels"]), 2), self.utterances, self.pa,
        ))

        # 相手の声: 既定出力デバイスの WASAPI ループバック
        try:
            loopback = self.pa.get_default_wasapi_loopback()
            self.threads.append(_CaptureThread(
                config, "other", loopback["index"], int(loopback["defaultSampleRate"]),
                min(int(loopback["maxInputChannels"]), 2), self.utterances, self.pa,
            ))
        except OSError:
            print("[warn] WASAPIループバックが見つかりません。相手側音声は取得しません。")

    def start(self) -> None:
        for t in self.threads:
            t.start()

    def stop(self) -> None:
        for t in self.threads:
            t.stop_flag.set()
        for t in self.threads:
            t.join(timeout=2)
        self.pa.terminate()
