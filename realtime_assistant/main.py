"""リアルタイム回答生成アシスタント (フェーズ1 MVP)

使い方:
  音声モード (Windows):  python main.py --context docs.md
  テキストモード (動作確認用): python main.py --text --context docs.md
"""
import argparse
import sys
import threading

from config import Config
from responder import Responder


def text_mode(config: Config) -> None:
    """マイクを使わず、相手の発言をキーボードで入力して試すモード。"""
    responder = Responder(config)
    print("テキストモード。相手の発言を入力してください (Ctrl+C で終了)")
    while True:
        try:
            said = input("\n相手> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n終了します。")
            return
        if not said:
            continue
        responder.add_utterance("other", said)
        print("--- 回答候補 ---")
        full = responder.suggest(lambda t: print(t, end="", flush=True))
        print()
        responder.add_utterance("self", "(候補を参考に回答)" if full else "")


def audio_mode(config: Config) -> None:
    """マイク+ループバックから文字起こしし、オーバーレイに候補を表示する。"""
    from audio_capture import AudioCapture
    from overlay import Overlay
    from transcriber import Transcriber

    overlay = Overlay()
    responder = Responder(config)
    transcriber = Transcriber(config)
    capture = AudioCapture(config)

    def worker() -> None:
        while True:
            speaker, audio = capture.utterances.get()
            text = transcriber.transcribe(audio)
            if not text:
                continue
            overlay.post_transcript(speaker, text)
            responder.add_utterance(speaker, text)
            if speaker == "other":
                # 相手の発話が確定したら回答候補を生成
                overlay.post_suggestion_reset()
                try:
                    responder.suggest(overlay.post_suggestion_delta)
                except Exception as e:  # APIエラーでもループは止めない
                    overlay.post_suggestion_delta(f"[エラー] {e}\n")

    threading.Thread(target=worker, daemon=True).start()
    capture.start()
    try:
        overlay.run()
    finally:
        capture.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="リアルタイム回答生成アシスタント")
    parser.add_argument("--text", action="store_true",
                        help="テキスト入力モード(音声デバイス不要の動作確認用)")
    parser.add_argument("--context", default="", help="事前資料ファイル (md/txt)")
    parser.add_argument("--model", default="", help="Claudeモデル ID の上書き")
    parser.add_argument("--effort", default="", choices=["", "low", "medium", "high"],
                        help="回答生成の思考量 (既定: low=速度優先)")
    args = parser.parse_args()

    config = Config()
    if args.context:
        config.context_file = args.context
    if args.model:
        config.model = args.model
    if args.effort:
        config.effort = args.effort

    if args.text:
        text_mode(config)
    else:
        if sys.platform != "win32":
            print("音声モードは Windows 専用です。--text で動作確認できます。")
            sys.exit(1)
        audio_mode(config)


if __name__ == "__main__":
    main()
