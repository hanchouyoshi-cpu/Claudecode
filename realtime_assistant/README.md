# リアルタイム回答生成アシスタント (フェーズ1 MVP)

会話(Web会議・通話・対面)の音声をリアルタイムに文字起こしし、
相手の発言に対する回答候補を Claude が生成してカンペとして表示する Windows 向けツール。

企画の全体像は [`../docs/realtime-response-generator-proposal.md`](../docs/realtime-response-generator-proposal.md) を参照。

## 仕組み

```
マイク(自分の声) ─┐
                    ├→ 簡易VADで発話単位に分割 → faster-whisper で文字起こし
ループバック(相手の声)┘         │
                                ↓
                会話履歴 + 事前資料 → Claude API → 回答候補3件をオーバーレイ表示
```

- **相手の声** は WASAPI ループバック(PCで再生されている音)から取得するため、
  Zoom / Teams / Meet など会議アプリを問わず動作します。
- **文字起こし** はローカルの faster-whisper(無料・オフライン)。
- **回答生成** は Claude API のストリーミング。事前資料はプロンプトキャッシュに載せて低遅延化。

## セットアップ (Windows)

1. Python 3.10 以上をインストール
2. 依存パッケージをインストール:

   ```
   cd realtime_assistant
   pip install -r requirements.txt
   ```

3. Anthropic API キーを設定:

   ```
   set ANTHROPIC_API_KEY=sk-ant-...
   ```

   (キーは https://platform.claude.com/ で取得)

## 使い方

### まずはテキストモードで動作確認(どのOSでも可)

音声デバイス不要。相手の発言をキーボードで入力すると回答候補が返ります。

```
python main.py --text
```

### 音声モード (Windows)

```
python main.py --context 資料.md
```

- 常時最前面の小型ウィンドウが開き、会話ログと回答候補が表示されます
- `--context` に製品資料・想定問答・職務経歴書などを渡すと、その内容を根拠に回答します
- 相手の発話が途切れて約0.8秒で候補生成が始まります

### 主なオプション

| オプション | 説明 |
|---|---|
| `--context FILE` | 事前資料 (md/txt)。回答の根拠になる |
| `--model ID` | Claude モデルの上書き(既定: `claude-opus-4-8`) |
| `--effort low\|medium\|high` | 回答の思考量。既定 `low`(速度優先)。精度重視なら `medium` 以上 |
| 環境変数 `RTA_WHISPER_MODEL` | whisper モデルサイズ(既定 `small`。GPU があれば `medium` 推奨) |

## チューニングのヒント

- **遅延が大きい**: whisper モデルを `base` に下げる / GPU で `transcriber.py` の
  `device="cuda", compute_type="float16"` に変更
- **無音で区切られすぎる / 区切られない**: `config.py` の `silence_ms`・`energy_threshold` を調整
- **候補の質を上げたい**: `--effort medium` にする、事前資料を充実させる

## 注意事項

- 相手側音声の取得・処理は **相手の同意を得てから** 使用してください(詳細は企画書の注意点を参照)
- 面接など、AI 支援ツールの使用が禁止されている場面では使用しないでください
