#!/usr/bin/env python3
"""reports/latest.json を読み、週次調査の結果を Discord に通知する。

GitHub Actions（.github/workflows/discord-notify.yml）から呼ばれる。
入出力の契約:
  - 入力: reports/latest.json（スキーマは docs/latest-json.md）
  - 環境変数: DISCORD_WEBHOOK_URL
  - 引数: 当日のレポートファイルパス（日付の取得にのみ使う）
方針:
  - **通知は必ず1メッセージ**。連投すると通知が読まれなくなるため、
    件数が多い場合は詳細表示を絞り、残りは一覧行に落とす。
Discordの制約（components v2）:
  - 1メッセージあたりテキスト合計4000字 / コンポーネント総数40 が上限
  - チャンネルWebhookでも style=5（リンク）ボタンは送れる（?with_components=true が必要）
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import unicodedata
import urllib.error
import urllib.request

WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]
LATEST_JSON = "reports/latest.json"

IS_COMPONENTS_V2 = 1 << 15
CONTAINER, SECTION, TEXT, SEPARATOR, BUTTON = 17, 9, 10, 14, 2
LINK_STYLE = 5

# 左端のアクセントバーの色。状態を色で示すため3色を使い分ける。
# 彩度・明度を揃えた寒色系でまとめ、週次で見ても疲れないトーンにしている。
ACCENT_URGENT = 0x8B5CF6   # 締切間近 … バイオレット
ACCENT_HIGH = 0x38BDF8     # 関連度「高」… スカイブルー
ACCENT_NEW = 0x34D399      # 新規発見 … エメラルド

MAX_DETAIL_ITEMS = 5      # ボタン付きで詳細表示する上限
MAX_LIST_ITEMS = 8        # 一覧行で流す上限
MAX_URGENT_ROWS = 6       # 締切間近リストに出す上限
TEXT_BUDGET = 3600        # components v2 のテキスト合計上限4000に対する安全域
MAX_COMPONENTS = 36       # components v2 の総数上限40に対する安全域


# --- latest.json の読み取り ---------------------------------------------------

def today_jst() -> dt.date:
    """実行環境のTZに依存せずJSTの今日を返す（GitHub ActionsのランナーはUTC）。"""
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=9)).date()


def load(today: dt.date) -> list[dict]:
    with open(LATEST_JSON, encoding="utf-8") as f:
        subsidies = json.load(f).get("subsidies", [])
    for s in subsidies:
        s["_days_left"] = days_left(s, today)
    return subsidies


def clear_new_flags() -> int:
    """通知済みの「新規」フラグを落とす。

    ローカルの日次調査はフラグを積むだけにしてあるので、送信したこの時点で
    まとめて外す。次の通知までに見つかったものが、また新規として溜まる。
    """
    with open(LATEST_JSON, encoding="utf-8") as f:
        data = json.load(f)
    cleared = 0
    for s in data.get("subsidies", []):
        if s.pop("new_this_survey", None):
            cleared += 1
    if cleared:
        with open(LATEST_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
    return cleared


def days_left(s: dict, today: dt.date) -> int | None:
    try:
        return (dt.date.fromisoformat(s["deadline"]) - today).days
    except (KeyError, TypeError, ValueError):
        return None


def by_deadline(s: dict) -> int:
    return s["_days_left"] if s["_days_left"] is not None else 9999


# --- 表示ヘルパ ---------------------------------------------------------------

def width(text: str) -> int:
    """全角を2桁として数えた表示幅。"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def clip(text: str, cells: int) -> str:
    out = ""
    for c in text:
        if width(out) + (2 if unicodedata.east_asian_width(c) in "WF" else 1) > cells:
            return out[:-1] + "…" if out else ""
        out += c
    return out


def deadline_label(s: dict) -> str:
    d = s["_days_left"]
    if s.get("deadline") and d is not None:
        if d < 0:
            return f"{s['deadline']}（超過）"
        return f"{s['deadline']}（残{d}日）"
    note = (s.get("deadline_note") or "").split("。")[0]
    return clip(note, 40) if note else "未定"


