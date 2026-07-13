# 制作自動化パイプライン(Mac用)

計画書の制作工程のうち、自動化できる部分をスクリプト化したもの。
1本あたりの工数を **約10時間 → 約4時間** に短縮するのが目標。

## 自動化の全体像

| 工程 | 自動化 | ツール |
|---|---|---|
| 競合リサーチ | ✅ `research.py` | YouTube Data API(無料枠で十分) |
| 台本作成 | ✅ `generate_script.sh` | Claude Code ヘッドレスモード(`claude -p`) |
| 音声合成 | ✅ `tts_voicevox.py` | VOICEVOX ローカルAPI |
| 台本の検証・体験談追記 | ❌ 手作業(ここが差別化の核) | — |
| スライド作成 | △ 半自動(台本の [スライド:] 指示に従って作る) | Keynote / Canva |
| 編集・サムネ | ❌ 手作業(テンプレ化で短縮) | CapCut / Canva |

> ⚠️ **AI丸投げは禁止**: 台本を無編集で動画化し続けると「再利用コンテンツ」と判定され
> 収益化停止のリスクがあります(`docs/genre-research.md` 参照)。
> 台本生成後に必ず自分の検証・数字・体験を追記してください。それが伸びる動画の条件でもあります。

## 初回セットアップ(Mac)

```bash
# 1. Claude Code(インストール済みならスキップ)
npm install -g @anthropic-ai/claude-code

# 2. VOICEVOX — https://voicevox.hiroshiba.jp/ からMac版をダウンロードして起動

# 3. YouTube Data API キー(リサーチ用・無料)
#    https://console.cloud.google.com/ → プロジェクト作成 → YouTube Data API v3 を有効化 → APIキー発行
echo 'export YOUTUBE_API_KEY="AIza..."' >> ~/.zshrc && source ~/.zshrc

# 4. スクリプトに実行権限
chmod +x automation/*.sh automation/*.py
```

## 使い方

### 週次リサーチ(月曜・企画出しの前に)

```bash
python3 automation/research.py
# → output/research/YYYY-MM-DD.md に「勢いのある動画」レポートが出る
```

キーワードは引数で変更可能: `python3 automation/research.py "Claude 副業" "AIエージェント"`

### 台本生成

```bash
./automation/generate_script.sh "ChatGPTでブログ記事を量産して月1万円稼ぐ手順"
# リサーチ結果を反映する場合:
./automation/generate_script.sh -r output/research/2026-07-13.md "同上"
```

### 音声合成(VOICEVOXアプリを起動してから)

```bash
python3 automation/tts_voicevox.py output/scripts/20260713-1200.md
# → 同名の .wav が生成される。スピーカー変更: --speaker 2(四国めたん)等
```

### 全部まとめて

```bash
./automation/pipeline.sh -R "動画テーマ"   # リサーチ→台本→(確認後)音声化
```

## 週次ワークフローへの組み込み

| 曜日 | Before(手作業) | After(自動化後) |
|---|---|---|
| 月 | リサーチ+台本1本目 (2.5h) | `research.py` + `pipeline.sh` ×2本 → 台本確認・追記 (1.5h) |
| 火 | 台本2本目+スライド (2.5h) | スライド2本分 (2h) |
| 水 | スライド+音声収録 (2.5h) | `tts_voicevox.py` ×2 + 画面収録 (1h) |
| 木・金 | 編集 (5h) | 編集(テンプレ化で 3.5h) |
| 土 | ショート切り出し (1.5h) | 同左 (1.5h) |

→ 週合計 約15h → **約9.5h**。浮いた時間は「検証(実際にAI副業を試す)」に回す。
検証こそがこのチャンネルのコンテンツの源泉。

## 発展(必要になったら)

- **サムネ半自動化**: Canvaのテンプレを固定し、文字だけ差し替え
- **メタデータ生成**: `claude -p "この台本からタイトル・説明文・タグを生成: $(cat 台本.md)"`
- **週次分析**: YouTube Analytics API(OAuth必要)で振り返りレポート自動化 — 収益化後に検討
