#!/bin/bash
# 一括パイプライン: テーマを渡すと 台本生成 → VOICEVOX音声化 までを自動で行う。
#
# 使い方:
#   ./automation/pipeline.sh "ChatGPTでブログ記事を量産して月1万円稼ぐ手順"
#   ./automation/pipeline.sh -m 8 "AIツール比較"        # 8分動画
#   ./automation/pipeline.sh -R "AI 副業" ...            # 先に競合リサーチも実行して台本に反映
#
# 残り(手作業が必要な工程): 台本の確認・体験談の追記 / スライド作成 / 編集 / サムネ
# ※台本は必ず自分で確認・修正すること。AI丸投げ動画は収益化停止リスクがある(docs/genre-research.md 参照)

set -euo pipefail
cd "$(dirname "$0")/.."

MINUTES=10
DO_RESEARCH=0

while getopts "m:R" opt; do
  case "$opt" in
    m) MINUTES="$OPTARG" ;;
    R) DO_RESEARCH=1 ;;
    *) echo "使い方: $0 [-m 分数] [-R] \"動画テーマ\"" >&2; exit 1 ;;
  esac
done
shift $((OPTIND - 1))

if [ $# -lt 1 ]; then
  echo "エラー: 動画テーマを指定してください。" >&2
  exit 1
fi
TOPIC="$1"

RESEARCH_OPT=()
if [ "$DO_RESEARCH" -eq 1 ]; then
  echo "=== 1/3 競合リサーチ ==="
  python3 automation/research.py "$TOPIC"
  LATEST_RESEARCH=$(ls -t output/research/*.md | head -1)
  RESEARCH_OPT=(-r "$LATEST_RESEARCH")
else
  echo "=== 1/3 競合リサーチ(スキップ: -R で有効化) ==="
fi

echo "=== 2/3 台本生成 (Claude) ==="
./automation/generate_script.sh -m "$MINUTES" "${RESEARCH_OPT[@]}" "$TOPIC"
LATEST_SCRIPT=$(ls -t output/scripts/*.md | head -1)

echo ""
echo "⚠️  台本を確認してください: $LATEST_SCRIPT"
echo "   自分の検証結果・体験談を追記してから音声化するのを推奨します。"
read -r -p "このまま音声化しますか? [y/N] " ANSWER
if [[ "$ANSWER" =~ ^[Yy]$ ]]; then
  echo "=== 3/3 音声合成 (VOICEVOX) ==="
  python3 automation/tts_voicevox.py "$LATEST_SCRIPT"
else
  echo "音声化をスキップしました。編集後に以下を実行してください:"
  echo "  python3 automation/tts_voicevox.py $LATEST_SCRIPT"
fi
