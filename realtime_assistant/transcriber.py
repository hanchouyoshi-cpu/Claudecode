"""faster-whisper によるローカル文字起こし。"""
import numpy as np

from config import Config


class Transcriber:
    def __init__(self, config: Config):
        from faster_whisper import WhisperModel  # 遅延import

        self.config = config
        # GPUがあれば cuda / float16 に変えると速い
        self.model = WhisperModel(config.whisper_model, device="auto", compute_type="int8")

    def transcribe(self, audio: np.ndarray) -> str:
        """float32 モノラル 16kHz の音声波形をテキストにする。"""
        segments, _info = self.model.transcribe(
            audio,
            language=self.config.language,
            beam_size=1,          # 速度優先
            vad_filter=True,
            condition_on_previous_text=False,
        )
        return "".join(seg.text for seg in segments).strip()
