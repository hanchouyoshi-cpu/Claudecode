#!/usr/bin/env python3
"""競合リサーチ自動化: YouTube Data API v3 でキーワードごとの上位動画を取得する。

再生数だけでなく「1日あたり再生数(勢い)」を計算し、いま伸びているテーマを見つける。
標準ライブラリのみで動作(pip install 不要)。

準備:
  1. https://console.cloud.google.com/ でプロジェクト作成 → YouTube Data API v3 を有効化
  2. APIキーを発行し、環境変数に設定:  export YOUTUBE_API_KEY="..."

使い方:
  python3 automation/research.py                       # デフォルトキーワードで調査
  python3 automation/research.py "AI 副業" "Claude 使い方"
  python3 automation/research.py --days 90 --max 20 "ChatGPT 稼ぐ"

出力: output/research/YYYY-MM-DD.md (Markdownレポート)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

API_BASE = "https://www.googleapis.com/youtube/v3"

DEFAULT_KEYWORDS = [
    "AI 副業",
    "AI 稼ぐ",
    "ChatGPT 使い方",
    "Claude 使い方",
    "AIツール おすすめ",
]


def api_get(endpoint: str, params: dict) -> dict:
    params["key"] = os.environ["YOUTUBE_API_KEY"]
    url = f"{API_BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as res:
        return json.load(res)


def search_videos(keyword: str, days: int, max_results: int) -> list[dict]:
    published_after = (
        dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    search = api_get(
        "search",
        {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "order": "viewCount",
            "publishedAfter": published_after,
            "regionCode": "JP",
            "relevanceLanguage": "ja",
            "maxResults": max_results,
        },
    )
    video_ids = [item["id"]["videoId"] for item in search.get("items", [])]
    if not video_ids:
        return []

    stats = api_get(
        "videos",
        {"part": "snippet,statistics", "id": ",".join(video_ids)},
    )

    now = dt.datetime.now(dt.timezone.utc)
    rows = []
    for v in stats.get("items", []):
        views = int(v["statistics"].get("viewCount", 0))
        published = dt.datetime.fromisoformat(
            v["snippet"]["publishedAt"].replace("Z", "+00:00")
        )
        age_days = max((now - published).days, 1)
        rows.append(
            {
                "title": v["snippet"]["title"],
                "channel": v["snippet"]["channelTitle"],
                "views": views,
                "age_days": age_days,
                "views_per_day": views // age_days,
                "url": f"https://www.youtube.com/watch?v={v['id']}",
            }
        )
    rows.sort(key=lambda r: r["views_per_day"], reverse=True)
    return rows


def write_report(results: dict[str, list[dict]], out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    today = dt.date.today().isoformat()
    path = os.path.join(out_dir, f"{today}.md")

    lines = [f"# 競合リサーチ {today}", ""]
    lines.append("1日あたり再生数(勢い)の降順。タイトルの型・サムネの傾向を観察して企画に反映する。")
    lines.append("")
    for keyword, rows in results.items():
        lines.append(f"## 「{keyword}」")
        lines.append("")
        if not rows:
            lines.append("(該当なし)")
            lines.append("")
            continue
        lines.append("| 勢い(再生/日) | 総再生 | 経過日数 | タイトル | チャンネル |")
        lines.append("|---:|---:|---:|---|---|")
        for r in rows:
            lines.append(
                f"| {r['views_per_day']:,} | {r['views']:,} | {r['age_days']} "
                f"| [{r['title']}]({r['url']}) | {r['channel']} |"
            )
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube競合リサーチ")
    parser.add_argument("keywords", nargs="*", default=None, help="検索キーワード(省略時はデフォルト5種)")
    parser.add_argument("--days", type=int, default=180, help="何日以内の動画を対象にするか(デフォルト180)")
    parser.add_argument("--max", type=int, default=15, help="キーワードごとの取得件数(デフォルト15)")
    parser.add_argument("--out", default="output/research", help="出力ディレクトリ")
    args = parser.parse_args()

    if "YOUTUBE_API_KEY" not in os.environ:
        sys.exit(
            "エラー: 環境変数 YOUTUBE_API_KEY が未設定です。\n"
            "Google Cloud Console で YouTube Data API v3 のキーを発行し、\n"
            '  export YOUTUBE_API_KEY="AIza..."\n'
            "を実行してください(~/.zshrc に書いておくと便利)。"
        )

    keywords = args.keywords or DEFAULT_KEYWORDS
    results = {}
    for kw in keywords:
        print(f"調査中: {kw} ...", file=sys.stderr)
        results[kw] = search_videos(kw, args.days, args.max)

    path = write_report(results, args.out)
    print(f"レポートを出力しました: {path}")


if __name__ == "__main__":
    main()
