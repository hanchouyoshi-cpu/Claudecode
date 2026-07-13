#!/bin/bash
# 台本自動生成: Claude Code のヘッドレスモード (claude -p) で動画台本を作る。
# ユーザーのMacにインストール済みの Claude Code をそのまま使うため、APIキー・追加費用は不要。
#
# 使い方:
#   ./automation/generate_script.sh "ChatGPTでブログ記事を量産して月1万円稼ぐ手順"
#   ./automation/generate_script.sh -m 8 -r output/research/2026-07-13.md "AIツール比較"
#
# オプション:
#   -m 分数      動画の長さ(デフォルト10分)
#   -r ファイル  リサーチ結果のMarkdownを参考資料として渡す
#
# 出力: output/scripts/YYYYMMDD-HHMM.md

set -euo pipefail

MINUTES=10
RESEARCH_FILE=""

while getopts "m:r:" opt; do
  case "$opt" in
    m) MINUTES="$OPTARG" ;;
    r) RESEARCH_FILE="$OPTARG" ;;
    *) echo "使い方: $0 [-m 分数] [-r リサーチファイル] \"動画テーマ\"" >&2; exit 1 ;;
  esac
done
shift $((OPTIND - 1))

if [ $# -lt 1 ]; then
  echo "エラー: 動画テーマを指定してください。" >&2
  echo "例: $0 \"ChatGPTでブログ記事を量産して月1万円稼ぐ手順\"" >&2
  exit 1
fi
TOPIC="$1"

if ! command -v claude >/dev/null 2>&1; then
  echo "エラー: claude コマンドが見つかりません。Claude Code をインストールしてください:" >&2
  echo "  npm install -g @anthropic-ai/claude-code" >&2
  exit 1
fi

# 読み上げ想定: 約350字/分
CHARS=$((MINUTES * 350))

RESEARCH_SECTION=""
if [ -n "$RESEARCH_FILE" ] && [ -f "$RESEARCH_FILE" ]; then
  RESEARCH_SECTION="# 参考: 競合リサーチ結果(伸びている動画の傾向を踏まえること)
$(cat "$RESEARCH_FILE")"
fi

PROMPT=$(cat <<EOF
あなたはYouTube台本作家です。以下の条件で解説動画の台本を書いてください。

# 動画テーマ
${TOPIC}

# 条件
- 想定視聴者: AI初心者の会社員(専門用語は都度ひとこと解説)
- 長さ: ${MINUTES}分(読み上げで約${CHARS}字)
- 構成:
  1. フック(15秒以内): 結論とベネフィットを先に言う
  2. この動画で得られること(3点)
  3. 本編(手順を番号付きで、画面操作の指示も書く)
  4. 注意点・失敗しやすいポイント
  5. まとめ+次に見るべき動画への誘導+チャンネル登録の一言
- 文体: です・ます調、1文は短く、話し言葉
- 各セクションに [スライド: 〇〇] の形でスライド指示を入れる
- 誇大表現は禁止。「確実に稼げる」等は使わず、現実的な数字で語る
- 台本の冒頭に、タイトル案3つとサムネイル文言案3つを付ける

${RESEARCH_SECTION}
EOF
)

OUT_DIR="output/scripts"
mkdir -p "$OUT_DIR"
OUT_FILE="${OUT_DIR}/$(date +%Y%m%d-%H%M).md"

echo "台本を生成中: ${TOPIC} (${MINUTES}分想定)..." >&2
claude -p "$PROMPT" > "$OUT_FILE"

echo "台本を出力しました: $OUT_FILE"
echo "次のステップ: 内容を確認・自分の体験を追記してから ./automation/tts_voicevox.py $OUT_FILE で音声化"
