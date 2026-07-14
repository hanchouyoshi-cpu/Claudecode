#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ロト6「逆説的」予測アルゴリズム

一般のロト愛好家が避けがちなパターンを、確率的な裏付けに基づいて
あえて採用する（＝逆説的に考える）決定論的な選択ルール。

ルール（直近13回をウィンドウとして使用）:
  R1 引っ張り   : 「前回の数字は続けて出ない」という通念の逆。
                  実際は P(前回数字が1個以上重複) = 1 - C(37,6)/C(43,6) ≈ 61.9%。
                  → 前回本数字から2個採用（ウィンドウ内出現頻度→直近性で選択）。
  R2 スライド   : 「連番は出にくい」という通念の逆。
                  実際は P(連番が1組以上) = 1 - C(38,6)/C(43,6) ≈ 54.7%。
                  → R1採用数字の±1隣接から2個採用（頻度→直近性で選択）。
  R3 コールド逆張り: 「よく出る数字を追う」という通念の逆。
                  → ウィンドウ内で本数字として一度も出ていない数字から、
                    隣接数字（ボーナス含む）の活性が高いものを2個採用。

注意: ロト6は各数字が等確率で抽選される。本アルゴリズムに予測力はなく、
過去傾向の整理と「逆説的選択」の思考実験である。
"""

from itertools import combinations
from math import comb

# (回, 抽選日, 本数字6個, ボーナス数字)
# 出典: 佐賀新聞・福井新聞の当選番号記事、loto6.jp ほか（README参照）
DRAWS = [
    (2006, "2025-06-09", (4, 7, 19, 22, 26, 28), 33),
    (2007, "2025-06-12", (6, 18, 23, 24, 30, 35), 38),
    (2008, "2025-06-16", (5, 8, 9, 17, 22, 36), 30),
    (2009, "2025-06-19", (8, 17, 20, 35, 36, 40), 12),
    (2010, "2025-06-23", (9, 15, 24, 29, 31, 40), 13),
    (2011, "2025-06-26", (12, 14, 18, 24, 30, 42), 4),
    (2012, "2025-06-30", (1, 14, 20, 36, 38, 41), 30),
    (2013, "2025-07-03", (5, 12, 18, 24, 31, 38), 9),
    (2014, "2025-07-07", (7, 11, 21, 24, 29, 34), 40),
    (2015, "2025-07-10", (6, 8, 13, 16, 20, 23), 26),
    (2016, "2025-07-14", (10, 13, 27, 31, 40, 42), 1),
    (2017, "2025-07-17", (2, 4, 11, 22, 24, 35), 8),
    (2018, "2025-07-21", (1, 2, 14, 21, 22, 33), 37),
    (2019, "2025-07-24", (7, 13, 14, 21, 39, 42), 9),
    (2020, "2025-07-28", (5, 21, 23, 28, 38, 39), 32),  # 検証用
]

WINDOW = 13


def get_draw(round_no):
    for d in DRAWS:
        if d[0] == round_no:
            return d
    return None


def predict(target_round):
    """target_round の直前 WINDOW 回のデータのみを使って6数字を選ぶ。"""
    window = [d for d in DRAWS if target_round - WINDOW <= d[0] < target_round]
    assert len(window) == WINDOW, f"第{target_round}回の予測にはデータが不足"
    prev = window[-1]

    main_freq = {n: 0 for n in range(0, 45)}
    comb_freq = {n: 0 for n in range(0, 45)}
    last_seen = {n: 0 for n in range(0, 45)}  # 本数字として最後に出た回
    for rnd, _, mains, bonus in window:
        for n in mains:
            main_freq[n] += 1
            comb_freq[n] += 1
            last_seen[n] = max(last_seen[n], rnd)
        comb_freq[bonus] += 1

    def seen_before_prev(n):
        return max((r for r, _, m, _ in window if n in m and r < prev[0]),
                   default=0)

    # R1 引っ張り: 前回本数字から2個
    carry = sorted(prev[2],
                   key=lambda n: (-main_freq[n], -seen_before_prev(n), n))[:2]

    # R2 スライド: R1採用数字の±1から2個（連番を作る）
    cands = {c + d for c in carry for d in (-1, 1)}
    cands = sorted(cands & set(range(1, 44)) - set(carry),
                   key=lambda n: (-main_freq[n], -last_seen[n], n))
    slides = cands[:2]

    # R3 コールド逆張り: ウィンドウ未出現数字から、隣接活性の高い2個
    colds = [n for n in range(1, 44) if main_freq[n] == 0]
    colds = sorted(
        colds,
        key=lambda n: (-(comb_freq[n - 1] + comb_freq[n + 1]),
                       -max(last_seen[n - 1], last_seen[n + 1]), n))
    cold_pick = colds[:2]

    pick = sorted(carry + slides + cold_pick)
    return pick, {"carry": sorted(carry), "slides": sorted(slides),
                  "colds": sorted(cold_pick)}


def describe(pick):
    odd = sum(1 for n in pick if n % 2)
    pairs = [(a, b) for a, b in zip(pick, pick[1:]) if b - a == 1]
    return (f"合計={sum(pick)}  奇偶比={odd}:{6 - odd}  "
            f"連番={pairs if pairs else 'なし'}")


def main():
    p_carry = 1 - comb(37, 6) / comb(43, 6)
    p_pair = 1 - comb(38, 6) / comb(43, 6)
    print("=== 逆説の根拠となる確率 ===")
    print(f"前回数字が1個以上重複する確率: {p_carry:.1%}")
    print(f"連番が1組以上含まれる確率:     {p_pair:.1%}")
    print(f"ランダムな6数字の期待一致数:   {6 * 6 / 43:.2f}個\n")

    for target in (2019, 2020):
        pick, parts = predict(target)
        print(f"=== 第{target}回 予測 ===")
        print(f"引っ張り(R1): {parts['carry']}  "
              f"スライド(R2): {parts['slides']}  "
              f"コールド(R3): {parts['colds']}")
        print(f"予測数字: {' '.join(f'{n:02d}' for n in pick)}")
        print(f"  {describe(pick)}")
        actual = get_draw(target)
        if actual:
            hits = sorted(set(pick) & set(actual[2]))
            print(f"実際の当選番号({actual[1]}): "
                  f"{' '.join(f'{n:02d}' for n in actual[2])} "
                  f"ボーナス {actual[3]:02d}")
            print(f"一致: {len(hits)}個 {hits}")
        print()


if __name__ == "__main__":
    main()
