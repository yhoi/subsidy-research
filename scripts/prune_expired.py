#!/usr/bin/env python3
"""latest.json から締切切れ・終了済みの案件を機械的に取り除く。

背景:
  プロンプトには「終了した案件は subsidies から削除する」と書いてあるが、
  LLM任せだと「受付終了」「採択結果公表済」のまま残り、通知に締切切れが
  並ぶ事故が Pignet 向けbotで起きた（2026-09）。掲載可否を毎回の判断に
  委ねず、ここで一律に落とす。

判定（どれか1つでも当てはまれば削除）:
  1. deadline が今日より前（JST）
  2. status が「✅」で始まる（終了・採択結果公表済・受付終了 の印）

残すもの:
  - deadline が今日（本日締切）の案件
  - deadline が null で status が Watch／受付中 のもの
  次回公募を追いたい案件は、deadline を null にして status を 📋 にすればよい。

使い方:
  python3 scripts/prune_expired.py <latest.json のパス> [--dry-run]
  終了コードは常に 0（削除件数は標準出力に出す）。
"""

from __future__ import annotations

import datetime as dt
import json
import sys

ENDED_PREFIX = "✅"


def today_jst() -> dt.date:
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=9)).date()


def is_expired(s: dict, today: dt.date) -> str | None:
    """削除すべきなら理由を、残すなら None を返す。"""
    deadline = s.get("deadline")
    if deadline:
        try:
            if dt.date.fromisoformat(deadline) < today:
                return f"締切超過（{deadline}）"
        except ValueError:
            pass  # 不正な日付は status 側の判定に回す
    status = (s.get("status") or "").strip()
    if status.startswith(ENDED_PREFIX):
        return f"終了ステータス（{status[:30]}）"
    return None


def prune(data: dict, today: dt.date) -> tuple[list[dict], list[tuple[dict, str]]]:
    kept, removed = [], []
    for s in data.get("subsidies", []):
        reason = is_expired(s, today)
        if reason:
            removed.append((s, reason))
        else:
            kept.append(s)
    return kept, removed


def main(argv: list[str]) -> int:
    dry_run = "--dry-run" in argv
    paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        print("usage: prune_expired.py <latest.json> [--dry-run]", file=sys.stderr)
        return 2
    today = today_jst()
    for path in paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        kept, removed = prune(data, today)
        for s, reason in removed:
            print(f"prune[{path}]: {s.get('id')}  {reason}")
        print(f"prune[{path}]: {len(removed)}件削除 / {len(kept)}件残存（基準日 {today}）")
        if removed and not dry_run:
            data["subsidies"] = kept
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
