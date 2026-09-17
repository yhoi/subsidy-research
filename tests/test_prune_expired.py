#!/usr/bin/env python3
"""prune_expired.is_expired の判定テスト。 Usage: python3 tests/test_prune_expired.py"""
import datetime as dt, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import prune_expired  # noqa: E402

TODAY = dt.date(2026, 9, 17)
CASES = [
    ("締切が昨日", {"deadline": "2026-09-16", "status": "🔄 受付中"}, True),
    ("締切が今日は残す", {"deadline": "2026-09-17", "status": "🔄 本日締切"}, False),
    ("締切が明日", {"deadline": "2026-09-18", "status": "🔄 受付中"}, False),
    ("締切なし・Watchは残す", {"deadline": None, "status": "📋 次回公募Watch中"}, False),
    ("締切なし・✅終了は消す", {"deadline": None, "status": "✅ 採択結果公表済"}, True),
    ("締切は先だが✅終了", {"deadline": "2026-12-31", "status": "✅ 受付終了"}, True),
    ("不正な日付・受付中は残す", {"deadline": "未定", "status": "🔄 受付中"}, False),
    ("status欠損", {"deadline": None}, False),
]
failed = 0
for desc, s, expect in CASES:
    got = prune_expired.is_expired(s, TODAY) is not None
    print(f"  {'✓' if got == expect else '✗'} {desc}")
    failed += got != expect
kept, removed = prune_expired.prune({"subsidies": [s for _, s, _ in CASES]}, TODAY)
ok = len(removed) == 3 and len(kept) == 5
print(f"  {'✓' if ok else '✗'} prune() 件数 removed={len(removed)} kept={len(kept)}")
failed += not ok
print(f"\n{'PASS' if not failed else 'FAIL'}")
sys.exit(1 if failed else 0)
