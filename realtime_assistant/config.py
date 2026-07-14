"""設定。環境変数または起動引数で上書きできる。"""
from dataclasses import dataclass, field
import os


@dataclass
class Config:
    # Claude API
    model: str = os.environ.get("RTA_MODEL", "claude-opus-4-8")
    max_tokens: int = 1024
    effort: str = "low"  # 速度優先。精度を上げたい場合は "medium" / "high"

    # 文字起こし (faster-whisper)
    whisper_model: str = os.environ.get("RTA_WHISPER_MODEL", "small")
    language: str = "ja"

    # 音声キャプチャ
    sample_rate: int = 16000
    frame_ms: int = 30            # 1フレームの長さ
    silence_ms: int = 800         # これ以上無音が続いたら発話終了とみなす
    min_utterance_ms: int = 300   # これより短い発話は無視
    energy_threshold: float = 0.01  # RMSがこれ未満なら無音扱い

    # 事前資料(回答の根拠にするファイル)。Markdown/テキスト
    context_file: str = os.environ.get("RTA_CONTEXT_FILE", "")

    # 会話履歴として保持する発話数
    history_size: int = 20

    # 回答候補の数
    num_candidates: int = 3

    extra_instructions: str = field(default="")

    def load_context(self) -> str:
        if self.context_file and os.path.exists(self.context_file):
            with open(self.context_file, encoding="utf-8") as f:
                return f.read()
        return ""