def money_line(s: dict) -> str:
    """金額と補助率。この2つがこの通知の主役。

    Discordは通常テキストを折り返すので、途中で切るより全文を出したほうが読める。
    """
    amount = clip(s.get("amount") or "記載なし", 120)
    rate = clip(s.get("subsidy_rate") or "記載なし", 80)
    return f"補助額　**{amount}**\n補助率　**{rate}**"


# --- コンポーネント構築 -------------------------------------------------------

def text(content: str) -> dict:
    return {"type": TEXT, "content": content}


def separator(divider: bool = True, spacing: int = 1) -> dict:
    return {"type": SEPARATOR, "divider": divider, "spacing": spacing}


def item_section(s: dict) -> dict:
    """1案件 = 1ブロック。公式サイトはリンクボタンで開かせる。

    注意: components v2 の Section(type 9) は accessory が必須。
    ボタンを付けられない案件を Section で組むと 400 が返り、通知が丸ごと落ちる。
    そのため、ボタンが無い場合は素の Text コンポーネントにする。
    """
    lines = [
        f"**{clip(s.get('name') or '(名称不明)', 120)}**",
        money_line(s),
        f"締切　{deadline_label(s)}",
    ]
    meta = [v for v in (s.get("authority"), s.get("region"), s.get("status")) if v]
    if meta:
        lines.append("管轄　" + clip("　/　".join(meta), 90))

    if s.get("url") and s.get("url_verified"):
        return {
            "type": SECTION,
            "components": [text("\n".join(lines))],
            "accessory": {
                "type": BUTTON,
                "style": LINK_STYLE,
                "label": "公式サイト",
                "url": s["url"],
            },
        }

    # ボタンを付けられない場合もURLは本文に残す（リンク切れは明記）
    lines.append(f"URL　{s['url']}（要確認）" if s.get("url") else "URL　不明")
    return text("\n".join(lines))


def deadline_lines(items: list[dict], limit: int = MAX_URGENT_ROWS) -> str:
    """締切間近の一覧。

    以前は等幅コードブロックの表にしていたが、Discordはコードブロックを折り返さず
    横スクロールにするため、ウィンドウ幅によって名称の右側が見えなくなっていた。
    通常テキストなら折り返されるので、全文が読める形にする。
    """
    rows = []
    for s in items[:limit]:
        d = s["_days_left"]
        head = [f"**{s.get('deadline') or '未定'}**"]
        if d is not None:
            head.append(f"残{d}日")
        rate = s.get("subsidy_rate")
        if rate:
            head.append(f"補助率 {clip(rate, 60)}")
        rows.append(
            "　/　".join(head) + "\n"
            + "　" + clip(s.get("name") or "(名称不明)", 120)
        )
    if len(items) > limit:
        rows.append(f"-# ほか {len(items) - limit} 件")
    return "\n\n".join(rows)


def list_line(s: dict) -> str:
    """ボタンを付けない案件の2行表示。名称を優先し、金額・補助率・締切を下段に置く。"""
    rate = s.get("subsidy_rate") or "記載なし"
    parts = [f"補助額 {clip(s.get('amount') or '記載なし', 96)}"]
    if rate != "記載なし":
        parts.append(f"補助率 {clip(rate, 56)}")
    parts.append(f"締切 {clip(deadline_label(s), 36)}")
    return f"**{clip(s.get('name') or '', 100)}**\n-# " + "　/　".join(parts)


# --- 送信 ---------------------------------------------------------------------

