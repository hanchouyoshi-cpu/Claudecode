#!/usr/bin/env python3
"""音声自動生成: VOICEVOX の HTTP API で台本を読み上げ音声(WAV)にする。

Mac の VOICEVOX アプリを起動しておくと、裏で音声合成エンジンが
http://127.0.0.1:50021 で待ち受ける。このスクリプトはそこに台本を送り、
1つのWAVファイルに結合して出力する。標準ライブラリのみで動作。

準備:
  1. https://voicevox.hiroshiba.jp/ から Mac 版をダウンロード・起動しておく
  2. 使うキャラクターの利用規約を確認し、動画にクレジット表記
     (例: VOICEVOX:ずんだもん)

使い方:
  python3 automation/tts_voicevox.py output/scripts/20260713-1200.md
  python3 automation/tts_voicevox.py --speaker 3 --speed 1.1 台本.md

出力: 入力ファイルと同名の .wav (例: output/scripts/20260713-1200.wav)
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import urllib.parse
import urllib.request
import wave

ENGINE = "http://127.0.0.1:50021"

# 主なスピーカーID(/speakers で全一覧を取得可能)
#   3: ずんだもん(ノーマル)  2: 四国めたん(ノーマル)  13: 青山龍星


def engine_post(path: str, params: dict, body: bytes | None = None,
                content_type: str = "application/json") -> bytes:
    url = f"{ENGINE}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, data=body or b"", method="POST")
    req.add_header("Content-Type", content_type)
    with urllib.request.urlopen(req, timeout=120) as res:
        return res.read()


def extract_narration(markdown: str) -> list[str]:
    """台本Markdownから読み上げ対象の文だけを取り出す。"""
    lines = []
    for line in markdown.splitlines():
        line = line.strip()
        # 見出し・スライド指示・箇条書き記号・区切り線は読み上げない
        if not line or line.startswith(("#", "---", "|")):
            continue
        line = re.sub(r"\[スライド[::][^\]]*\]", "", line)
        line = re.sub(r"^[-*・>]\s*", "", line)
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)  # 太字マーカー除去
        line = line.strip()
        if line:
            lines.append(line)

    # 文単位に分割(合成品質と進捗表示のため)
    sentences = []
    for line in lines:
        for s in re.split(r"(?<=[。!?!?])", line):
            s = s.strip()
            if s:
                sentences.append(s)
    return sentences


def synthesize(text: str, speaker: int, speed: float) -> bytes:
    query = json.loads(engine_post("/audio_query", {"text": text, "speaker": speaker}))
    query["speedScale"] = speed
    return engine_post(
        "/synthesis", {"speaker": speaker}, json.dumps(query).encode("utf-8")
    )


def concat_wavs(wav_blobs: list[bytes], out_path: str) -> None:
    params = None
    frames = []
    for blob in wav_blobs:
        with wave.open(io.BytesIO(blob), "rb") as w:
            if params is None:
                params = w.getparams()
            frames.append(w.readframes(w.getnframes()))
    with wave.open(out_path, "wb") as out:
        out.setparams(params)
        for f in frames:
            out.writeframes(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="VOICEVOXで台本を音声化")
    parser.add_argument("script_file", help="台本ファイル(.md / .txt)")
    parser.add_argument("--speaker", type=int, default=3, help="スピーカーID(デフォルト3=ずんだもん)")
    parser.add_argument("--speed", type=float, default=1.1, help="話速(デフォルト1.1)")
    args = parser.parse_args()

    try:
        urllib.request.urlopen(f"{ENGINE}/version", timeout=5)
    except OSError:
        sys.exit(
            "エラー: VOICEVOXエンジンに接続できません。\n"
            "Mac の VOICEVOX アプリを起動してから再実行してください。\n"
            "(アプリを起動すると http://127.0.0.1:50021 でエンジンが動きます)"
        )

    with open(args.script_file, encoding="utf-8") as f:
        sentences = extract_narration(f.read())
    if not sentences:
        sys.exit("エラー: 読み上げ対象の文が見つかりませんでした。")

    print(f"{len(sentences)}文を合成します(speaker={args.speaker}, speed={args.speed})...")
    blobs = []
    for i, sentence in enumerate(sentences, 1):
        blobs.append(synthesize(sentence, args.speaker, args.speed))
        print(f"  [{i}/{len(sentences)}] {sentence[:30]}", file=sys.stderr)

    out_path = re.sub(r"\.(md|txt)$", "", args.script_file) + ".wav"
    concat_wavs(blobs, out_path)
    print(f"音声を出力しました: {out_path}")
    print("次のステップ: CapCut / DaVinci Resolve に読み込んでスライドと合わせる")


if __name__ == "__main__":
    main()
