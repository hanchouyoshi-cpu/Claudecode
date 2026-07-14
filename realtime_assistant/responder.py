"""Claude API で回答候補を生成する。"""
from collections import deque
from typing import Callable

from config import Config

SYSTEM_PROMPT = """あなたはリアルタイム会話支援アシスタントです。
ユーザーは今まさに会話(会議・商談・面接など)の最中で、あなたの提案をカンペとして見ながら話します。

相手の発言を受け取ったら、ユーザーが次に言うべき回答候補を{n}つ提案してください。

ルール:
- 各候補は「1.」「2.」のような番号付きで、そのまま口に出せる話し言葉で書く
- 候補ごとに方向性を変える(例: 丁寧に答える / 簡潔に答える / 逆に質問で返す)
- 1候補は1〜3文程度。長い説明はしない
- 事前資料が与えられている場合は、その内容を根拠にする。資料にない事実は捏造しない
- 前置きや解説は不要。候補のみを出力する"""


class Responder:
    def __init__(self, config: Config):
        import anthropic  # 遅延import: --text モード以外の構文チェックを軽くする

        self.config = config
        self.client = anthropic.Anthropic()
        self.history: deque[tuple[str, str]] = deque(maxlen=config.history_size)

        system = SYSTEM_PROMPT.format(n=config.num_candidates)
        if config.extra_instructions:
            system += "\n\n追加指示:\n" + config.extra_instructions
        self.system_blocks = [{"type": "text", "text": system}]
        context = config.load_context()
        if context:
            self.system_blocks.append({
                "type": "text",
                "text": "事前資料:\n" + context,
            })
        # 安定した接頭辞(システム+資料)をキャッシュして低遅延・低コスト化
        self.system_blocks[-1]["cache_control"] = {"type": "ephemeral"}

    def add_utterance(self, speaker: str, text: str) -> None:
        """会話履歴に発話を追加する。speaker は 'self'(自分) or 'other'(相手)。"""
        self.history.append((speaker, text))

    def suggest(self, on_delta: Callable[[str], None]) -> str:
        """現在の履歴に基づいて回答候補を生成し、ストリーミングで on_delta に渡す。"""
        transcript = "\n".join(
            ("相手: " if spk == "other" else "自分: ") + text
            for spk, text in self.history
        )
        messages = [{
            "role": "user",
            "content": f"ここまでの会話:\n{transcript}\n\n相手の最後の発言への回答候補を出してください。",
        }]

        parts: list[str] = []
        with self.client.messages.stream(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            output_config={"effort": self.config.effort},
            system=self.system_blocks,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                parts.append(text)
                on_delta(text)
        return "".join(parts)