def send(children: list[dict], accent: int) -> None:
    payload = {
        "flags": IS_COMPONENTS_V2,
        "components": [{"type": CONTAINER, "accent_color": accent, "components": children}],
        "allowed_mentions": {"parse": []},
    }
    req = urllib.request.Request(
        WEBHOOK + "?with_components=true",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "subsidy-research-bot"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"discord: {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"discord error {e.code}: {e.read().decode()}", file=sys.stderr)
        raise


def total_text(children: list[dict]) -> int:
    return sum(len(c.get("content", "")) for c in walk(children))


def walk(children: list[dict]):
    for c in children:
        yield c
        yield from walk(c.get("components", []))


def resolve_date(report_path: str | None) -> dt.date:
    """日付はレポートのファイル名から取る。無指定・不正ならJSTの今日。"""
    if report_path:
        try:
            return dt.date.fromisoformat(os.path.basename(report_path).replace(".md", ""))
        except ValueError:
            pass
    return today_jst()


def main(report_path: str | None = None, clear_new: bool = False) -> None:
    today = resolve_date(report_path)
    date = today.isoformat()
    subsidies = load(today)

    new_items = [s for s in subsidies if s.get("new_this_survey")]
    urgent = sorted(
        [s for s in subsidies if s["_days_left"] is not None and 0 <= s["_days_left"] <= 14],
        key=by_deadline,
    )
    high = sorted([s for s in subsidies if s.get("relevance") == "高"], key=by_deadline)

    # 詳細（ボタン付き）は「締切間近 → 関連度高 → 新規」の優先順で上位のみ
    highlighted: list[dict] = []
    for s in urgent + high + new_items:
        if s not in highlighted:
            highlighted.append(s)
    detail, overflow = highlighted[:MAX_DETAIL_ITEMS], highlighted[MAX_DETAIL_ITEMS:]

    # 注目枠（締切間近・関連度高・新規）に入らなかった案件も一覧の対象にする。
    # 以前はここで落ちた案件が件数にも出ず、ヘッダの「掲載中 N」と表示数が食い違っていた。
    overflow += sorted((s for s in subsidies if s not in highlighted), key=by_deadline)

    children: list[dict] = [
        text(
            "## 補助金・助成金 週次調査\n"
            f"-# {date}　会津大学発ベンチャー / 会津・福島県の中小企業"
        ),
        text(
            f"新規 **{len(new_items)}**　/　"
            f"掲載中 **{len(subsidies)}**　/　"
            f"締切2週間以内 **{len(urgent)}**　/　"
            f"関連度「高」 **{len(high)}**"
        ),
    ]

    if urgent:
        children += [separator(), text("**締切間近（2週間以内）**"), text(deadline_lines(urgent))]

    if detail:
        children.append(separator())
        children.append(text("**優先して見るべき案件**"))
        for i, s in enumerate(detail):
            # 案件同士が地続きだと読めないので、2件目以降は必ず線で区切る
            if i:
                children.append(separator())
            children.append(item_section(s))

    if overflow:
        # 1行に詰めず、案件ごとに空行を挟む（"\n\n"）
        rows = [list_line(s) for s in overflow[:MAX_LIST_ITEMS]]
        if len(overflow) > MAX_LIST_ITEMS:
            rows.append(f"-# ほか {len(overflow) - MAX_LIST_ITEMS} 件（詳細はレポート参照）")
        children += [separator(), text("**その他の案件**"), text("\n\n".join(rows))]

    if not subsidies:
        children.append(text("本日は掲載できる案件がありませんでした。"))

    # テキスト量・コンポーネント数が上限を超える場合は末尾（重要度の低い順）から削る。
    # 区切り線を入れたぶんコンポーネント数が増えるので、こちらも見る。
    def over_budget() -> bool:
        return total_text(children) > TEXT_BUDGET or len(list(walk(children))) > MAX_COMPONENTS

    trimmed = False
    while over_budget() and len(children) > 3:
        children.pop()
        trimmed = True
    if trimmed:
        children.append(text("-# ※ 件数が多いため一部を省略しています"))

    accent = ACCENT_URGENT if urgent else (ACCENT_HIGH if high else ACCENT_NEW)
    send(children, accent)

    if clear_new:
        print(f"新規フラグを{clear_new_flags()}件クリアしました")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--clear-new"]
    main(args[0] if args else None, clear_new="--clear-new" in sys.argv[1:])
